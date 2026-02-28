from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import List, Optional, Dict
import os
import uuid
import pandas as pd
from datetime import datetime
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.csv_import import CSVImport, CSVImportResponse, ColumnMapping
from app.models.transaction import Transaction
from app.services.csv_service import CSVProcessor
from app.core.config import settings
from app.core.database import get_database
from bson import ObjectId

router = APIRouter(prefix="/imports", tags=["imports"])
csv_processor = CSVProcessor()


@router.post("/upload", response_model=CSVImportResponse)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload CSV file for processing"""
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create import record
    csv_import = CSVImport(
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=file.size,
        status="pending"
    )
    
    db = get_database()
    result = await db.csv_imports.insert_one(csv_import.dict(by_alias=True))
    csv_import.id = result.inserted_id
    
    # Start processing
    await process_csv_upload(str(csv_import.id))
    
    return CSVImportResponse(**csv_import.dict())


async def process_csv_upload(import_id: str):
    """Process uploaded CSV file"""
    db = get_database()
    
    # Update status to processing
    await db.csv_imports.update_one(
        {"_id": ObjectId(import_id)},
        {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
    )
    
    try:
        # Get import record
        csv_import_doc = await db.csv_imports.find_one({"_id": ObjectId(import_id)})
        if not csv_import_doc:
            return
        
        # Read CSV file
        df = pd.read_csv(csv_import_doc["file_path"])
        total_rows = len(df)
        
        # Detect columns
        detected_columns = csv_processor.detect_columns(df)
        
        # Generate preview data
        preview_data = []
        for _, row in df.head(10).iterrows():
            preview_row = {}
            for col in df.columns:
                preview_row[col] = str(row[col]) if pd.notna(row[col]) else ""
            preview_data.append(preview_row)
        
        # Update import record
        update_data = {
            "status": "preview_ready",
            "total_rows": total_rows,
            "detected_columns": detected_columns,
            "preview_data": preview_data,
            "updated_at": datetime.utcnow()
        }
        
        await db.csv_imports.update_one(
            {"_id": ObjectId(import_id)},
            {"$set": update_data}
        )
        
    except Exception as e:
        # Update status to failed
        await db.csv_imports.update_one(
            {"_id": ObjectId(import_id)},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        )


@router.get("/{import_id}/preview", response_model=CSVImportResponse)
async def get_import_preview(
    import_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get import preview and column mapping"""
    db = get_database()
    
    csv_import = await db.csv_imports.find_one({
        "_id": ObjectId(import_id),
        "user_id": current_user.id
    })
    
    if not csv_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found"
        )
    
    return CSVImportResponse(**csv_import)


@router.put("/{import_id}/column-mapping", response_model=CSVImportResponse)
async def update_column_mapping(
    import_id: str,
    column_mapping: ColumnMapping,
    current_user: User = Depends(get_current_user)
):
    """Update column mapping for import"""
    db = get_database()
    
    csv_import = await db.csv_imports.find_one({
        "_id": ObjectId(import_id),
        "user_id": current_user.id
    })
    
    if not csv_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found"
        )
    
    # Update column mapping
    await db.csv_imports.update_one(
        {"_id": ObjectId(import_id)},
        {"$set": {
            "column_mapping": column_mapping.dict(),
            "updated_at": datetime.utcnow()
        }}
    )
    
    # Get updated record
    updated_import = await db.csv_imports.find_one({"_id": ObjectId(import_id)})
    return CSVImportResponse(**updated_import)


@router.post("/{import_id}/confirm", response_model=CSVImportResponse)
async def confirm_import(
    import_id: str,
    current_user: User = Depends(get_current_user)
):
    """Confirm import and create transactions"""
    db = get_database()
    
    csv_import = await db.csv_imports.find_one({
        "_id": ObjectId(import_id),
        "user_id": current_user.id
    })
    
    if not csv_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found"
        )
    
    if csv_import["status"] != "preview_ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Import is not ready for confirmation"
        )
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_import["file_path"])
        column_mapping = csv_import.get("column_mapping", {})
        detected_columns = csv_import.get("detected_columns", {})
        
        processed_rows = 0
        duplicate_rows = 0
        error_rows = 0
        
        for index, row in df.iterrows():
            try:
                # Extract and normalize data
                transaction_data = extract_transaction_data(row, column_mapping, detected_columns)
                if not transaction_data:
                    error_rows += 1
                    continue
                
                # Check for duplicates
                if await is_duplicate_transaction(db, current_user.id, transaction_data):
                    duplicate_rows += 1
                    continue
                
                # Create transaction
                transaction = Transaction(
                    user_id=current_user.id,
                    import_id=ObjectId(import_id),
                    **transaction_data
                )
                
                await db.transactions.insert_one(transaction.dict(by_alias=True))
                processed_rows += 1
                
            except Exception as e:
                error_rows += 1
                continue
        
        # Update import record
        await db.csv_imports.update_one(
            {"_id": ObjectId(import_id)},
            {"$set": {
                "status": "confirmed",
                "processed_rows": processed_rows,
                "duplicate_rows": duplicate_rows,
                "error_rows": error_rows,
                "updated_at": datetime.utcnow()
            }}
        )
        
        # Get updated record
        updated_import = await db.csv_imports.find_one({"_id": ObjectId(import_id)})
        return CSVImportResponse(**updated_import)
        
    except Exception as e:
        # Update status to failed
        await db.csv_imports.update_one(
            {"_id": ObjectId(import_id)},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "updated_at": datetime.utcnow()
            }}
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get("", response_model=List[CSVImportResponse])
async def list_imports(
    current_user: User = Depends(get_current_user)
):
    """List user's imports"""
    db = get_database()
    
    cursor = db.csv_imports.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1)
    
    imports = []
    async for import_doc in cursor:
        imports.append(CSVImportResponse(**import_doc))
    
    return imports


