"""
Vertex AI adapter for agents - alternative to Claude Agent SDK.

This adapter allows using Google Cloud Vertex AI (Gemini) models instead of Anthropic Claude.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import AsyncIterator, Dict, List, Optional, Any

from google.cloud import aiplatform
from google.oauth2 import service_account

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from config.agent_config import get_google_cloud_credentials_path, PROJECT_ROOT


class VertexAIOptions:
    """Configuration options for Vertex AI agents."""

    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        project_id: str = "agents-with-claude",
        location: str = "us-central1",
        credentials_path: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ):
        self.model = model
        self.project_id = project_id
        self.location = location
        self.credentials_path = credentials_path
        self.temperature = temperature
        self.max_tokens = max_tokens


class VertexAIAgent:
    """Vertex AI agent wrapper that mimics Claude Agent SDK interface."""

    def __init__(self, options: VertexAIOptions):
        self.options = options
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize Vertex AI client with service account credentials."""
        creds_path = self.options.credentials_path or get_google_cloud_credentials_path()
        
        if not creds_path:
            raise RuntimeError(
                "Google Cloud credentials not found. "
                "Set GOOGLE_APPLICATION_CREDENTIALS or place credentials at "
                "config/credentials/google-service-account.json"
            )

        credentials = service_account.Credentials.from_service_account_file(
            str(creds_path)
        )

        # Initialize Vertex AI
        aiplatform.init(
            project=self.options.project_id,
            location=self.options.location,
            credentials=credentials,
        )

        # Return credentials dict for use in query method
        # The actual GenerativeModel is initialized in the query method
            return {"credentials": credentials, "project": self.options.project_id}

    async def query(
        self,
        prompt: str,
        *,
        tools: Optional[List[Dict[str, Any]]] = None,
        system_instruction: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Query Vertex AI model and stream responses.
        
        Mimics the Claude Agent SDK query interface.
        Uses Vertex AI's Generative AI API.
        """
        try:
            # Use Vertex AI Generative AI API
            from vertexai.generative_models import GenerativeModel
            import vertexai
            
            # Initialize Vertex AI with project and location
            vertexai.init(
                project=self.options.project_id,
                location=self.options.location,
            )
            
            # Use correct model name format for Vertex AI
            # Try different model name formats
            model_name = self.options.model
            if not model_name.startswith("gemini"):
                model_name = f"gemini-{model_name}" if not model_name.startswith("gemini-") else model_name
            
            # Build the model
            model = GenerativeModel(model_name)
            
            # Build prompt with system instruction if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            
            # Generate content with streaming
            generation_config = {
                "temperature": self.options.temperature,
                "max_output_tokens": self.options.max_tokens,
            }
            
            # Generate and stream response
            response = model.generate_content(
                full_prompt,
                generation_config=generation_config,
                stream=True,
            )
            
            # Stream chunks
            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text
                elif hasattr(chunk, "candidates") and chunk.candidates:
                    for candidate in chunk.candidates:
                        if hasattr(candidate, "content") and candidate.content:
                            if hasattr(candidate.content, "parts"):
                                for part in candidate.content.parts:
                                    if hasattr(part, "text"):
                                        yield part.text
                                        
        except ImportError as e:
            # Fallback: use REST API directly
            yield f"Error: Missing required package. Install: pip install google-cloud-aiplatform\n"
            yield f"Import error: {str(e)}"
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                yield f"Error: Model not found. Possible causes:\n"
                yield f"1. Billing not enabled: https://console.cloud.google.com/billing?project={self.options.project_id}\n"
                yield f"2. Gemini access may require project approval/whitelisting\n"
                yield f"3. Try different region (us-east1, us-west1) instead of {self.options.location}\n"
                yield f"4. Model name: {self.options.model} may not be available\n"
                yield f"5. Check Vertex AI quotas: https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project={self.options.project_id}\n"
                yield f"Original error: {error_msg}\n"
            else:
                yield f"Error: {error_msg}\n"


def create_vertex_ai_options(
    model: str = "gemini-1.5-pro",
    project_id: Optional[str] = None,
    location: str = "us-central1",
) -> VertexAIOptions:
    """
    Create Vertex AI options from configuration.
    
    Args:
        model: Vertex AI model name (e.g., "gemini-1.5-pro", "gemini-1.5-flash")
        project_id: GCP project ID (defaults to credentials project)
        location: GCP region (default: us-central1)
    """
    creds_path = get_google_cloud_credentials_path()
    
    if creds_path:
        # Read project ID from credentials if not provided
        if not project_id:
            import json
            with open(creds_path) as f:
                creds = json.load(f)
                project_id = creds.get("project_id", "agents-with-claude")
    else:
        project_id = project_id or "agents-with-claude"

    return VertexAIOptions(
        model=model,
        project_id=project_id,
        location=location,
        credentials_path=str(creds_path) if creds_path else None,
    )


# Example usage function
async def run_vertex_ai_agent(prompt: str, model: str = "gemini-1.5-pro") -> None:
    """Example function showing how to use Vertex AI agent."""
    options = create_vertex_ai_options(model=model)
    agent = VertexAIAgent(options)
    
    async for chunk in agent.query(prompt):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(run_vertex_ai_agent("Hello, can you help me with software architecture?"))

