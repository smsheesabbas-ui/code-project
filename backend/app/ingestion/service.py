import os
import uuid
import shutil
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, UploadFile, status
from datetime import datetime
from ..database import csv_imports, transactions, users
from ..models.csv_import import CSVImportCreate, CSVImport, ImportStatus, ColumnMapping, ImportPreview
from ..models.transaction import TransactionCreate, Transaction
from .csv_processor import CSVProcessor
from ..config import settings
import pandas as pd

class IngestionService:
    def __init__(self):
        self.processor = CSVProcessor()
        self.upload_dir = settings.UPLOAD_DIR
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)

    async def upload_csv(self, file: UploadFile, user_id: str) -> CSVImport:
        """Upload CSV file and create import record"""
        # Validate file
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV files are supported"
            )
        
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        file_path = os.path.join(self.upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create import record
        import_data = CSVImportCreate(
            filename=file.filename,
            file_size=file.size
        )
        
        import_dict = import_data.dict()
        import_dict.update({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "status": ImportStatus.PENDING,
            "file_path": file_path,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        await csv_imports.insert_one(import_dict)
        
        return CSVImport(**import_dict)

    async def process_csv(self, import_id: str, user_id: str) -> CSVImport:
        """Process CSV file and detect columns"""
        # Get import record
        import_record = await csv_imports.find_one({"id": import_id, "user_id": user_id})
        if not import_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import not found"
            )
        
        try:
            # Update status to processing
            await csv_imports.update_one(
                {"id": import_id},
                {"$set": {"status": ImportStatus.PROCESSING, "updated_at": datetime.utcnow()}}
            )
            
            # Read CSV file
            df = pd.read_csv(import_record["file_path"])
            
            # Detect columns
            mapping, confidence = self.processor.detect_columns(df)
            
            # Generate preview
            preview_rows = self.processor.generate_preview(df, mapping)
            
            # Update import record
            update_data = {
                "status": ImportStatus.PREVIEW_READY,
                "column_mapping": mapping.dict(),
                "detection_confidence": confidence,
                "total_rows": len(df),
                "updated_at": datetime.utcnow()
            }
            
            await csv_imports.update_one(
                {"id": import_id},
                {"$set": update_data}
            )
            
            # Get updated record
            updated_import = await csv_imports.find_one({"id": import_id})
            return CSVImport(**updated_import)
            
        except Exception as e:
            # Update status to failed
            await csv_imports.update_one(
                {"id": import_id},
                {"$set": {
                    "status": ImportStatus.FAILED,
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process CSV: {str(e)}"
            )

    async def get_preview(self, import_id: str, user_id: str) -> ImportPreview:
        """Get import preview"""
        import_record = await csv_imports.find_one({"id": import_id, "user_id": user_id})
        if not import_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import not found"
            )
        
        if import_record["status"] != ImportStatus.PREVIEW_READY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Import not ready for preview"
            )
        
        # Read CSV and generate preview
        df = pd.read_csv(import_record["file_path"])
        mapping = ColumnMapping(**import_record["column_mapping"])
        preview_rows = self.processor.generate_preview(df, mapping)
        
        # Calculate validation summary
        valid_rows = len([r for r in preview_rows if not r.validation_errors])
        error_rows = len(preview_rows) - valid_rows
        duplicate_rows = 0  # TODO: Implement duplicate detection
        
        validation_summary = {
            "valid_rows": valid_rows,
            "error_rows": error_rows,
            "duplicate_rows": duplicate_rows
        }
        
        return ImportPreview(
            import_id=import_id,
            status=import_record["status"],
            column_mapping=mapping,
            detection_confidence=import_record["detection_confidence"],
            rows=preview_rows,
            total_rows=import_record["total_rows"],
            validation_summary=validation_summary
        )

    async def update_column_mapping(self, import_id: str, user_id: str, mapping: ColumnMapping) -> CSVImport:
        """Update column mapping"""
        import_record = await csv_imports.find_one({"id": import_id, "user_id": user_id})
        if not import_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import not found"
            )
        
        await csv_imports.update_one(
            {"id": import_id},
            {"$set": {
                "column_mapping": mapping.dict(),
                "updated_at": datetime.utcnow()
            }}
        )
        
        updated_import = await csv_imports.find_one({"id": import_id})
        return CSVImport(**updated_import)

    async def confirm_import(self, import_id: str, user_id: str, duplicate_action: str = "skip") -> Dict[str, Any]:
        """Confirm and import transactions"""
        import_record = await csv_imports.find_one({"id": import_id, "user_id": user_id})
        if not import_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Import not found"
            )
        
        try:
            # Update status to processing
            await csv_imports.update_one(
                {"id": import_id},
                {"$set": {"status": ImportStatus.PROCESSING, "updated_at": datetime.utcnow()}}
            )
            
            # Read and normalize CSV
            df = pd.read_csv(import_record["file_path"])
            mapping = ColumnMapping(**import_record["column_mapping"])
            normalized_df = self.processor.normalize_dataframe(df, mapping)
            
            # Process each row
            imported_count = 0
            skipped_duplicates = 0
            skipped_errors = 0
            transaction_ids = []
            
            for _, row in normalized_df.iterrows():
                # Skip rows with validation errors
                if not row.get('transaction_date') or row.get('amount') is None:
                    skipped_errors += 1
                    continue
                
                # Check for duplicates
                is_duplicate = await self._check_duplicate(user_id, row)
                if is_duplicate and duplicate_action == "skip":
                    skipped_duplicates += 1
                    continue
                
                # Create transaction
                transaction_data = TransactionCreate(
                    transaction_date=datetime.strptime(row['transaction_date'], '%Y-%m-%d'),
                    description=row['description'],
                    amount=float(row['amount']),
                    import_id=import_id,
                    import_timestamp=datetime.utcnow(),
                    source_file_reference=f"{import_record['filename']}:{row['row_number']}"
                )
                
                transaction_dict = transaction_data.dict()
                transaction_dict.update({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "is_duplicate": is_duplicate,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                await transactions.insert_one(transaction_dict)
                transaction_ids.append(transaction_dict["id"])
                imported_count += 1
            
            # Update import record
            await csv_imports.update_one(
                {"id": import_id},
                {"$set": {
                    "status": ImportStatus.COMPLETED,
                    "processed_rows": imported_count,
                    "duplicate_rows": skipped_duplicates,
                    "error_rows": skipped_errors,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return {
                "import_id": import_id,
                "status": ImportStatus.COMPLETED,
                "imported_count": imported_count,
                "skipped_duplicates": skipped_duplicates,
                "skipped_errors": skipped_errors,
                "transactions": transaction_ids
            }
            
        except Exception as e:
            await csv_imports.update_one(
                {"id": import_id},
                {"$set": {
                    "status": ImportStatus.FAILED,
                    "error_message": str(e),
                    "updated_at": datetime.utcnow()
                }}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to import transactions: {str(e)}"
            )

    async def _check_duplicate(self, user_id: str, row: Dict[str, Any]) -> bool:
        """Check if transaction is duplicate"""
        # Simple duplicate check based on date, amount, and description
        existing = await transactions.find_one({
            "user_id": user_id,
            "transaction_date": datetime.strptime(row['transaction_date'], '%Y-%m-%d'),
            "amount": float(row['amount']),
            "description": row['description']
        })
        return existing is not None

    async def get_imports(self, user_id: str) -> List[CSVImport]:
        """Get all imports for user"""
        cursor = csv_imports.find({"user_id": user_id}).sort("created_at", -1)
        imports = []
        async for import_doc in cursor:
            imports.append(CSVImport(**import_doc))
        return imports

ingestion_service = IngestionService()
