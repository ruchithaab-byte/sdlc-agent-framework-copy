# Vertex AI Setup Guide

This document explains how the project is configured to use **Google Cloud Vertex AI** as the primary API provider for the Claude Agent SDK.

## Overview

The Claude Agent SDK supports multiple authentication backends:
- **Anthropic API** (default) - Direct API access using `ANTHROPIC_API_KEY`
- **Vertex AI** - Google Cloud's managed Claude API using service account credentials
- **Amazon Bedrock** - AWS managed Claude API

This project is configured to use **Vertex AI** as the primary provider.

## Configuration

### Environment Variables

The following environment variables are configured in `.env`:

```bash
# Enable Vertex AI as primary backend
CLAUDE_CODE_USE_VERTEX=1

# Google Cloud Project ID
ANTHROPIC_VERTEX_PROJECT_ID=agents-with-claude

# Vertex AI Region
CLOUD_ML_REGION=us-central1

# Service Account Credentials Path
GOOGLE_APPLICATION_CREDENTIALS=/Users/Girish/Projects/agentic-coding-framework/agents-with-claude-e9365ec40584.json
```

### How It Works

When `CLAUDE_CODE_USE_VERTEX=1` is set, the Claude Agent SDK automatically:
1. Detects the environment variable
2. Uses Google Cloud Application Default Credentials (ADC)
3. Routes all API calls through Vertex AI endpoints
4. Authenticates using the service account specified in `GOOGLE_APPLICATION_CREDENTIALS`

**No code changes are required** - the SDK handles the routing automatically based on environment variables.

## Prerequisites

### 1. Enable Vertex AI API

Enable the Vertex AI API in your GCP project:

```bash
gcloud services enable aiplatform.googleapis.com --project=agents-with-claude
```

Or via the [Google Cloud Console](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project=agents-with-claude)

### 2. Service Account Permissions

Ensure your service account has the necessary permissions:

```bash
# Grant Vertex AI User role
gcloud projects add-iam-policy-binding agents-with-claude \
  --member="serviceAccount:girish-ai@agents-with-claude.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### 3. Billing

Ensure billing is enabled for your GCP project. Vertex AI requires a billing account.

## Verification

Run the test script to verify your configuration:

```bash
cd sdlc-agent-framework
python3 scripts/test_vertex_ai_config.py
```

Expected output:
- ✓ Vertex AI is enabled
- ✓ Project ID configured
- ✓ Credentials file found and valid
- ✓ Service account authenticated

## Testing with an Agent

Test that Vertex AI is working by running a simple agent query:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    cwd="./",
    setting_sources=["user", "project"],
)

async def test():
    async for chunk in query("Hello, can you confirm you're using Vertex AI?", options=options):
        print(chunk, end="")

# Run the test
import asyncio
asyncio.run(test())
```

## Switching Between Providers

### Use Vertex AI (Current Setup)
```bash
CLAUDE_CODE_USE_VERTEX=1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
ANTHROPIC_VERTEX_PROJECT_ID=agents-with-claude
```

### Use Anthropic API Directly
```bash
CLAUDE_CODE_USE_VERTEX=0  # or remove the variable
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Use Amazon Bedrock
```bash
CLAUDE_CODE_USE_BEDROCK=1
# Configure AWS credentials
```

## Troubleshooting

### Error: "Vertex AI API not enabled"
**Solution**: Enable the API in Google Cloud Console or via gcloud CLI

### Error: "Permission denied"
**Solution**: Grant the service account the `roles/aiplatform.user` role

### Error: "Billing not enabled"
**Solution**: Enable billing for your GCP project

### SDK still using Anthropic API
**Check**:
1. `CLAUDE_CODE_USE_VERTEX=1` is set in `.env`
2. `.env` file is loaded (check with `python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('CLAUDE_CODE_USE_VERTEX'))"`)
3. No `ANTHROPIC_API_KEY` is set (it takes precedence)

## Model Compatibility

When using Vertex AI, the SDK uses Claude models available through Vertex AI. Model names remain the same:
- `claude-sonnet-4-5-20250929`
- `claude-sonnet-4-20250514`
- etc.

The SDK automatically maps these to Vertex AI endpoints.

## Cost Considerations

- Vertex AI pricing may differ from direct Anthropic API pricing
- Check [Vertex AI pricing](https://cloud.google.com/vertex-ai/pricing) for current rates
- Monitor usage in [Google Cloud Console](https://console.cloud.google.com/billing?project=agents-with-claude)

## Additional Resources

- [Claude Agent SDK Documentation](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Google Cloud Authentication](https://cloud.google.com/docs/authentication)

