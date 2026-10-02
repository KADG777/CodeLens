$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv --without-pip .venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the virtual environment.' }
}
python -m pip --python .venv\Scripts\python.exe install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check network access and pip configuration.' }
Write-Host 'Ready. Run start.cmd or: .\.venv\Scripts\python.exe -m streamlit run app.py'
