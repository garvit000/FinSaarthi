from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
from datetime import datetime

DATABASE_URL = "sqlite:///./lighthouse.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, unique=True, index=True) # From CSV
    name = Column(String, index=True)
    age = Column(Integer)
    income = Column(Float)
    loan_amount = Column(Float)
    emi_amount = Column(Float)
    join_date = Column(String) # Storing as string for simplicity in SQLite
    is_delinquent = Column(Integer)
    
    transactions = relationship("Transaction", back_populates="customer")
    risk_scores = relationship("RiskScore", back_populates="customer")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    date = Column(DateTime)
    type = Column(String)
    amount = Column(Float)
    category = Column(String)
    merchant = Column(String)
    
    customer = relationship("Customer", back_populates="transactions")

class RiskScore(Base):
    __tablename__ = "risk_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"))
    date = Column(DateTime, default=datetime.utcnow)
    score = Column(Float) # 0-100
    risk_factors = Column(JSON) # Store top factors
    
    customer = relationship("Customer", back_populates="risk_scores")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_data():
    print("Seeding database...")
    db = SessionLocal()
    
    # Check if data exists
    if db.query(Customer).count() > 0:
        print("Database already seeded.")
        return

    try:
        # Load CSVs
        df_customers = pd.read_csv("data/customers.csv")
        df_transactions = pd.read_csv("data/transactions.csv")
        
        # Insert Customers
        print("Inserting customers...")
        customers_data = df_customers.to_dict(orient='records')
        db.bulk_insert_mappings(Customer, customers_data)
        db.commit()
        
        # Insert Transactions (Batching might be needed for large data)
        print("Inserting transactions...")
         # Validating dates
        df_transactions['date'] = pd.to_datetime(df_transactions['date'])
        
        # SQLite bulk insert can be slow or hit limits, let's do chunks
        chunk_size = 10000
        for i in range(0, len(df_transactions), chunk_size):
            chunk = df_transactions.iloc[i:i+chunk_size]
            db.bulk_insert_mappings(Transaction, chunk.to_dict(orient='records'))
            db.commit()
            print(f"Inserted {i+len(chunk)} transactions...")
            
        print("Database seeding complete.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_data()
