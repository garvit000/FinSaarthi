FROM python:3.10-slim

WORKDIR /app

# Copy requirements from backend directory (relative to build context root)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project context
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
