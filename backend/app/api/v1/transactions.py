from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, date
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, TransactionCreate, TransactionUpdate, TransactionResponse
from app.core.database import get_database
from bson import ObjectId
from pydantic import BaseModel

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    per_page: int


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Transactions endpoint working"}

@router.get("/")
async def get_transactions(
    page: int = 1,
    per_page: int = 50,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """List demo user's transactions with filtering and pagination"""
    db = get_database()
    
    # Use demo user data
    demo_user_id = "69a235b64db7304c81b42977"
    
    # Build filter
    filter_dict = {"user_id": demo_user_id}
    
    if start_date:
        filter_dict["transaction_date"] = {"$gte": datetime.combine(start_date, datetime.min.time())}
    
    if end_date:
        if "transaction_date" in filter_dict:
            filter_dict["transaction_date"]["$lte"] = datetime.combine(end_date, datetime.max.time())
        else:
            filter_dict["transaction_date"] = {"$lte": datetime.combine(end_date, datetime.max.time())}
    
    if category:
        filter_dict["category"] = category
    
    if search:
        filter_dict["$or"] = [
            {"description": {"$regex": search, "$options": "i"}},
            {"normalized_description": {"$regex": search.lower(), "$options": "i"}}
        ]
    
    # Get total count
    total = await db.transactions.count_documents(filter_dict)
    
    # Get transactions with pagination
    skip = (page - 1) * per_page
    cursor = db.transactions.find(filter_dict).sort("transaction_date", -1).skip(skip).limit(per_page)
    
    transactions = []
    async for transaction_doc in cursor:
        # Create simple transaction dict
        transaction_data = {
            "id": str(transaction_doc["_id"]),
            "date": transaction_doc["transaction_date"].strftime("%Y-%m-%d"),
            "description": transaction_doc["description"],
            "amount": transaction_doc["amount"],
            "category": transaction_doc.get("category", "Uncategorized"),
            "balance": transaction_doc.get("balance", 0)
        }
        transactions.append(transaction_data)
    
    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "per_page": per_page
    }


# Note: Individual transaction endpoint removed for demo mode


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a transaction"""
    db = get_database()
    
    # Check if transaction exists
    existing = await db.transactions.find_one({
        "_id": ObjectId(transaction_id),
        "user_id": current_user.id
    })
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Update transaction
    update_data = transaction_update.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        # Update normalized description if description changed
        if "description" in update_data:
            update_data["normalized_description"] = update_data["description"].lower()
        
        await db.transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": update_data}
        )
    
    # Get updated transaction
    updated_transaction = await db.transactions.find_one({"_id": ObjectId(transaction_id)})
    return TransactionResponse(**updated_transaction)


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a transaction"""
    db = get_database()
    
    # Check if transaction exists
    existing = await db.transactions.find_one({
        "_id": ObjectId(transaction_id),
        "user_id": current_user.id
    })
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Delete transaction
    await db.transactions.delete_one({"_id": ObjectId(transaction_id)})
    
    return {"message": "Transaction deleted successfully"}


@router.post("", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
):
    """Create a new transaction"""
    db = get_database()
    
    # Check for duplicates
    normalized_description = transaction_data.description.lower()
    existing = await db.transactions.find_one({
        "transaction_date": transaction_data.transaction_date,
        "amount": transaction_data.amount,
        "normalized_description": normalized_description
    })
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Transaction already exists"
        )
    
    # Create transaction
    transaction = Transaction(
        description=transaction_data.description,
        normalized_description=normalized_description,
        **transaction_data.dict(exclude={"description"})
    )
    
    result = await db.transactions.insert_one(transaction.dict(by_alias=True))
    transaction.id = result.inserted_id
    
    return TransactionResponse(**transaction.dict())
