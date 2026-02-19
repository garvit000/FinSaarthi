import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

# Initialize Faker
fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# Configuration
NUM_CUSTOMERS = 10000
DAYS_HISTORY = 180
STRESS_START_DAY = 150  # Stress signals start 30 days before end (day 150 of 180)
DELINQUENCY_RATE = 0.05 # 5% of customers go delinquent

def generate_customers():
    print(f"Generating {NUM_CUSTOMERS} customers...")
    customers = []
    for i in range(NUM_CUSTOMERS):
        is_delinquent = 1 if i < (NUM_CUSTOMERS * DELINQUENCY_RATE) else 0
        
        income = round(np.random.normal(60000, 15000), 2)
        if income < 20000: income = 20000
        
        loan_amount = round(np.random.normal(income * 3, income * 0.5), 2)
        emi_amount = round(loan_amount / 60, 2) # 5 year loan roughly
        
        customers.append({
            "customer_id": i,
            "name": fake.name(),
            "age": np.random.randint(22, 60),
            "income": income,
            "loan_amount": loan_amount,
            "emi_amount": emi_amount,
            "join_date": fake.date_between(start_date='-2y', end_date='-1y'),
            "is_delinquent": is_delinquent
        })
    return pd.DataFrame(customers)

def generate_transactions(customers_df):
    print("Generating transactions...")
    all_transactions = []
    
    start_date = datetime.now() - timedelta(days=DAYS_HISTORY)
    
    for _, customer in customers_df.iterrows():
        customer_id = customer['customer_id']
        income = customer['income']
        is_delinquent = customer['is_delinquent']
        
        # Monthly Salary Pattern
        salary_day = 1 # Usually 1st of month
        
        # Daily transaction loop
        for day in range(DAYS_HISTORY):
            current_date = start_date + timedelta(days=day)
            is_stress_period = is_delinquent and day >= STRESS_START_DAY
            
            # --- Salary ---
            if current_date.day == salary_day:
                # If stress period, salary might be delayed (we simulate by skipping here and adding later, 
                # or just slight variation. For simplicity, let's say functionality wise:
                # Normal: Salary on 1st.
                # Stress: Salary might come on 5th-10th. (We will implement this by checking logic)
                pass 

            # Improved Salary Logic to handle delays
            actual_salary_day = 1
            if is_stress_period:
                actual_salary_day = random.randint(5, 10) # Salary delayed to 5th-10th
            
            if current_date.day == actual_salary_day:
                 all_transactions.append({
                    "customer_id": customer_id,
                    "date": current_date.date(),
                    "type": "CREDIT",
                    "amount": income,
                    "category": "Salary",
                    "merchant": "Employer"
                })

            # --- Random Daily Spending ---
            # Discretionary spending (Dining, Entertainment)
            # Stress: 60-80% reduction
            if random.random() < 0.3: # 30% chance of spend per day
                amount = random.uniform(20, 200)
                category = random.choice(["Dining", "Entertainment", "Shopping"])
                
                if is_stress_period:
                    amount = amount * 0.3 # Reduced spending
                
                all_transactions.append({
                    "customer_id": customer_id,
                    "date": current_date.date(),
                    "type": "DEBIT",
                    "amount": round(amount, 2),
                    "category": category,
                    "merchant": fake.company()
                })

            # --- Bill Payments ---
            # Utilities, Rent, etc. Usually around 10th
            if current_date.day == 10:
                # Stress: Pay late (e.g., 20th-25th)
                if is_stress_period:
                     # We skip here, handle in "Late Bill" block or just probability check
                     # Let's say 80% chance they miss it today and pay later
                     if random.random() < 0.8:
                         pass # Missed
                     else:
                        all_transactions.append({
                             "customer_id": customer_id,
                             "date": current_date.date(),
                             "type": "DEBIT",
                             "amount": random.uniform(100, 300),
                             "category": "Utilities",
                             "merchant": "Utility Co"
                        })
                else:
                     all_transactions.append({
                         "customer_id": customer_id,
                         "date": current_date.date(),
                         "type": "DEBIT",
                         "amount": random.uniform(100, 300),
                         "category": "Utilities",
                         "merchant": "Utility Co"
                    })
            
            # Late Bill Payment (Stress)
            if is_stress_period and current_date.day == 25:
                 # Catch up on bills
                 all_transactions.append({
                     "customer_id": customer_id,
                     "date": current_date.date(),
                     "type": "DEBIT",
                     "amount": random.uniform(100, 300),
                     "category": "Utilities",
                     "merchant": "Utility Co (Late)"
                })

            # --- Lending Apps (Stress Signal) ---
            if is_stress_period:
                if random.random() < 0.1: # 10% chance per day
                     all_transactions.append({
                        "customer_id": customer_id,
                        "date": current_date.date(),
                        "type": "CREDIT",
                        "amount": random.uniform(500, 2000),
                        "category": "Loan",
                        "merchant": random.choice(["MoneyTap", "PayTM Loan", "KreditBee"])
                    })

            # --- Cash Hoarding (ATM) ---
            # Stress: 3x increase
            atm_prob = 0.05
            if is_stress_period:
                atm_prob = 0.15
            
            if random.random() < atm_prob:
                 all_transactions.append({
                    "customer_id": customer_id,
                    "date": current_date.date(),
                    "type": "DEBIT",
                    "amount": random.uniform(100, 500),
                    "category": "Cash",
                    "merchant": "ATM Withdrawal"
                })

    return pd.DataFrame(all_transactions)

def main():
    if not os.path.exists("data"):
        os.makedirs("data")

    df_customers = generate_customers()
    df_transactions = generate_transactions(df_customers)
    
    # Save to CSV
    df_customers.to_csv("data/customers.csv", index=False)
    df_transactions.to_csv("data/transactions.csv", index=False)
    
    # Labels (just IDs and label)
    df_labels = df_customers[['customer_id', 'is_delinquent']]
    df_labels.to_csv("data/labels.csv", index=False)
    
    print("Data generation complete.")
    print(f"Customers: {len(df_customers)}")
    print(f"Transactions: {len(df_transactions)}")

if __name__ == "__main__":
    main()
