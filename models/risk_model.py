import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, classification_report
import shap
import mlflow
import mlflow.xgboost
import pickle
import os

def load_data():
    if not os.path.exists("data/feature_matrix.csv"):
        raise FileNotFoundError("Feature matrix not found. Please run models/feature_engineering.py first.")
    
    df = pd.read_csv("data/feature_matrix.csv")
    return df

def train_model(df):
    print("Training XGBoost model...")
    
    X = df.drop(['customer_id', 'is_delinquent'], axis=1)
    y = df['is_delinquent']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    model = xgb.XGBClassifier(
        max_depth=6,
        n_estimators=100,
        learning_rate=0.1,
        eval_metric='logloss',
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob)
    
    print(f"Accuracy: {accuracy:.4f}")
    print(f"AUC-ROC: {roc_auc:.4f}")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # SHAP Explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    
    # Save Model
    with open("models/xgboost_model.pkl", "wb") as f:
        pickle.dump(model, f)
        
    # Save Explainer (for later use in API)
    # We might need the explainer object or just use TreeExplainer on loaded model
    # Saving just in case
    # with open("models/shap_explainer.pkl", "wb") as f:
    #     pickle.dump(explainer, f)
        
    print("Model saved to models/xgboost_model.pkl")

if __name__ == "__main__":
    mlflow.autolog()
    
    if not os.path.exists("models"):
        os.makedirs("models")
        
    try:
        df = load_data()
        train_model(df)
    except FileNotFoundError as e:
        print(e)
