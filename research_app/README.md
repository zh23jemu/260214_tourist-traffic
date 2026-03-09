# Research App

This directory contains the thesis-aligned research-system track.

Planned scope:

- unified research dataset pipeline
- descriptive statistics and explainability
- ARIMA / Prophet / XGBoost / LightGBM / LSTM / TFT experiments
- Streamlit + Plotly dashboard

Current status:

- directory structure initialized
- Streamlit app entrypoint added
- dashboard supports overview metrics, date-type analysis, holiday analysis, model roadmap and raw-data table
- data-loading and descriptive chart modules added
- model experiment modules reserved for incremental implementation

Run the dashboard:

```powershell
.\venv\Scripts\python.exe -m streamlit run research_app\app.py
```
