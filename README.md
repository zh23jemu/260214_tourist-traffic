# Tourist Traffic Backend (Phase 1)

## Run

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to test APIs.

## Suggested API Order

1. `POST /api/v1/data/import/excel` with `毕设数据统计.xlsx`
2. `POST /api/v1/features/build`
3. `POST /api/v1/models/train`
4. `POST /api/v1/models/predict`
5. `GET /api/v1/predictions`

