# LSTM Model Training Guide

## Prerequisites

```bash
cd /projects/arra4944/nba-predictive-analytics/nba-analytics
pip install -r requirements.txt
```

## Training Steps

### 1. Start Database Services
```bash
docker-compose up postgres redis -d
```

### 2. Initialize Database
```bash
python -m models.database
```

### 3. Ingest Team Data
```bash
python scripts/run_ingestion.py
```

### 4. Ingest Historical Data (5 Seasons)
```bash
python -m services.historical_ingestion
```
Fetches data for seasons 2020-21 through 2024-25. Takes ~2-3 minutes.

### 5. Train the Model
```bash
python -m ml.training_pipeline
```
Trains LSTM, saves weights to `trained_models/`, and generates predictions.

## Verify

Check predictions via API:
```bash
curl http://localhost:8000/api/predictions
```

Or view in dashboard under the "Predictions" tab.

## Retraining

```bash
python -m ml.training_pipeline
```
Or via API: `POST /api/model/retrain`
