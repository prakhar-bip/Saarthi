#!/bin/bash
# ============================================================
# Sarthi - Google Cloud Run Deployment Script (Production Ready)
# Prerequisites: gcloud CLI installed and authenticated
# ============================================================

set -e

PROJECT_ID="project-e3e4dcb5-593d-4e61-9a8"
REGION="us-central1"
REPO_NAME="sarthi-repo"
BACKEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/sarthi-backend"
FRONTEND_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/sarthi"

echo "=== Setting active Google Cloud Project to $PROJECT_ID ==="
gcloud config set project $PROJECT_ID

# Load local .env file if it exists to retrieve API keys and configuration
if [ -f backend/.env ]; then
  echo "=== Loading environment variables from backend/.env ==="
  # Export non-comment lines
  export $(grep -v '^#' backend/.env | xargs)
fi

# Set default values if not already present in environment
MONGODB_URI="${MONGODB_URI:-mongodb://localhost:27017}"
DATABASE_NAME="${DATABASE_NAME:-sarthi}"
JWT_SECRET="${JWT_SECRET:-sarthi-jwt-super-secret-key-2026}"
JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}"
USE_VERTEX_AI="${USE_VERTEX_AI:-True}"
GOOGLE_MODEL="${GOOGLE_MODEL:-gemini-3.1-pro}"
GOOGLE_FAST_MODEL="${GOOGLE_FAST_MODEL:-gemini-2.5-flash}"
GOOGLE_REASONING_MODEL="${GOOGLE_REASONING_MODEL:-gemini-3.1-pro}"
GOOGLE_API_KEY="${GOOGLE_API_KEY:-}"
NVIDIA_API_KEY="${NVIDIA_API_KEY:-}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
GROQ_API_KEY="${GROQ_API_KEY:-}"

# Create temp env.yaml for initial deploy
cat <<EOF > backend/env.yaml
MONGODB_URI: "$MONGODB_URI"
DATABASE_NAME: "$DATABASE_NAME"
JWT_SECRET: "$JWT_SECRET"
JWT_ALGORITHM: "$JWT_ALGORITHM"
GOOGLE_MODEL: "$GOOGLE_MODEL"
GOOGLE_FAST_MODEL: "$GOOGLE_FAST_MODEL"
GOOGLE_REASONING_MODEL: "$GOOGLE_REASONING_MODEL"
GOOGLE_API_KEY: "$GOOGLE_API_KEY"
NVIDIA_API_KEY: "$NVIDIA_API_KEY"
OPENROUTER_API_KEY: "$OPENROUTER_API_KEY"
GROQ_API_KEY: "$GROQ_API_KEY"
GCP_PROJECT_ID: "$PROJECT_ID"
GCP_LOCATION: "$REGION"
USE_VERTEX_AI: "$USE_VERTEX_AI"
CORS_ORIGINS: '["*"]'
EOF

echo "=== Building and deploying Sarthi Backend ==="
cd backend
gcloud builds submit --tag $BACKEND_IMAGE
gcloud run deploy sarthi-backend \
  --image $BACKEND_IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --env-vars-file env.yaml \
  --memory 1Gi \
  --timeout 300
cd ..

BACKEND_URL=$(gcloud run services describe sarthi-backend --region $REGION --format 'value(status.url)')
echo "Backend deployed at: $BACKEND_URL"

echo "=== Building and deploying Sarthi Frontend (named sarthi) ==="
cd frontend
gcloud builds submit --config=cloudbuild.yaml --substitutions=_NEXT_PUBLIC_API_URL=$BACKEND_URL
gcloud run deploy sarthi \
  --image $FRONTEND_IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL" \
  --memory 512Mi
cd ..

FRONTEND_URL=$(gcloud run services describe sarthi --region $REGION --format 'value(status.url)')
echo "Frontend deployed at: $FRONTEND_URL"

echo "=== Rebuilding secure env.yaml for backend ==="
cat <<EOF > backend/env.yaml
MONGODB_URI: "$MONGODB_URI"
DATABASE_NAME: "$DATABASE_NAME"
JWT_SECRET: "$JWT_SECRET"
JWT_ALGORITHM: "$JWT_ALGORITHM"
GOOGLE_MODEL: "$GOOGLE_MODEL"
GOOGLE_FAST_MODEL: "$GOOGLE_FAST_MODEL"
GOOGLE_REASONING_MODEL: "$GOOGLE_REASONING_MODEL"
GOOGLE_API_KEY: "$GOOGLE_API_KEY"
NVIDIA_API_KEY: "$NVIDIA_API_KEY"
OPENROUTER_API_KEY: "$OPENROUTER_API_KEY"
GROQ_API_KEY: "$GROQ_API_KEY"
GCP_PROJECT_ID: "$PROJECT_ID"
GCP_LOCATION: "$REGION"
USE_VERTEX_AI: "$USE_VERTEX_AI"
CORS_ORIGINS: '["$FRONTEND_URL","http://localhost:3000","http://127.0.0.1:3000"]'
EOF

echo "=== Updating CORS_ORIGINS on backend with secure Frontend URL ==="
gcloud run services update sarthi-backend \
  --region $REGION \
  --env-vars-file backend/env.yaml

# Clean up
rm -f backend/env.yaml

echo "=== Deployment Complete ==="
echo "Backend: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
