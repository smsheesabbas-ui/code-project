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


@router.post("/upload")
async def upload_csv_file(file: UploadFile = File(...)):
    """Upload CSV file for processing - no auth required for demo"""
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB"
        )
    
    db = get_database()
    
    # Use demo user data
    demo_user_id = "69a235b64db7304c81b42977"
    
    # Create import record
    import_record = {
        "user_id": demo_user_id,
        "filename": file.filename,
        "status": "uploaded",
        "file_size": file.size,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.imports.insert_one(import_record)
    import_id = str(result.inserted_id)
    
    # Save file temporarily
    file_path = f"/tmp/{import_id}.csv"
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the file immediately
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
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
            
            # Update import record with processed data
            update_data = {
                "status": "preview_ready",
                "total_rows": total_rows,
                "detected_columns": detected_columns,
                "preview_data": preview_data,
                "updated_at": datetime.utcnow()
            }
            
            await db.imports.update_one(
                {"_id": ObjectId(import_id)},
                {"$set": update_data}
            )
            
        except Exception as processing_error:
            # Update status to failed
            await db.imports.update_one(
                {"_id": ObjectId(import_id)},
                {"$set": {
                    "status": "failed",
                    "error_message": str(processing_error),
                    "updated_at": datetime.utcnow()
                }}
            )
        
        return {
            "id": import_id,
            "filename": file.filename,
            "status": "uploaded",
            "file_size": file.size
        }
        
    except Exception as e:
        # Clean up on error
        await db.imports.delete_one({"_id": result.inserted_id})
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


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
async def get_import_preview(import_id: str):
    """Get import preview and column mapping - no auth required for demo"""
    db = get_database()
    
    # Use demo user data
    demo_user_id = "69a235b64db7304c81b42977"
    
    csv_import = await db.imports.find_one({
        "_id": ObjectId(import_id),
        "user_id": demo_user_id
    })
    
    if not csv_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found"
        )
    
    # Convert MongoDB document to response format
    response_data = {
        "id": str(csv_import["_id"]),
        "user_id": str(csv_import["user_id"]),
        "filename": csv_import["filename"],
        "file_size": csv_import["file_size"],
        "status": csv_import["status"],
        "total_rows": csv_import.get("total_rows", 0),
        "processed_rows": csv_import.get("processed_rows", 0),
        "duplicate_rows": csv_import.get("duplicate_rows", 0),
        "error_rows": csv_import.get("error_rows", 0),
        "column_mapping": csv_import.get("column_mapping"),
        "detected_columns": csv_import.get("detected_columns"),
        "preview_data": csv_import.get("preview_data"),
        "error_message": csv_import.get("error_message"),
        "created_at": csv_import["created_at"]
    }
    
    return CSVImportResponse(**response_data)


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
