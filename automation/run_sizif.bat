@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\Антон\Desktop\BOGI AI"
python automation\imagefx_runner.py content\сизиф\prompts\images.md --from 13
pause
