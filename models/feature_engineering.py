import pandas as pd
import numpy as np
from datetime import datetime
import os

def load_data():
    if not os.path.exists("data"):
        raise FileNotFoundError("Data directory not found. Please run data/synthetic_generator.py first.")
    
    customers = pd.read_csv("data/customers.csv")
    transactions = pd.read_csv("data/transactions.csv")
    labels = pd.read_csv("data/labels.csv")
    
    # Convert dates
    transactions['date'] = pd.to_datetime(transactions['date'])
    
    return customers, transactions, labels

def feature_engineering(customers, transactions):
    print("Starting feature engineering...")
    
    features = []
    
    for _, customer in customers.iterrows():
        cust_id = customer['customer_id']
        cust_txns = transactions[transactions['customer_id'] == cust_id].sort_values('date')
        
        if cust_txns.empty:
            continue
            
        # 1. Salary Timing Deviation
        salary_txns = cust_txns[cust_txns['category'] == 'Salary']
        salary_dates = salary_txns['date'].dt.day.tolist()
        if salary_dates:
            avg_day = np.mean(salary_dates) # Should be close to 1
            # Current month (last salary) deviation
            last_salary_day = salary_dates[-1]
            salary_deviation = last_salary_day - 1 # Assuming 1st is normal
        else:
            salary_deviation = 0
            
        # 2. Savings Balance Change (approximate via net flow)
        # We don't have balance, so use net flow in last 30 days vs previous 30
        end_date = cust_txns['date'].max()
        last_30 = cust_txns[cust_txns['date'] > (end_date - pd.Timedelta(days=30))]
        prev_30 = cust_txns[(cust_txns['date'] <= (end_date - pd.Timedelta(days=30))) & 
                            (cust_txns['date'] > (end_date - pd.Timedelta(days=60)))]
        
        net_flow_last_30 = last_30[last_30['type'] == 'CREDIT']['amount'].sum() - last_30[last_30['type'] == 'DEBIT']['amount'].sum()
        net_flow_prev_30 = prev_30[prev_30['type'] == 'CREDIT']['amount'].sum() - prev_30[prev_30['type'] == 'DEBIT']['amount'].sum()
        
        savings_change_pct = 0
        if net_flow_prev_30 != 0:
            savings_change_pct = (net_flow_last_30 - net_flow_prev_30) / abs(net_flow_prev_30)

        # 3. Lending App Count (30-day rolling)
        lending_txns = last_30[last_30['category'] == 'Loan']
        lending_app_count = len(lending_txns)
        
        # 4. Bill Payment Delay
        # Look for Utilities in last 30 days
        utility_txns = last_30[last_30['category'] == 'Utilities']
        bill_delay = 0
        if not utility_txns.empty:
            last_bill_day = utility_txns['date'].iloc[-1].day
            # Expected date is 10th
            if last_bill_day > 10:
                bill_delay = last_bill_day - 10
        
        # 5. Discretionary Spend Ratio
        # (Dining + Entertainment) / Total Outflow
        discretionary_cat = ['Dining', 'Entertainment', 'Shopping']
        disc_last_30 = last_30[last_30['category'].isin(discretionary_cat)]['amount'].sum()
        total_outflow_last_30 = last_30[last_30['type'] == 'DEBIT']['amount'].sum()
        
        disc_ratio = 0
        if total_outflow_last_30 > 0:
            disc_ratio = disc_last_30 / total_outflow_last_30
            
        # Compare to 3-month average
        last_90 = cust_txns[cust_txns['date'] > (end_date - pd.Timedelta(days=90))]
        disc_last_90 = last_90[last_90['category'].isin(discretionary_cat)]['amount'].sum()
        total_outflow_last_90 = last_90[last_90['type'] == 'DEBIT']['amount'].sum()
        
        avg_disc_ratio = 0
        if total_outflow_last_90 > 0:
            avg_disc_ratio = disc_last_90 / total_outflow_last_90
            
        disc_ratio_change = disc_ratio - avg_disc_ratio

        # 6. ATM Withdrawal Frequency Change
        # Count ATM in last 30 vs avg per month
        atm_last_30 = len(last_30[last_30['category'] == 'Cash'])
        atm_last_90 = len(last_90[last_90['category'] == 'Cash'])
        avg_atm_monthly = atm_last_90 / 3
        
        atm_freq_change = atm_last_30 - avg_atm_monthly

        features.append({
            "customer_id": cust_id,
            "salary_deviation": salary_deviation,
            "savings_change_pct": savings_change_pct,
            "lending_app_count": lending_app_count,
            "bill_delay": bill_delay,
            "disc_ratio_change": disc_ratio_change,
            "atm_freq_change": atm_freq_change
        })
        
    return pd.DataFrame(features)

def main():
    if not os.path.exists("models"):
        os.makedirs("models")
        
    customers, transactions, labels = load_data()
    df_features = feature_engineering(customers, transactions)
    
    # Merge with labels
    df_final = pd.merge(df_features, labels, on='customer_id')
    
    # Save feature matrix
    df_final.to_csv("data/feature_matrix.csv", index=False)
    print(f"Feature matrix saved with {len(df_final)} rows.")

if __name__ == "__main__":
    main()
