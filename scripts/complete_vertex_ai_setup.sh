#!/bin/bash
# Complete Vertex AI Setup Script
# This script completes the setup after gcloud is installed

set -e

export PATH="/opt/homebrew/share/google-cloud-sdk/bin:$PATH"
export CLOUDSDK_PYTHON=$(which python3)

PROJECT_ID="agents-with-claude"
SERVICE_ACCOUNT_EMAIL="ruchitha-vertexai@agents-with-claude.iam.gserviceaccount.com"

echo "============================================================"
echo "Complete Vertex AI Setup"
echo "============================================================"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""

# Check if authenticated
echo "1. Checking authentication..."
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
if [ -z "$CURRENT_ACCOUNT" ]; then
    echo "   ⚠ Not authenticated. Running: gcloud auth login"
    echo "   Please authenticate in the browser that opens..."
    gcloud auth login
else
    echo "   ✓ Authenticated as: $CURRENT_ACCOUNT"
fi
echo ""

# Set project
echo "2. Setting active project..."
gcloud config set project $PROJECT_ID
echo "   ✓ Project set to: $PROJECT_ID"
echo ""

# Enable APIs
echo "3. Enabling required APIs..."
echo "   - Enabling Cloud Resource Manager API..."
gcloud services enable cloudresourcemanager.googleapis.com --project=$PROJECT_ID || echo "     ⚠ May already be enabled"

echo "   - Enabling Vertex AI API..."
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID || echo "     ⚠ May already be enabled"

echo "   - Enabling Service Usage API..."
gcloud services enable serviceusage.googleapis.com --project=$PROJECT_ID || echo "     ⚠ May already be enabled"
echo ""

# Wait for APIs to propagate
echo "4. Waiting for APIs to propagate (15 seconds)..."
sleep 15
echo "   ✓ APIs should be ready"
echo ""

# Grant IAM roles
echo "5. Granting IAM roles to service account..."
echo "   - Granting Vertex AI User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user" || echo "     ⚠ Role may already be granted"

echo "   - Granting Service Account User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountUser" || echo "     ⚠ Role may already be granted"
echo ""

# Verify service account
echo "6. Verifying service account..."
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "   ✓ Service account exists"
else
    echo "   ✗ Service account not found: $SERVICE_ACCOUNT_EMAIL"
    echo "   Please verify the service account email is correct"
fi
echo ""

# Check API status
echo "7. Verifying Vertex AI API is enabled..."
if gcloud services list --enabled --project=$PROJECT_ID --filter="name:aiplatform.googleapis.com" --format="value(name)" 2>/dev/null | grep -q "aiplatform.googleapis.com"; then
    echo "   ✓ Vertex AI API is enabled"
else
    echo "   ✗ Vertex AI API is not enabled"
    echo "   Try: gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID"
fi
echo ""

echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Test the configuration:"
echo "   cd sdlc-agent-framework"
echo "   source venv/bin/activate"
echo "   python3 scripts/test_vertex_ai_config.py"
echo ""
echo "2. Test an agent:"
echo "   python3 main.py agent productspec --requirements 'Test requirement'"
echo ""

