@echo off
chcp 65001 >nul
REM Установка зависимостей CosyVoice 3 в венв пользователя.
REM Используем venv (не conda-env в ProgramData) — иначе pip работает без прав.
REM GPU: RTX 4070 Ti → torch+torchaudio с CUDA 12.1.
REM Запускать один раз. Установка занимает 10-20 минут (скачивает ~3 ГБ).

setlocal
set "BASE_PY=C:\ProgramData\anaconda3\envs\cosyvoice\python.exe"
set "VENV=%USERPROFILE%\cosyvoice-venv"
set "VPY=%VENV%\Scripts\python.exe"
set "REPO=%~dp0.."
set "COSYREQ=%REPO%\external\CosyVoice\requirements.txt"
set "MATCHA=%REPO%\external\CosyVoice\third_party\Matcha-TTS"

echo ============================================================
echo CosyVoice setup
echo   venv: %VENV%
echo   requirements: %COSYREQ%
echo ============================================================

if not exist "%VPY%" (
  echo [setup] Создаю venv...
  "%BASE_PY%" -m venv "%VENV%" || goto :err
)

echo.
echo [1/4] Обновляю pip...
"%VPY%" -m pip install --upgrade pip setuptools wheel || goto :err

echo.
echo [2/4] Ставлю torch 2.3.1 + torchaudio 2.3.1 (CUDA 12.1)...
"%VPY%" -m pip install ^
  torch==2.3.1 ^
  torchaudio==2.3.1 ^
  --index-url https://download.pytorch.org/whl/cu121 || goto :err

echo.
echo [3/4] Ставлю зависимости CosyVoice...
"%VPY%" -m pip install -r "%COSYREQ%" || goto :err

echo.
echo [4/4] Ставлю Matcha-TTS как editable пакет...
"%VPY%" -m pip install -e "%MATCHA%" || goto :err

echo.
echo ============================================================
echo [verify] Проверяю импорты...
"%VPY%" -c "import torch, torchaudio, soundfile, librosa, hyperpyyaml, matcha, onnxruntime, transformers, conformer, lightning, diffusers, modelscope; print('OK — CUDA:', torch.cuda.is_available(), 'torch', torch.__version__)" || goto :err

echo.
echo ✅ Установка завершена успешно.
echo    Для запуска webapp с CosyVoice используй webapp\run.bat
endlocal
exit /b 0

:err
echo.
echo ❌ Установка упала. Прокрути вверх и смотри последнюю ошибку pip.
endlocal
exit /b 1
