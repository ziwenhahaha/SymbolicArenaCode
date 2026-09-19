@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

python core50_60_70_80_selector.py ^
  --input "input\postprocess_final_20260501-105508_664+4+3result.zip" ^
  --outdir outputs_reproduced
if errorlevel 1 exit /b 1

echo Completed. Results are in outputs_reproduced\
pause
