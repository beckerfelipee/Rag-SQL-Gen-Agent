@echo off
REM Run the Streamlit RAG SQL App from the project root
streamlit run Code\UI.py --server.headless true
REM Wait a moment for the server to start, then open the browser
powershell -Command "Start-Sleep -Seconds 5; Start-Process http://localhost:8501"
