#!/usr/bin/env python3
"""
Test script to verify Vertex AI configuration for Claude Agent SDK.

This script checks:
1. Environment variables are set correctly
2. Google Cloud credentials are accessible
3. Vertex AI API is enabled (if permissions allow)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from config.agent_config import get_google_cloud_credentials_path

# Load environment variables
load_dotenv(project_root / ".env")


def check_vertex_ai_config():
    """Check Vertex AI configuration.
    
    Returns:
        tuple: (success: bool, results: dict) - Success status and detailed results
    """
    print("=" * 60)
    print("Vertex AI Configuration Test")
    print("=" * 60)
    print()

    results = {
        "env_vars": {},
        "credentials": {},
        "api_status": {},
        "summary": {}
    }

    # Check environment variables
    print("1. Environment Variables:")
    print("-" * 40)
    
    claude_vertex = os.getenv("CLAUDE_CODE_USE_VERTEX")
    vertex_project = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")
    cloud_region = os.getenv("CLOUD_ML_REGION")
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"  CLAUDE_CODE_USE_VERTEX: {claude_vertex or 'NOT SET'}")
    if claude_vertex == "1":
        print("    ✓ Vertex AI is enabled")
        results["env_vars"]["claude_vertex"] = True
    else:
        print("    ✗ Vertex AI is NOT enabled (set CLAUDE_CODE_USE_VERTEX=1)")
        results["env_vars"]["claude_vertex"] = False
    
    print(f"  ANTHROPIC_VERTEX_PROJECT_ID: {vertex_project or 'NOT SET'}")
    if vertex_project:
        print(f"    ✓ Project ID: {vertex_project}")
        results["env_vars"]["vertex_project"] = True
    else:
        results["env_vars"]["vertex_project"] = False
    
    print(f"  CLOUD_ML_REGION: {cloud_region or 'NOT SET (defaults to global)'}")
    if cloud_region:
        print(f"    ✓ Region: {cloud_region}")
    results["env_vars"]["cloud_region"] = cloud_region or "global"
    
    print(f"  GOOGLE_APPLICATION_CREDENTIALS: {google_creds or 'NOT SET'}")
    results["env_vars"]["google_creds"] = bool(google_creds)
    print()

    # Check credentials
    print("2. Google Cloud Credentials:")
    print("-" * 40)
    creds_path = get_google_cloud_credentials_path()
    creds_data = None
    
    if creds_path and creds_path.exists():
        print(f"  ✓ Credentials file found: {creds_path}")
        results["credentials"]["file_found"] = True
        results["credentials"]["file_path"] = str(creds_path)
        
        # Try to read and validate JSON
        try:
            import json
            with open(creds_path) as f:
                creds_data = json.load(f)
                print(f"  ✓ Valid JSON format")
                print(f"  ✓ Project ID: {creds_data.get('project_id', 'N/A')}")
                print(f"  ✓ Service Account: {creds_data.get('client_email', 'N/A')}")
                results["credentials"]["valid_json"] = True
                results["credentials"]["project_id"] = creds_data.get('project_id')
                results["credentials"]["service_account"] = creds_data.get('client_email')
        except Exception as e:
            print(f"  ✗ Error reading credentials: {e}")
            results["credentials"]["valid_json"] = False
            results["credentials"]["error"] = str(e)
    else:
        print("  ✗ Credentials file not found")
        if google_creds:
            print(f"    Expected at: {google_creds}")
        results["credentials"]["file_found"] = False
    print()

    # Check Vertex AI API (if permissions allow)
    print("3. Vertex AI API Status:")
    print("-" * 40)
    api_initialized = False
    try:
        from google.cloud import aiplatform
        from google.oauth2 import service_account
        
        if creds_path and creds_path.exists():
            credentials = service_account.Credentials.from_service_account_file(
                str(creds_path)
            )
            print("  ✓ Successfully loaded credentials")
            print("  ✓ Can initialize Vertex AI client")
            results["api_status"]["credentials_loaded"] = True
            
            # Try to initialize (this will fail if API not enabled, but we can catch it)
            try:
                # Use creds_data if available, otherwise use vertex_project or fallback
                project_id = vertex_project
                if not project_id and creds_data:
                    project_id = creds_data.get('project_id')
                
                aiplatform.init(
                    project=project_id,
                    location=cloud_region or "us-central1",
                    credentials=credentials,
                )
                print("  ✓ Vertex AI initialized successfully")
                api_initialized = True
                results["api_status"]["initialized"] = True
            except Exception as e:
                error_msg = str(e)
                if "PERMISSION_DENIED" in error_msg or "403" in error_msg:
                    print("  ⚠ Vertex AI API may not be enabled or service account lacks permissions")
                    print(f"     Error: {error_msg[:100]}...")
                    print("     Action: Enable Vertex AI API in Google Cloud Console")
                    results["api_status"]["initialized"] = False
                    results["api_status"]["error_type"] = "PERMISSION_DENIED"
                else:
                    print(f"  ⚠ Vertex AI initialization issue: {error_msg[:100]}...")
                    results["api_status"]["initialized"] = False
                    results["api_status"]["error_type"] = "OTHER"
                results["api_status"]["error"] = error_msg[:200]
        else:
            print("  ✗ Cannot test - credentials not found")
            results["api_status"]["credentials_loaded"] = False
    except ImportError:
        print("  ⚠ google-cloud-aiplatform not installed")
        print("     Install with: pip install google-cloud-aiplatform")
        results["api_status"]["error"] = "ImportError: google-cloud-aiplatform not installed"
    except Exception as e:
        print(f"  ⚠ Error checking Vertex AI: {e}")
        results["api_status"]["error"] = str(e)
    print()

    # Summary
    print("=" * 60)
    print("Summary:")
    print("=" * 60)
    
    all_good = (
        claude_vertex == "1"
        and vertex_project
        and creds_path
        and creds_path.exists()
    )
    
    results["summary"]["all_checks_passed"] = all_good
    
    if all_good:
        print("✓ Configuration looks good!")
        print("  Your project is configured to use Vertex AI as the primary API.")
        print("  The Claude Agent SDK will automatically use Vertex AI endpoints.")
    else:
        print("✗ Configuration incomplete:")
        if claude_vertex != "1":
            print("  - Set CLAUDE_CODE_USE_VERTEX=1 in .env")
        if not vertex_project:
            print("  - Set ANTHROPIC_VERTEX_PROJECT_ID in .env")
        if not creds_path or not creds_path.exists():
            print("  - Set GOOGLE_APPLICATION_CREDENTIALS to valid service account file")
    
    print()
    print("Next steps:")
    print("  1. Ensure Vertex AI API is enabled in your GCP project")
    print("  2. Verify service account has 'Vertex AI User' role")
    print("  3. Test with a simple agent query")
    
    return all_good, results


if __name__ == "__main__":
    success, results = check_vertex_ai_config()
    sys.exit(0 if success else 1)

