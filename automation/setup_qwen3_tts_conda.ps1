param(
    [string]$CondaRoot = "",
    [string]$EnvName = "qwen3-tts",
    [switch]$InstallEditableRepo,
    [switch]$DownloadModel,
    [switch]$InstallFlashAttn
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$toolsRoot = Join-Path $repoRoot ".tools"
$repoDir = Join-Path $repoRoot "external\Qwen3-TTS"
$modelDir = Join-Path $repoRoot ".models\Qwen3-TTS-12Hz-1.7B-Base"

if ([string]::IsNullOrWhiteSpace($CondaRoot)) {
    $CondaRoot = Join-Path $toolsRoot "miniforge3"
}

$condaExe = Join-Path $CondaRoot "Scripts\conda.exe"

if (-not (Test-Path $condaExe)) {
    throw "conda was not found at $condaExe. Install Miniforge or Miniconda first."
}

Write-Host "Creating conda environment $EnvName with Python 3.12"
& $condaExe create -n $EnvName python=3.12 -y

Write-Host "Installing qwen-tts from PyPI"
& $condaExe run -n $EnvName python -m pip install -U qwen-tts imageio-ffmpeg

if ($InstallEditableRepo) {
    if (-not (Test-Path $repoDir)) {
        throw "Local Qwen3-TTS repository was not found: $repoDir"
    }

    Write-Host "Installing the local Qwen3-TTS repository in editable mode"
    & $condaExe run -n $EnvName python -m pip install -e $repoDir
}

if ($InstallFlashAttn) {
    Write-Host "Installing flash-attn"
    & $condaExe run -n $EnvName python -m pip install -U flash-attn --no-build-isolation
}

if ($DownloadModel) {
    Write-Host "Downloading Qwen3-TTS-12Hz-1.7B-Base"
    & $condaExe run -n $EnvName python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='Qwen/Qwen3-TTS-12Hz-1.7B-Base', local_dir=r'$modelDir', local_dir_use_symlinks=False)"
}

Write-Host ""
Write-Host "Environment check:"
& $condaExe run -n $EnvName python -c "import torch; print('torch', torch.__version__); print('cuda', torch.cuda.is_available())"

Write-Host ""
Write-Host "Run voice clone script:"
Write-Host "  `"$condaExe`" run -n $EnvName python `"$repoRoot\scripts\qwen3_tts_voice_clone.py`""
