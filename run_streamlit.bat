@echo off
cd /d "%~dp0"
set PYTHONPATH=%CD%
call .\venv\Scripts\activate
REM Run the Streamlit RAG SQL App from the project root
streamlit run Code\UI.py --server.headless true
echo "Streamlit app is running. Press Ctrl+C to stop."
REM Wait a moment for the server to start, then open the browser
powershell -Command "Start-Sleep -Seconds 5; Start-Process http://localhost:8501"
pause
echo Current directory: %CD%
echo PYTHONPATH: %PYTHONPATH%
where streamlit
pause
