from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import xgboost as xgb
import pandas as pd
import numpy as np
import pickle
import shap
from typing import List, Optional
import asyncio
import random
import json
from datetime import datetime
from .database import SessionLocal, Customer, Transaction, RiskScore

app = FastAPI(title="Lighthouse API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model
MODEL_PATH = "models/xgboost_model.pkl"
model = None

@app.on_event("startup")
def load_model():
    global model
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")

# Pydantic Models
class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    age: int
    income: float
    loan_amount: float
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None

class ScoreRequest(BaseModel):
    customer_id: int

class ScoreResponse(BaseModel):
    customer_id: int
    risk_score: float # 0-100
    risk_level: str
    risk_factors: List[dict]

class SimulationRequest(BaseModel):
    income: float
    savings_change_pct: float
    lending_app_count: int
    bill_delay: int
    disc_ratio_change: float
    atm_freq_change: float
    salary_deviation: float

# Routes
@app.get("/customers", response_model=List[CustomerResponse])
def get_customers(skip: int = 0, limit: int = 100):
    db = SessionLocal()
    customers = db.query(Customer).offset(skip).limit(limit).all()
    
    results = []
    for c in customers:
        # Fetch latest risk score
        latest_score = db.query(RiskScore).filter(RiskScore.customer_id == c.customer_id).order_by(RiskScore.date.desc()).first()
        score_val = latest_score.score if latest_score else None
        
        level = "Low"
        if score_val:
            if score_val > 70: level = "High"
            elif score_val > 30: level = "Medium"
            
        results.append({
            "customer_id": c.customer_id,
            "name": c.name,
            "age": c.age,
            "income": c.income,
            "loan_amount": c.loan_amount,
            "risk_score": score_val,
            "risk_level": level
        })
    db.close()
    return results

@app.get("/customer/{customer_id}")
def get_customer_detail(customer_id: int):
    db = SessionLocal()
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        db.close()
        raise HTTPException(status_code=404, detail="Customer not found")
        
    transactions = db.query(Transaction).filter(Transaction.customer_id == customer_id).order_by(Transaction.date.desc()).limit(50).all()
    
    latest_score = db.query(RiskScore).filter(RiskScore.customer_id == customer_id).order_by(RiskScore.date.desc()).first()
    
    db.close()
    
    return {
        "profile": customer,
        "risk_score": latest_score,
        "transactions": transactions
    }

@app.post("/score", response_model=ScoreResponse)
def score_customer(req: ScoreRequest):
    db = SessionLocal()
    existing_score = db.query(RiskScore).filter(RiskScore.customer_id == req.customer_id).order_by(RiskScore.date.desc()).first()
    db.close()
    
    if existing_score:
        level = "Low"
        if existing_score.score > 70: level = "High"
        elif existing_score.score > 30: level = "Medium"
            
        return {
            "customer_id": req.customer_id,
            "risk_score": existing_score.score,
            "risk_level": level,
            "risk_factors": existing_score.risk_factors or []
        }
    
    raise HTTPException(status_code=404, detail="Score not found (run batch scoring first)")

@app.post("/simulate")
def simulate_risk(req: SimulationRequest):
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    input_data = pd.DataFrame([{
        "salary_deviation": req.salary_deviation,
        "savings_change_pct": req.savings_change_pct,
        "lending_app_count": req.lending_app_count,
        "bill_delay": req.bill_delay,
        "disc_ratio_change": req.disc_ratio_change,
        "atm_freq_change": req.atm_freq_change
    }])
    
    prob = model.predict_proba(input_data)[0][1]
    score = float(prob * 100)
    
    # SHAP for finding contributors
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(input_data)
    
    # map shap values to features
    feature_names = input_data.columns
    contributions = zip(feature_names, shap_values[0])
    
    # Sort by absolute contribution
    sorted_contribs = sorted(contributions, key=lambda x: abs(x[1]), reverse=True)
    
    top_factors = [{"feature": k, "impact": float(v)} for k, v in sorted_contribs[:3]]
    
    level = "Low"
    if score > 70: level = "High"
    elif score > 30: level = "Medium"
    
    return {
        "risk_score": score,
        "risk_level": level,
        "top_factors": top_factors
    }

# --- Real-time Simulation ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/simulate")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Simulate a transaction event every 2 seconds
            await asyncio.sleep(2)
            
            # Pick random customer
            customer_id = random.randint(0, 500) # limiting to first 500 for demo overlap with delinquent
            
            # Generate random score change
            # In real system, we'd add txn and rescore. Here we mock:
            new_score = random.uniform(10, 95)
            
            # Alert logic
            is_alert = new_score > 75
            
            event = {
                "customer_id": customer_id,
                "name": f"Customer {customer_id}", # Ideally fetch name from DB but ok
                "new_score": new_score,
                "alert": is_alert,
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_text(json.dumps(event))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        # manager.disconnect(websocket) # might fail if already closed
