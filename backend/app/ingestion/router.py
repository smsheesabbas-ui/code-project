from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, status
from typing import List
from ..service import ingestion_service
from ..models.csv_import import CSVImport, ImportPreview, ColumnMapping, ImportStatus
from ..auth.router import get_current_user
from ..models.user import User
from ..tasks import process_csv_import

router = APIRouter(prefix="/imports", tags=["imports"])

@router.post("/upload", response_model=CSVImport)
async def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload CSV file"""
    import_record = await ingestion_service.upload_csv(file, current_user.id)
    
    # Process CSV in background (async for iteration 2)
    process_csv_import.delay(import_record.id, current_user.id)
    
    return import_record

@router.get("/{import_id}/preview", response_model=ImportPreview)
async def get_preview(
    import_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get import preview"""
    return await ingestion_service.get_preview(import_id, current_user.id)

@router.put("/{import_id}/column-mapping", response_model=CSVImport)
async def update_column_mapping(
    import_id: str,
    mapping: ColumnMapping,
    current_user: User = Depends(get_current_user)
):
    """Update column mapping"""
    return await ingestion_service.update_column_mapping(import_id, current_user.id, mapping)

@router.post("/{import_id}/confirm")
async def confirm_import(
    import_id: str,
    duplicate_action: str = "skip",
    current_user: User = Depends(get_current_user)
):
    """Confirm and import transactions"""
    return await ingestion_service.confirm_import(import_id, current_user.id, duplicate_action)

@router.get("/", response_model=List[CSVImport])
async def get_imports(
    current_user: User = Depends(get_current_user)
):
    """Get all imports"""
    return await ingestion_service.get_imports(current_user.id)