def extract_transaction_data(row: pd.Series, column_mapping: Dict, detected_columns: Dict) -> Optional[Dict]:
    """Extract transaction data from CSV row"""
    try:
        # Get column mappings
        date_col = column_mapping.date_column or detected_columns.get("columns", {}).get("date", {}).get("source_column")
        amount_col = column_mapping.amount_column
        debit_col = column_mapping.debit_column
        credit_col = column_mapping.credit_column
        desc_col = column_mapping.description_column or detected_columns.get("columns", {}).get("description", {}).get("source_column")
        balance_col = column_mapping.balance_column or detected_columns.get("columns", {}).get("balance", {}).get("source_column")
        
        if not date_col or not (amount_col or (debit_col and credit_col)):
            return None
        
        # Extract values
        date_str = row[date_col] if date_col in row and pd.notna(row[date_col]) else None
        amount_val = row[amount_col] if amount_col and amount_col in row and pd.notna(row[amount_col]) else None
        debit_val = row[debit_col] if debit_col and debit_col in row and pd.notna(row[debit_col]) else None
        credit_val = row[credit_col] if credit_col and credit_col in row and pd.notna(row[credit_col]) else None
        desc_val = row[desc_col] if desc_col and desc_col in row and pd.notna(row[desc_col]) else ""
        balance_val = row[balance_col] if balance_col and balance_col in row and pd.notna(row[balance_col]) else None
        
        if not date_str:
            return None
        
        # Parse date
        date_format = detected_columns.get("columns", {}).get("date", {}).get("format", "MM/DD/YYYY")
        transaction_date = csv_processor.parse_date(date_str, date_format)
        
        # Normalize amount
        amount = csv_processor.normalize_amount(amount_val, debit_val, credit_val)
        
        # Normalize description
        description = csv_processor.normalize_description(desc_val)
        
        # Parse balance
        balance = None
        if balance_val:
            balance = csv_processor._parse_amount(str(balance_val))
        
        return {
            "transaction_date": transaction_date,
            "amount": amount,
            "description": description,
            "normalized_description": description.lower(),
            "balance": balance
        }
        
    except Exception:
        return None


async def is_duplicate_transaction(db, user_id: ObjectId, transaction_data: Dict) -> bool:
    """Check if transaction is a duplicate"""
    # Check for existing transaction with same date, amount, and description
    existing = await db.transactions.find_one({
        "user_id": user_id,
        "transaction_date": transaction_data["transaction_date"],
        "amount": transaction_data["amount"],
        "normalized_description": transaction_data["normalized_description"]
    })
    
    return existing is not None


@router.get("", response_model=List[CSVImportResponse])
async def list_imports(
    current_user: User = Depends(get_current_user)
):
    """List user's imports"""
    db = get_database()
    
    cursor = db.csv_imports.find(
        {"user_id": current_user.id}
    ).sort("created_at", -1)
    
    imports = []
    async for import_doc in cursor:
        imports.append(CSVImportResponse(**import_doc))
    
    return imports


def extract_transaction_data(row: pd.Series, column_mapping: Dict, detected_columns: Dict) -> Optional[Dict]:
    """Extract transaction data from CSV row"""
    try:
        # Get column mappings
        date_col = column_mapping.date_column or detected_columns.get("columns", {}).get("date", {}).get("source_column")
        amount_col = column_mapping.amount_column
        debit_col = column_mapping.debit_column
        credit_col = column_mapping.credit_column
        desc_col = column_mapping.description_column or detected_columns.get("columns", {}).get("description", {}).get("source_column")
        balance_col = column_mapping.balance_column or detected_columns.get("columns", {}).get("balance", {}).get("source_column")
        
        if not date_col or not (amount_col or (debit_col and credit_col)):
            return None
        
        # Extract values
        date_str = row[date_col] if date_col in row and pd.notna(row[date_col]) else None
        amount_val = row[amount_col] if amount_col and amount_col in row and pd.notna(row[amount_col]) else None
        debit_val = row[debit_col] if debit_col and debit_col in row and pd.notna(row[debit_col]) else None
        credit_val = row[credit_col] if credit_col and credit_col in row and pd.notna(row[credit_col]) else None
        desc_val = row[desc_col] if desc_col and desc_col in row and pd.notna(row[desc_col]) else ""
        balance_val = row[balance_col] if balance_col and balance_col in row and pd.notna(row[balance_col]) else None
        
        if not date_str:
            return None
        
        # Parse date
        date_format = detected_columns.get("columns", {}).get("date", {}).get("format", "MM/DD/YYYY")
        transaction_date = csv_processor.parse_date(date_str, date_format)
        
        # Normalize amount
        amount = csv_processor.normalize_amount(amount_val, debit_val, credit_val)
        
        # Normalize description
        description = csv_processor.normalize_description(desc_val)
        
        # Parse balance
        balance = None
        if balance_val:
            balance = csv_processor._parse_amount(str(balance_val))
        
        return {
            "transaction_date": transaction_date,
            "amount": amount,
            "description": description,
            "normalized_description": description.lower(),
            "balance": balance
        }
        
    except Exception:
        return None


async def is_duplicate_transaction(db, user_id: ObjectId, transaction_data: Dict) -> bool:
    """Check if transaction is a duplicate"""
    # Check for existing transaction with same date, amount, and description
    existing = await db.transactions.find_one({
        "user_id": user_id,
        "transaction_date": transaction_data["transaction_date"],
        "amount": transaction_data["amount"],
        "normalized_description": transaction_data["normalized_description"]
    })
    
    return existing is not None
