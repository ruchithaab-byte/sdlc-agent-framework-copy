# GCP CLI Commands for Vertex AI Setup

This guide provides the exact GCP CLI commands to enable Vertex AI API and grant permissions to your service account.

## Prerequisites

**Important**: You must authenticate with a **user account** (not the service account) that has Owner or Editor role on the project.

### Step 1: Authenticate with Your User Account

```bash
# Authenticate with your user account (not service account)
gcloud auth login

# Verify you're authenticated with the correct account
gcloud config get-value account

# If you need to switch accounts
gcloud auth login --account=your-email@example.com
```

### Step 2: Set the Project

```bash
gcloud config set project agents-with-claude
```

## Enable Vertex AI API

### Enable Required APIs

```bash
# Enable Cloud Resource Manager API (required for IAM operations)
gcloud services enable cloudresourcemanager.googleapis.com --project=agents-with-claude

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=agents-with-claude

# Enable Service Usage API (required for API management)
gcloud services enable serviceusage.googleapis.com --project=agents-with-claude
```

### Verify APIs are Enabled

```bash
# List all enabled APIs
gcloud services list --enabled --project=agents-with-claude

# Check specifically for Vertex AI
gcloud services list --enabled --project=agents-with-claude --filter="name:aiplatform.googleapis.com"
```

## Grant IAM Permissions to Service Account

### Grant Required Roles

```bash
# Service account email
SERVICE_ACCOUNT="girish-ai@agents-with-claude.iam.gserviceaccount.com"
PROJECT_ID="agents-with-claude"

# Grant Vertex AI User role (allows using Vertex AI)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user"

# Grant Service Account User role (allows using service accounts)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/iam.serviceAccountUser"

# Grant Storage Object Viewer role (for accessing model artifacts)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.objectViewer"
```

### Verify Permissions

```bash
# List all IAM bindings for the service account
gcloud projects get-iam-policy agents-with-claude \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:girish-ai@agents-with-claude.iam.gserviceaccount.com" \
    --format="table(bindings.role)"
```

## Using the Setup Scripts

### Option 1: Bash Script

```bash
cd sdlc-agent-framework
./scripts/setup_vertex_ai_permissions.sh
```

### Option 2: Python Script

```bash
cd sdlc-agent-framework
python3 scripts/setup_vertex_ai_permissions.py
```

## Troubleshooting

### Error: "Permission denied"

**Cause**: You're authenticated with the service account instead of a user account.

**Solution**:
```bash
# Logout from service account
gcloud auth revoke girish-ai@agents-with-claude.iam.gserviceaccount.com

# Login with your user account
gcloud auth login

# Verify
gcloud config get-value account
```

### Error: "API not enabled"

**Cause**: The API needs to be enabled by a user with Owner/Editor role.

**Solution**: Use the commands above with a user account that has proper permissions.

### Error: "Service account not found"

**Cause**: The service account email might be incorrect.

**Solution**: List all service accounts:
```bash
gcloud iam service-accounts list --project=agents-with-claude
```

### Check Current Authentication

```bash
# See all authenticated accounts
gcloud auth list

# See which account is active
gcloud config get-value account

# See current project
gcloud config get-value project
```

## Quick One-Liner Setup

If you're authenticated with a user account with Owner/Editor role:

```bash
PROJECT_ID="agents-with-claude"
SA_EMAIL="girish-ai@agents-with-claude.iam.gserviceaccount.com"

# Enable APIs
gcloud services enable cloudresourcemanager.googleapis.com aiplatform.googleapis.com serviceusage.googleapis.com --project=$PROJECT_ID

# Grant roles
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/storage.objectViewer"
```

## Verify Everything Works

After setup, test the configuration:

```bash
cd sdlc-agent-framework
python3 scripts/test_vertex_ai_config.py
```

## Additional Resources

- [GCP IAM Roles](https://cloud.google.com/iam/docs/understanding-roles)
- [Vertex AI Access Control](https://cloud.google.com/vertex-ai/docs/general/access-control)
- [Service Account Permissions](https://cloud.google.com/iam/docs/service-accounts)

