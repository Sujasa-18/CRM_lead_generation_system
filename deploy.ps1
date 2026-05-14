[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
# ==============================================================================
#  AI-Powered Lead Generation CRM System
#  Zero-Touch Deployment Script
#  Compatible with: On-Premises Servers | Cloud VMs (AWS EC2, Azure VM, GCP CE)
#  Usage: .\deploy.ps1
#         .\deploy.ps1 -Mode cloud
# ==============================================================================

param (
    [string]$Mode = "local"   # "local" for on-prem/laptop | "cloud" for remote VM
)

# ── Colour helpers ─────────────────────────────────────────────────────────────
function Write-Header  { param($msg)
    Write-Host "`n=======================================" -ForegroundColor Cyan
    Write-Host "  $msg"                                   -ForegroundColor Cyan
    Write-Host "======================================="  -ForegroundColor Cyan }
function Write-Step    { param($msg) Write-Host "[....] $msg" -ForegroundColor Yellow }
function Write-Success { param($msg) Write-Host "[ OK ] $msg" -ForegroundColor Green  }
function Write-Fail    { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red    }
function Write-Info    { param($msg) Write-Host "[INFO] $msg" -ForegroundColor White  }

# ── Banner ─────────────────────────────────────────────────────────────────────
# ── Banner ─────────────────────────────────────────────────────────────────────
Clear-Host
Write-Host "  ============================================" -ForegroundColor Cyan
Write-Host "                                              " -ForegroundColor Cyan
Write-Host "      AI-Powered Lead Generation CRM          " -ForegroundColor Cyan
Write-Host "         Zero-Touch Deployment                " -ForegroundColor Cyan
Write-Host "         Mode: $Mode                          " -ForegroundColor Cyan
Write-Host "                                              " -ForegroundColor Cyan
Write-Host "  ============================================" -ForegroundColor Cyan

Start-Sleep -Seconds 1

# ==============================================================================
# STEP 1 - Check Python
# ==============================================================================
Write-Header "Step 1 of 6 - Python Check"
Write-Step "Looking for Python 3.8+ ..."

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.([89]|1\d)") {
            $pythonCmd = $cmd
            Write-Success "Found: $ver"
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Fail "Python 3.8 or higher was not found on this machine."
    Write-Info  "Download it from: https://www.python.org/downloads/"
    Write-Info  "Make sure to check 'Add Python to PATH' during installation."
    Read-Host   "Press Enter to exit"
    exit 1
}

# ==============================================================================
# STEP 2 - Virtual Environment
# ==============================================================================
Write-Header "Step 2 of 6 - Virtual Environment"

$venvPath = ".\venv"

if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    Write-Success "Existing venv found - reusing it."
} else {
    Write-Step "Creating virtual environment ..."
    & $pythonCmd -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Failed to create virtual environment."
        Read-Host  "Press Enter to exit"
        exit 1
    }
    Write-Success "Virtual environment created."
}

Write-Step "Activating virtual environment ..."
& "$venvPath\Scripts\Activate.ps1"
Write-Success "Virtual environment activated."

# ==============================================================================
# STEP 3 - Install Dependencies
# ==============================================================================
Write-Header "Step 3 of 6 - Installing Dependencies"

if (-not (Test-Path ".\requirements.txt")) {
    Write-Fail "requirements.txt not found. Please include it in the project folder."
    Read-Host  "Press Enter to exit"
    exit 1
}

Write-Step "Installing packages from requirements.txt ..."
Write-Info  "This may take a few minutes on first run ..."
pip install -r .\requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Fail "Package installation failed."
    Write-Info  "Check your internet connection or review requirements.txt."
    Read-Host   "Press Enter to exit"
    exit 1
}
Write-Success "All packages installed successfully."

# ==============================================================================
# STEP 4 - Environment Configuration (.env)
# ==============================================================================
Write-Header "Step 4 of 6 - Environment Configuration"

if (Test-Path ".\.env") {
    Write-Success "Existing .env file found - using it."
} else {
    Write-Step "No .env file found. Let's create one now."
    Write-Info  "Please enter your configuration details:"

    $dbHost = Read-Host "MySQL Host       (press Enter for 'localhost')"
    if ($dbHost -eq "") { $dbHost = "localhost" }

    $dbPort = Read-Host "MySQL Port       (press Enter for '3306')"
    if ($dbPort -eq "") { $dbPort = "3306" }

    $dbName = Read-Host "Database Name    (press Enter for 'crm_leads')"
    if ($dbName -eq "") { $dbName = "crm_leads" }

    $dbUser = Read-Host "MySQL Username   (press Enter for 'root')"
    if ($dbUser -eq "") { $dbUser = "root" }

    $securePass = Read-Host "MySQL Password" -AsSecureString
    $dbPass     = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                      [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePass))

    $secureGroq = Read-Host "Groq API Key" -AsSecureString
    $groqKey    = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                      [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureGroq))

    $secretKey  = [System.Guid]::NewGuid().ToString("N")

@"
# Auto-generated by deploy.ps1
SECRET_KEY=$secretKey
CRM_PASSWORD=$dbPass

DB_HOST=$dbHost
DB_PORT=$dbPort
DB_NAME=$dbName
DB_USER=$dbUser
DB_PASSWORD=$dbPass

