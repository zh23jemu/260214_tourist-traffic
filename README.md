# Tourist Traffic Backend

## Stack

- FastAPI
- MySQL 8 via Docker
- SQLAlchemy
- LightGBM / scikit-learn
- JWT auth

## Setup

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

## Suggested API Order

1. `POST /api/v1/auth/login`
2. `POST /api/v1/data/import/excel` with `毕设数据统计.xlsx`
3. `POST /api/v1/features/build`
4. `POST /api/v1/models/train`
5. `POST /api/v1/models/predict`
6. `GET /api/v1/dashboard/overview`
7. `GET /api/v1/export/report?format=csv`
