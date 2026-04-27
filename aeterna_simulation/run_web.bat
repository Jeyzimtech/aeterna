@echo off
echo Starting Aeterna Sol-IV Digital Twin Web Server...
cd webapp
start http://localhost:8000
python -m http.server 8000
