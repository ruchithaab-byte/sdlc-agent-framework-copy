#!/bin/bash
# Activate Google Cloud Service Account
# Usage: ./scripts/activate_service_account.sh /path/to/service-account-key.json

SERVICE_ACCOUNT_EMAIL="ruchitha-vertexai@agents-with-claude.iam.gserviceaccount.com"

if [ -z "$1" ]; then
    echo "Error: Please provide the path to your service account key file"
    echo "Usage: $0 /path/to/service-account-key.json"
    exit 1
fi

KEY_FILE="$1"

if [ ! -f "$KEY_FILE" ]; then
    echo "Error: Key file not found: $KEY_FILE"
    exit 1
fi

echo "Activating service account: $SERVICE_ACCOUNT_EMAIL"
echo "Using key file: $KEY_FILE"
echo ""

gcloud auth activate-service-account "$SERVICE_ACCOUNT_EMAIL" \
    --key-file="$KEY_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Service account activated successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update .env file with the key file path:"
    echo "   GOOGLE_APPLICATION_CREDENTIALS=$KEY_FILE"
    echo ""
    echo "2. Verify activation:"
    echo "   gcloud auth list"
    echo ""
    echo "3. Test Vertex AI configuration:"
    echo "   python3 scripts/test_vertex_ai_config.py"
else
    echo ""
    echo "✗ Failed to activate service account"
    exit 1
fi
