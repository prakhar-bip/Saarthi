#!/bin/bash
# ============================================================
# Sarthi - Google Cloud Run Deployment Script
# Prerequisites: gcloud CLI installed and authenticated
# ============================================================

set -e

PROJECT_ID="project-e3e4dcb5-593d-4e61-9a8"
REGION="us-central1"

echo "=== Building and deploying Sarthi Backend ==="
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/sarthi-backend
gcloud run deploy sarthi-backend \
  --image gcr.io/$PROJECT_ID/sarthi-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "MONGODB_URI=$MONGODB_URI,DATABASE_NAME=sarthi,GOOGLE_API_KEY=$GOOGLE_API_KEY,GCP_PROJECT_ID=$PROJECT_ID,GCP_LOCATION=$REGION,CORS_ORIGINS=*" \
  --memory 1Gi \
  --timeout 300

BACKEND_URL=$(gcloud run services describe sarthi-backend --region $REGION --format 'value(status.url)')
echo "Backend deployed at: $BACKEND_URL"

cd ../frontend
echo "=== Building and deploying Sarthi Frontend ==="
gcloud builds submit --tag gcr.io/$PROJECT_ID/sarthi-frontend --build-arg NEXT_PUBLIC_API_URL=$BACKEND_URL
gcloud run deploy sarthi-frontend \
  --image gcr.io/$PROJECT_ID/sarthi-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL" \
  --memory 512Mi

FRONTEND_URL=$(gcloud run services describe sarthi-frontend --region $REGION --format 'value(status.url)')
echo "Frontend deployed at: $FRONTEND_URL"
echo "=== Deployment Complete ==="
