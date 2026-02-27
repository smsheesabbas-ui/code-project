db = db.getSiblingDB('cashflow');

// Create collections and indexes
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "auth_provider": 1, "auth_provider_id": 1 });

db.transactions.createIndex({ "user_id": 1, "transaction_date": -1 });
db.transactions.createIndex({ "user_id": 1, "entity_id": 1 });
db.transactions.createIndex({ "user_id": 1, "import_id": 1 });

db.entities.createIndex({ "user_id": 1, "normalized_name": 1 }, { unique: true });

db.csv_imports.createIndex({ "user_id": 1, "created_at": -1 });

db.expense_categories.createIndex({ "user_id": 1, "name": 1 }, { unique: true });

db.revenue_streams.createIndex({ "user_id": 1, "name": 1 }, { unique: true });

db.tags.createIndex({ "user_id": 1, "name": 1 }, { unique: true });

// Insert default expense categories
db.expense_categories.insertMany([
  { name: "Software & Subscriptions", user_id: null, is_default: true },
  { name: "Office Expenses", user_id: null, is_default: true },
  { name: "Marketing", user_id: null, is_default: true },
  { name: "Professional Services", user_id: null, is_default: true },
  { name: "Travel & Transport", user_id: null, is_default: true },
  { name: "Meals & Entertainment", user_id: null, is_default: true },
  { name: "Rent/Utilities", user_id: null, is_default: true },
  { name: "Equipment", user_id: null, is_default: true },
  { name: "Taxes", user_id: null, is_default: true },
  { name: "Other", user_id: null, is_default: true }
]);

print("Database initialized successfully");
