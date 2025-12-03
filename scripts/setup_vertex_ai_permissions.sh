#!/bin/bash
#
# Setup Vertex AI API and Service Account Permissions
# 
# This script enables the Vertex AI API and grants necessary permissions
# to the service account for using Vertex AI with Claude Agent SDK.
#
# Prerequisites:
# - You must be authenticated with a user account that has Owner/Editor role
# - Run: gcloud auth login (if not already authenticated)
#

set -e

PROJECT_ID="agents-with-claude"
SERVICE_ACCOUNT_EMAIL="ruchitha-vertexai@agents-with-claude.iam.gserviceaccount.com"

echo "============================================================"
echo "Vertex AI Setup Script"
echo "============================================================"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""

# Check if user is authenticated
echo "1. Checking authentication..."
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
if [ -z "$CURRENT_ACCOUNT" ]; then
    echo "   ✗ Not authenticated. Please run: gcloud auth login"
    exit 1
fi
echo "   ✓ Authenticated as: $CURRENT_ACCOUNT"
echo ""

# Set the project
echo "2. Setting active project..."
gcloud config set project $PROJECT_ID
echo "   ✓ Project set to: $PROJECT_ID"
echo ""

# Enable required APIs
echo "3. Enabling required APIs..."
echo "   - Enabling Cloud Resource Manager API..."
gcloud services enable cloudresourcemanager.googleapis.com --project=$PROJECT_ID || echo "   ⚠ Cloud Resource Manager API may already be enabled"

echo "   - Enabling Vertex AI API..."
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID || echo "   ⚠ Vertex AI API may already be enabled"

echo "   - Enabling Service Usage API..."
gcloud services enable serviceusage.googleapis.com --project=$PROJECT_ID || echo "   ⚠ Service Usage API may already be enabled"
echo ""

# Wait for APIs to propagate
echo "4. Waiting for APIs to propagate (10 seconds)..."
sleep 10
echo "   ✓ APIs should be ready"
echo ""

# Grant IAM roles to service account
echo "5. Granting IAM roles to service account..."

echo "   - Granting Vertex AI User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user" \
    --condition=None || echo "   ⚠ Role may already be granted"

echo "   - Granting Service Account User role..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountUser" \
    --condition=None || echo "   ⚠ Role may already be granted"

echo "   - Granting Storage Object Viewer (for model artifacts)..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.objectViewer" \
    --condition=None || echo "   ⚠ Role may already be granted"
echo ""

# Verify service account exists
echo "6. Verifying service account..."
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "   ✓ Service account exists"
else
    echo "   ✗ Service account not found: $SERVICE_ACCOUNT_EMAIL"
    echo "   Please verify the service account email is correct"
fi
echo ""

# List current permissions
echo "7. Current IAM bindings for service account:"
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --format="table(bindings.role)" 2>/dev/null || echo "   ⚠ Could not list permissions (may need additional permissions)"
echo ""

# Check API status
echo "8. Checking API status..."
if gcloud services list --enabled --project=$PROJECT_ID --filter="name:aiplatform.googleapis.com" --format="value(name)" 2>/dev/null | grep -q "aiplatform.googleapis.com"; then
    echo "   ✓ Vertex AI API is enabled"
else
    echo "   ✗ Vertex AI API is not enabled"
    echo "   Try enabling manually: gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID"
fi
echo ""

echo "============================================================"
echo "Setup Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Verify billing is enabled for the project"
echo "2. Test the configuration:"
echo "   cd sdlc-agent-framework"
echo "   python3 scripts/test_vertex_ai_config.py"
echo ""
echo "If you encounter permission errors, ensure:"
echo "- Your user account has Owner or Editor role on the project"
echo "- Billing is enabled for the project"
echo "- APIs have propagated (may take a few minutes)"
echo ""

