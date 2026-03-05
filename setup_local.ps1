# Quick Start Script for Local Testing
# Run this before deploying to Hugging Face Spaces

Write-Host "🚀 Dot Matrix OCR - Local Testing Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example...`n" -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file" -ForegroundColor Green
    Write-Host "❗ Please edit .env and add your OPENROUTER_API_KEY`n" -ForegroundColor Red
    notepad .env
}

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor White
$pythonVersion = python --version 2>&1
Write-Host "✅ $pythonVersion`n" -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor White
    python -m venv venv
    Write-Host "✅ Virtual environment created`n" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor White
. .\venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated`n" -ForegroundColor Green

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor White
pip install -r requirements.txt --quiet
Write-Host "✅ Dependencies installed`n" -ForegroundColor Green

# Create uploads directory
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "✅ Created uploads directory`n" -ForegroundColor Green
}

# Check if static files exist
Write-Host "Verifying project structure..." -ForegroundColor White
$requiredFiles = @("app.py", "index.html", "requirements.txt", "Dockerfile", "README.md", "script.js", "styles.css")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file (MISSING!)" -ForegroundColor Red
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Missing required files! Please ensure all files are present.`n" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "To start the server, run:" -ForegroundColor White
Write-Host "  python app.py`n" -ForegroundColor Yellow

Write-Host "The app will be available at:" -ForegroundColor White
Write-Host "  http://localhost:7860`n" -ForegroundColor Cyan

Write-Host "Before deploying to Hugging Face:" -ForegroundColor White
Write-Host "  1. Test the app locally" -ForegroundColor White
Write-Host "  2. Ensure OPENROUTER_API_KEY is set in .env" -ForegroundColor White
Write-Host "  3. Review DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host "  4. DO NOT commit your .env file!`n" -ForegroundColor Yellow

$startNow = Read-Host "Start the server now? (Y/N)"
if ($startNow -eq "Y" -or $startNow -eq "y") {
    Write-Host "`nStarting server...`n" -ForegroundColor Cyan
    python app.py
}
