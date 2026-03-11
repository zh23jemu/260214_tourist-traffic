# Tourist Traffic Project

## Overview

This repository now contains two parallel tracks:

1. Engineering prototype

- FastAPI
- MySQL 8 via Docker
- SQLAlchemy
- JWT auth
- Vue 3 + Element Plus + ECharts frontend

2. Research system target

- Unified daily modeling dataset
- Multi-model experiments: ARIMA / Prophet / XGBoost / LightGBM / LSTM / TFT
- SHAP explainability
- Streamlit + Plotly interactive dashboard

The research-system route is the primary development direction for thesis alignment.

## Current Stack

- FastAPI
- MySQL 8 via Docker
- SQLAlchemy
- LightGBM / scikit-learn
- JWT auth
- Vue 3 frontend

## Setup

Detailed fresh-machine deployment steps are documented in [新电脑部署说明.md](C:/Coding/260214_tourist-traffic/新电脑部署说明.md).

1. Start MySQL:

```powershell
docker compose up -d
```

2. Configure environment:

```powershell
Copy-Item .env.example .env
```

3. Install dependencies:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Run the API:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to test APIs.

Default admin credentials are controlled by `.env`:

- username: `admin`
- password: `admin123`

5. Run the current frontend:

```powershell
cd frontend
npm run dev
```

## Current Prototype API Flow

1. `POST /api/v1/auth/login`
2. `POST /api/v1/data/import/excel` with `毕设数据统计.xlsx`
3. `POST /api/v1/features/build`
4. `POST /api/v1/models/train`
5. `POST /api/v1/models/predict`
6. `GET /api/v1/dashboard/overview`
7. `GET /api/v1/export/report?format=csv`

## Thesis-Aligned Development Direction

The thesis-aligned target is described in [技术方案.md](C:/Coding/260214_tourist-traffic/技术方案.md).

Planned additions:

- research data pipeline for unified modeling data
- ARIMA / Prophet / XGBoost / LSTM / TFT experiments
- SHAP-based explainability
- Streamlit + Plotly dashboard for research presentation

The existing FastAPI + Vue system remains available as an engineering prototype while the research system is built in parallel.
