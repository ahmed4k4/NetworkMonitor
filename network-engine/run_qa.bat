@echo off
cd /d e:\NetworkMonitor\network-engine
.venv\Scripts\python qa_test.py > qa_output.txt 2>&1
echo EXIT_CODE=%ERRORLEVEL%