#!/usr/bin/env python3
"""
Setup Vertex AI API and Service Account Permissions using GCP CLI.

This script enables the Vertex AI API and grants necessary permissions
to the service account for using Vertex AI with Claude Agent SDK.

Prerequisites:
- You must be authenticated with a user account that has Owner/Editor role
- Run: gcloud auth login (if not already authenticated)
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ID = "agents-with-claude"
SERVICE_ACCOUNT_EMAIL = "ruchitha-vertexai@agents-with-claude.iam.gserviceaccount.com"

# Required APIs to enable
REQUIRED_APIS = [
    "cloudresourcemanager.googleapis.com",
    "aiplatform.googleapis.com",
    "serviceusage.googleapis.com",
]

# Required IAM roles for the service account
REQUIRED_ROLES = [
    "roles/aiplatform.user",           # Access Vertex AI
    "roles/iam.serviceAccountUser",   # Use service accounts
    "roles/storage.objectViewer",      # Access model artifacts
]


def run_command(cmd, check=True, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result.stdout.strip() if capture_output else None
    except subprocess.CalledProcessError as e:
        if check:
            print(f"   ✗ Error: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            return None
        return None


def check_authentication():
    """Check if user is authenticated."""
    print("1. Checking authentication...")
    account = run_command("gcloud config get-value account", check=False)
    if not account:
        print("   ✗ Not authenticated. Please run: gcloud auth login")
        return False
    print(f"   ✓ Authenticated as: {account}")
    return True


def set_project():
    """Set the active project."""
    print("2. Setting active project...")
    run_command(f"gcloud config set project {PROJECT_ID}")
    print(f"   ✓ Project set to: {PROJECT_ID}")


def enable_apis():
    """Enable required APIs."""
    print("3. Enabling required APIs...")
    for api in REQUIRED_APIS:
        api_name = api.split(".")[0].replace("-", " ").title()
        print(f"   - Enabling {api_name} API...")
        result = run_command(
            f"gcloud services enable {api} --project={PROJECT_ID}",
            check=False
        )
        if result is not None:
            print(f"     ✓ {api_name} API enabled")
        else:
            print(f"     ⚠ {api_name} API may already be enabled or error occurred")
    
    print("   Waiting for APIs to propagate (10 seconds)...")
    time.sleep(10)
    print("   ✓ APIs should be ready")


def grant_iam_roles():
    """Grant IAM roles to service account."""
    print("4. Granting IAM roles to service account...")
    
    for role in REQUIRED_ROLES:
        role_name = role.split("/")[-1]
        print(f"   - Granting {role_name} role...")
        cmd = (
            f"gcloud projects add-iam-policy-binding {PROJECT_ID} "
            f"--member='serviceAccount:{SERVICE_ACCOUNT_EMAIL}' "
            f"--role='{role}' "
            f"--condition=None"
        )
        result = run_command(cmd, check=False)
        if result is not None:
            print(f"     ✓ {role_name} role granted")
        else:
            print(f"     ⚠ {role_name} role may already be granted or error occurred")


def verify_service_account():
    """Verify service account exists."""
    print("5. Verifying service account...")
    result = run_command(
        f"gcloud iam service-accounts describe {SERVICE_ACCOUNT_EMAIL} --project={PROJECT_ID}",
        check=False
    )
    if result:
        print("   ✓ Service account exists")
    else:
        print(f"   ✗ Service account not found: {SERVICE_ACCOUNT_EMAIL}")
        print("   Please verify the service account email is correct")


def list_permissions():
    """List current permissions for service account."""
    print("6. Current IAM bindings for service account:")
    cmd = (
        f"gcloud projects get-iam-policy {PROJECT_ID} "
        f"--flatten='bindings[].members' "
        f"--filter='bindings.members:serviceAccount:{SERVICE_ACCOUNT_EMAIL}' "
        f"--format='table(bindings.role)'"
    )
    result = run_command(cmd, check=False)
    if result:
        print(result)
    else:
        print("   ⚠ Could not list permissions (may need additional permissions)")


def check_api_status():
    """Check if Vertex AI API is enabled."""
    print("7. Checking API status...")
    result = run_command(
        f"gcloud services list --enabled --project={PROJECT_ID} "
        f"--filter='name:aiplatform.googleapis.com' --format='value(name)'",
        check=False
    )
    if result and "aiplatform.googleapis.com" in result:
        print("   ✓ Vertex AI API is enabled")
    else:
        print("   ✗ Vertex AI API is not enabled")
        print(f"   Try enabling manually: gcloud services enable aiplatform.googleapis.com --project={PROJECT_ID}")


def main():
    """Main execution."""
    print("=" * 60)
    print("Vertex AI Setup Script")
    print("=" * 60)
    print()
    print(f"Project ID: {PROJECT_ID}")
    print(f"Service Account: {SERVICE_ACCOUNT_EMAIL}")
    print()
    
    if not check_authentication():
        sys.exit(1)
    
    print()
    set_project()
    print()
    enable_apis()
    print()
    grant_iam_roles()
    print()
    verify_service_account()
    print()
    list_permissions()
    print()
    check_api_status()
    print()
    
    print("=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Verify billing is enabled for the project")
    print("2. Test the configuration:")
    print("   cd sdlc-agent-framework")
    print("   python3 scripts/test_vertex_ai_config.py")
    print()
    print("If you encounter permission errors, ensure:")
    print("- Your user account has Owner or Editor role on the project")
    print("- Billing is enabled for the project")
    print("- APIs have propagated (may take a few minutes)")
    print()


if __name__ == "__main__":
    main()

