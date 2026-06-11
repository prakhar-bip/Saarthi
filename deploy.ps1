# Sarthi - Google Cloud Run Deployment Script (PowerShell for Windows)
# ===================================================================

$ErrorActionPreference = "Stop"

function Check-LastExit {
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error: Last command failed with exit code $LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

$PROJECT_ID = "project-e3e4dcb5-593d-4e61-9a8"
$REGION = "us-central1"
$REPO_NAME = "sarthi-repo"
$BACKEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/sarthi-backend"
$FRONTEND_IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/sarthi"

Write-Host "=== Setting active Google Cloud Project to $PROJECT_ID ==="
gcloud config set project $PROJECT_ID
Check-LastExit

# Load backend/.env if it exists
if (Test-Path "backend\.env") {
    Write-Host "=== Loading environment variables from backend\.env ==="
    Get-Content "backend\.env" | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $key, $value = $line.Split("=", 2)
            $value = $value.Trim("`"").Trim("'")
            [System.Environment]::SetEnvironmentVariable($key.Trim(), $value, "Process")
        }
    }
}

# Get Env values or use defaults
$MONGODB_URI = [System.Environment]::GetEnvironmentVariable("MONGODB_URI")
if (-not $MONGODB_URI) { $MONGODB_URI = "mongodb://localhost:27017" }

$DATABASE_NAME = [System.Environment]::GetEnvironmentVariable("DATABASE_NAME")
if (-not $DATABASE_NAME) { $DATABASE_NAME = "sarthi" }

$JWT_SECRET = [System.Environment]::GetEnvironmentVariable("JWT_SECRET")
if (-not $JWT_SECRET) { $JWT_SECRET = "sarthi-jwt-super-secret-key-2026" }

$JWT_ALGORITHM = [System.Environment]::GetEnvironmentVariable("JWT_ALGORITHM")
if (-not $JWT_ALGORITHM) { $JWT_ALGORITHM = "HS256" }

$USE_VERTEX_AI = [System.Environment]::GetEnvironmentVariable("USE_VERTEX_AI")
if (-not $USE_VERTEX_AI) { $USE_VERTEX_AI = "True" }
$GOOGLE_MODEL = [System.Environment]::GetEnvironmentVariable("GOOGLE_MODEL")
if (-not $GOOGLE_MODEL) { $GOOGLE_MODEL = "gemini-3.1-pro-preview" }
$GOOGLE_FAST_MODEL = [System.Environment]::GetEnvironmentVariable("GOOGLE_FAST_MODEL")
if (-not $GOOGLE_FAST_MODEL) { $GOOGLE_FAST_MODEL = "gemini-3.5-flash" }
$GOOGLE_REASONING_MODEL = [System.Environment]::GetEnvironmentVariable("GOOGLE_REASONING_MODEL")
if (-not $GOOGLE_REASONING_MODEL) { $GOOGLE_REASONING_MODEL = "gemini-3.1-pro-preview" }

$NVIDIA_API_KEY = [System.Environment]::GetEnvironmentVariable("NVIDIA_API_KEY")
$OPENROUTER_API_KEY = [System.Environment]::GetEnvironmentVariable("OPENROUTER_API_KEY")
$GROQ_API_KEY = [System.Environment]::GetEnvironmentVariable("GROQ_API_KEY")
$GOOGLE_API_KEY = [System.Environment]::GetEnvironmentVariable("GOOGLE_API_KEY")

# Create initial env.yaml for backend
$env_yaml = @"
MONGODB_URI: "$MONGODB_URI"
DATABASE_NAME: "$DATABASE_NAME"
JWT_SECRET: "$JWT_SECRET"
JWT_ALGORITHM: "$JWT_ALGORITHM"
GOOGLE_MODEL: "$GOOGLE_MODEL"
GOOGLE_FAST_MODEL: "$GOOGLE_FAST_MODEL"
GOOGLE_REASONING_MODEL: "$GOOGLE_REASONING_MODEL"
NVIDIA_API_KEY: "$NVIDIA_API_KEY"
OPENROUTER_API_KEY: "$OPENROUTER_API_KEY"
GROQ_API_KEY: "$GROQ_API_KEY"
GOOGLE_API_KEY: "$GOOGLE_API_KEY"
GCP_PROJECT_ID: "$PROJECT_ID"
GCP_LOCATION: "$REGION"
USE_VERTEX_AI: "$USE_VERTEX_AI"
CORS_ORIGINS: '["*"]'
"@
$env_yaml | Out-File -FilePath "backend/env.yaml" -Encoding utf8 -Force

Write-Host "=== Building and deploying Sarthi Backend ==="
Push-Location backend
try {
    gcloud builds submit --tag $BACKEND_IMAGE
    Check-LastExit
}
finally {
    Pop-Location
}

gcloud run deploy sarthi-backend `
  --image $BACKEND_IMAGE `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --env-vars-file "backend/env.yaml" `
  --memory 1Gi `
  --timeout 300
Check-LastExit

$BACKEND_URL = (gcloud run services describe sarthi-backend --region $REGION --format 'value(status.url)').Trim()
Check-LastExit
Write-Host "Backend deployed at: $BACKEND_URL"

Write-Host "=== Building and deploying Sarthi Frontend (named sarthi) ==="
Push-Location frontend
try {
    gcloud builds submit --config=cloudbuild.yaml --substitutions="_NEXT_PUBLIC_API_URL=$BACKEND_URL"
    Check-LastExit
}
finally {
    Pop-Location
}

gcloud run deploy sarthi `
  --image $FRONTEND_IMAGE `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL" `
  --memory 512Mi
Check-LastExit

$FRONTEND_URL = (gcloud run services describe sarthi --region $REGION --format 'value(status.url)').Trim()
Check-LastExit
Write-Host "Frontend deployed at: $FRONTEND_URL"

Write-Host "=== Rebuilding secure env.yaml for backend ==="
$env_yaml_secure = @"
MONGODB_URI: "$MONGODB_URI"
DATABASE_NAME: "$DATABASE_NAME"
JWT_SECRET: "$JWT_SECRET"
JWT_ALGORITHM: "$JWT_ALGORITHM"
GOOGLE_MODEL: "$GOOGLE_MODEL"
GOOGLE_FAST_MODEL: "$GOOGLE_FAST_MODEL"
GOOGLE_REASONING_MODEL: "$GOOGLE_REASONING_MODEL"
NVIDIA_API_KEY: "$NVIDIA_API_KEY"
OPENROUTER_API_KEY: "$OPENROUTER_API_KEY"
GROQ_API_KEY: "$GROQ_API_KEY"
GOOGLE_API_KEY: "$GOOGLE_API_KEY"
GCP_PROJECT_ID: "$PROJECT_ID"
GCP_LOCATION: "$REGION"
USE_VERTEX_AI: "$USE_VERTEX_AI"
CORS_ORIGINS: '["$FRONTEND_URL","http://localhost:3000","http://127.0.0.1:3000"]'
"@
$env_yaml_secure | Out-File -FilePath "backend/env.yaml" -Encoding utf8 -Force

Write-Host "=== Updating CORS_ORIGINS on backend with secure Frontend URL ==="
gcloud run services update sarthi-backend `
  --region $REGION `
  --env-vars-file "backend/env.yaml"
Check-LastExit

# Clean up temp env.yaml
if (Test-Path "backend/env.yaml") {
    Remove-Item "backend/env.yaml" -Force
}

Write-Host "=== Deployment Complete ==="
Write-Host "Backend URL: $BACKEND_URL"
Write-Host "Frontend URL: $FRONTEND_URL"
