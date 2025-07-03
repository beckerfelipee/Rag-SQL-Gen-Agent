@echo off
REM Run the Streamlit RAG SQL App
cd Code
start "" cmd /c "streamlit run UI.py --server.headless true"
REM Wait a moment for the server to start, then open the browser
powershell -Command "Start-Sleep -Seconds 3; Start-Process http://localhost:8501"
