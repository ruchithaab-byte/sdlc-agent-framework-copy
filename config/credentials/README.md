# Google Cloud Service Account Setup

## Your Service Account Key

Your Google Cloud service account key has been saved to:
```
config/credentials/google-service-account.json
```

## Project Details
- **Project ID:** `agents-with-claude`
- **Service Account Email:** `ruchitha-vertexai@agents-with-claude.iam.gserviceaccount.com`
- **Client ID:** `111100179379796576700`

## Usage in Code

The framework automatically detects your credentials in one of two ways:

### Option 1: Default Location (Already Set Up)
The framework will automatically use:
```
config/credentials/google-service-account.json
```

### Option 2: Environment Variable
Set `GOOGLE_APPLICATION_CREDENTIALS` in your `.env` file:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
```

## Using in Python Code

```python
from config.agent_config import get_google_cloud_credentials_path
from google.oauth2 import service_account
import google.auth

# Get the credentials path
creds_path = get_google_cloud_credentials_path()
if creds_path:
    credentials, project = google.auth.load_credentials_from_file(
        str(creds_path)
    )
    # Use credentials for Google Cloud API calls
```

## Security Notes

⚠️ **Important:**
- The `google-service-account.json` file is in `.gitignore` and will NOT be committed to git
- Never share your private key publicly
- Rotate keys if they are ever exposed
- Use least-privilege IAM roles for the service account

## Next Steps

To use Google Cloud services (e.g., Vertex AI, Cloud Storage, etc.), install the SDK:
```bash
pip install google-cloud-aiplatform google-auth
```

Then use the credentials path from `get_google_cloud_credentials_path()` to authenticate.

## Vertex AI Configuration for Claude Agent SDK

The framework is configured to use **Vertex AI as the primary API provider** for the Claude Agent SDK.

### Environment Variables

The following environment variables are set in `.env`:

```bash
# Enable Vertex AI as primary backend
CLAUDE_CODE_USE_VERTEX=1

# GCP Project ID
ANTHROPIC_VERTEX_PROJECT_ID=agents-with-claude

# Vertex AI Region
CLOUD_ML_REGION=us-central1

# Service Account Credentials
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Prerequisites

1. **Enable Vertex AI API** in your GCP project:
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=agents-with-claude
   ```
   
   Or via the [Google Cloud Console](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=agents-with-claude)

2. **Service Account Permissions**: Ensure your service account has the `Vertex AI User` role:
   ```bash
   gcloud projects add-iam-policy-binding agents-with-claude \
     --member="serviceAccount:girish-ai@agents-with-claude.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

3. **Billing**: Ensure billing is enabled for your GCP project.

### How It Works

When `CLAUDE_CODE_USE_VERTEX=1` is set, the Claude Agent SDK automatically:
- Uses Vertex AI endpoints instead of Anthropic's direct API
- Authenticates using Google Cloud credentials (service account)
- Routes all agent requests through Vertex AI

### Verification

Test your Vertex AI configuration:
```bash
cd sdlc-agent-framework
python3 -c "from config.agent_config import get_google_cloud_credentials_path; print('✓ Credentials:', get_google_cloud_credentials_path())"
```

### Switching Back to Anthropic API

To use Anthropic's direct API instead:
1. Set `ANTHROPIC_API_KEY` in `.env` with your Anthropic API key
2. Remove or set `CLAUDE_CODE_USE_VERTEX=0`
3. The SDK will automatically use Anthropic's API
