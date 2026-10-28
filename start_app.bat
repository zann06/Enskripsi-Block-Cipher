@echo off
cd C:\project\Kriptografi
call .venv\Scripts\Activate.ps1 2>nul
python -m streamlit run app.py --server.headless true --server.port 8501