GROQ_API_KEY=$groqKey
"@ | Out-File -FilePath ".\.env" -Encoding utf8

    Write-Success ".env file created."
}

# ==============================================================================
# STEP 5 - Database Initialisation
# ==============================================================================
Write-Header "Step 5 of 6 - Database Initialisation"

# Load .env values into current PowerShell session
foreach ($line in Get-Content ".\.env") {
    if ($line -match "^\s*#" -or $line.Trim() -eq "") { continue }
    if ($line -match "^(.*?)=(.*)$") {
        [System.Environment]::SetEnvironmentVariable($Matches[1].Trim(), $Matches[2].Trim())
    }
}

$dbHost = [System.Environment]::GetEnvironmentVariable("DB_HOST")
$dbPort = [System.Environment]::GetEnvironmentVariable("DB_PORT")
$dbName = [System.Environment]::GetEnvironmentVariable("DB_NAME")
$dbUser = [System.Environment]::GetEnvironmentVariable("DB_USER")
$dbPass = [System.Environment]::GetEnvironmentVariable("DB_PASSWORD")

if (-not $dbHost) { $dbHost = "localhost" }
if (-not $dbPort) { $dbPort = "3306"      }
if (-not $dbName) { $dbName = "crm_leads" }
if (-not $dbUser) { $dbUser = "root"      }

# Locate mysql.exe automatically
$mysqlExe = "mysql"
$mysqlPaths = @(
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
    "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe",
    "C:\xampp\mysql\bin\mysql.exe"
)
foreach ($path in $mysqlPaths) {
    if (Test-Path $path) { $mysqlExe = $path; break }
}

Write-Step "Verifying database connection to '$dbName' ..."

$checkDb = & "$mysqlExe" -u $dbUser "-p$dbPass" -h $dbHost -P $dbPort `
               -e "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$dbName';" 2>&1

if ($checkDb -match $dbName) {
    Write-Success "Database '$dbName' already exists - skipping schema import."
} else {
    Write-Step "Database '$dbName' not found - creating and importing schema ..."

    if (-not (Test-Path ".\schema.sql")) {
        Write-Fail "schema.sql not found. Please include it in the project folder."
        Read-Host  "Press Enter to exit"
        exit 1
    }

    # Create database
    & "$mysqlExe" -u $dbUser "-p$dbPass" -h $dbHost -P $dbPort `
        -e "CREATE DATABASE IF NOT EXISTS ``$dbName``;" 2>&1 | Out-Null

    # Import schema
    Get-Content ".\schema.sql" | & "$mysqlExe" -u $dbUser "-p$dbPass" -h $dbHost -P $dbPort $dbName 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database created and schema imported successfully."
    } else {
        Write-Fail "Schema import failed. Check schema.sql and your DB credentials in .env."
        Read-Host  "Press Enter to exit"
        exit 1
    }
}

# ==============================================================================
# STEP 6 - Verify ML Model Files
# ==============================================================================
Write-Header "Step 6 of 6 - Verifying ML Models"

$modelFiles = @(
    "churn_model.pkl",
    "churn_scaler.pkl",
    "lead_scoring_model.pkl",
    "lead_scoring_features.pkl",
    "scaler.pkl"
)

$missingModels = @()
foreach ($model in $modelFiles) {
    if (Test-Path ".\$model") {
        Write-Success "$model found."
    } else {
        Write-Fail   "$model is MISSING."
        $missingModels += $model
    }
}

if ($missingModels.Count -gt 0) {
    Write-Info "Some model files are missing. Attempting to train them now ..."
    foreach ($script in @("lead_scoring.py", "churn_model.py", "ml_model.py")) {
        if (Test-Path ".\$script") {
            Write-Step "Running $script ..."
            & $pythonCmd ".\$script"
            if ($LASTEXITCODE -eq 0) {
                Write-Success "$script completed."
            } else {
                Write-Fail "$script failed. Check the script for errors."
            }
        }
    }
}

# ==============================================================================
# LAUNCH - Start Flask Application
# ==============================================================================
Write-Header "Launching CRM Application"

if ($Mode -eq "cloud") {
    $env:FLASK_RUN_HOST = "0.0.0.0"
    Write-Info "Cloud mode - app will be accessible on this server's public IP."
    Write-Info "Make sure port 5000 is open in your firewall / security group."
} else {
    $env:FLASK_RUN_HOST = "127.0.0.1"
}

$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "production"

Write-Host ""
Write-Host "  ================================================" -ForegroundColor Green
Write-Host "   CRM System is starting ..."                       -ForegroundColor Green
Write-Host "   URL  : http://localhost:5000"                     -ForegroundColor Green
Write-Host "   Stop : Press Ctrl+C"                              -ForegroundColor Green
Write-Host "  ================================================" -ForegroundColor Green
Write-Host ""

# Auto-open browser in local mode after a short delay
if ($Mode -eq "local") {
    Start-Job -ScriptBlock {
        Start-Sleep -Seconds 3
        Start-Process "http://localhost:5000"
    } | Out-Null
}

# Start Flask
& $pythonCmd -m flask run --host=$env:FLASK_RUN_HOST --port=5000