"""
Batch scorer: Runs the trained XGBoost model against all customers
and populates the risk_scores table in the database.
"""
import pandas as pd
import numpy as np
import pickle
import shap
import json
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, RiskScore, init_db

def main():
    # Load model
    with open("models/xgboost_model.pkl", "rb") as f:
        model = pickle.load(f)
    print("Model loaded.")

    # Load feature matrix
    df = pd.read_csv("data/feature_matrix.csv")
    print(f"Feature matrix: {len(df)} rows")

    feature_cols = ["salary_deviation", "savings_change_pct", "lending_app_count",
                    "bill_delay", "disc_ratio_change", "atm_freq_change"]

    X = df[feature_cols]
    probs = model.predict_proba(X)[:, 1]
    scores = probs * 100  # 0-100 scale

    # SHAP for top factors per customer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Init DB
    init_db()
    db = SessionLocal()

    # Clear existing scores
    db.query(RiskScore).delete()
    db.commit()

    print("Inserting risk scores...")
    batch = []
    for i, row in df.iterrows():
        cust_id = int(row["customer_id"])
        score = float(scores[i])

        # Top 3 SHAP factors
        sv = shap_values[i]
        pairs = list(zip(feature_cols, sv))
        pairs.sort(key=lambda x: abs(x[1]), reverse=True)
        top_factors = [{"feature": k, "impact": round(float(v), 4)} for k, v in pairs[:3]]

        batch.append({
            "customer_id": cust_id,
            "date": datetime.utcnow(),
            "score": round(score, 2),
            "risk_factors": json.dumps(top_factors)
        })

        if len(batch) >= 500:
            db.bulk_insert_mappings(RiskScore, batch)
            db.commit()
            batch = []
            print(f"  Scored {i+1}/{len(df)} customers...")

    if batch:
        db.bulk_insert_mappings(RiskScore, batch)
        db.commit()

    db.close()

    high = sum(1 for s in scores if s > 70)
    med = sum(1 for s in scores if 30 < s <= 70)
    low = sum(1 for s in scores if s <= 30)
    print(f"\nDone! Scored {len(df)} customers.")
    print(f"  High risk (>70): {high}")
    print(f"  Medium risk (30-70): {med}")
    print(f"  Low risk (<=30): {low}")

if __name__ == "__main__":
    main()
