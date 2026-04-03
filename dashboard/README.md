# Dashboard

Normalized dashboard module boundary.

## Entrypoints
- dashboard/app.py (normalized wrapper entrypoint)
- src/dashboard.py (active runtime entrypoint for compatibility)

## Run
streamlit run dashboard/app.py --server.headless true

Compatibility launchers still use src/dashboard.py to avoid runtime breakage.
