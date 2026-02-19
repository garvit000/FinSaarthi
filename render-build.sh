#!/bin/bash
# Render build script for backend
# This script runs on deploy to generate data, train model, and seed DB

set -e

echo "Installing dependencies..."
pip install -r backend/requirements.txt

echo "Generating synthetic data..."
python data/synthetic_generator.py

echo "Running feature engineering..."
python models/feature_engineering.py

echo "Training risk model..."
python models/risk_model.py

echo "Seeding database..."
python backend/database.py

echo "Running batch scorer..."
python models/batch_scorer.py

echo "Build complete!"
