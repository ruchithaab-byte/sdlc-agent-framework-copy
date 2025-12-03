"""Repository Router for multi-repository orchestration.

Uses an LLM (Google Vertex AI Gemini) to analyze user prompts and route them
to the most appropriate repository based on repository descriptions.
"""

from __future__ import annotations

import os
import re
import json
from pathlib import Path
from typing import Optional

import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
from google.cloud import aiplatform

from config.agent_config import PROJECT_ROOT, get_google_cloud_credentials_path
from src.orchestrator.registry import RepoRegistry, RepoConfig


class RoutingError(Exception):
    """Raised when routing fails."""
    pass


class RepoRouter:
    """
    Routes user prompts to the appropriate repository using LLM classification.
    
    Uses Google Vertex AI (Gemini) to analyze user prompts and match them
    against repository descriptions to determine the best target repository.
    """

    DEFAULT_MODEL = "gemini-1.5-pro-001"

    def __init__(
        self,
        registry: RepoRegistry,
        *,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the RepoRouter.
        
        Args:
            registry: The RepoRegistry instance to get repository information from.
            project_id: GCP project ID. Defaults to ANTHROPIC_VERTEX_PROJECT_ID env var.
            location: GCP region. Defaults to CLOUD_ML_REGION env var or "us-central1".
            model: Gemini model to use. Defaults to gemini-1.5-pro-001.
            credentials_path: Path to service account JSON. Defaults to GOOGLE_APPLICATION_CREDENTIALS.
        """
        self.registry = registry
        self.model = model or self.DEFAULT_MODEL
        
        # Get credentials path
        self._credentials_path = credentials_path or get_google_cloud_credentials_path()
        if not self._credentials_path:
            raise RoutingError(
                "Google Cloud credentials not found. Set GOOGLE_APPLICATION_CREDENTIALS "
                "environment variable or place credentials at "
                "config/credentials/google-service-account.json"
            )
        
        # Load credentials
        try:
            self._credentials = service_account.Credentials.from_service_account_file(
                str(self._credentials_path)
            )
        except Exception as e:
            raise RoutingError(f"Failed to load Google Cloud credentials: {e}")
        
        # Get project ID from credentials or environment
        if not project_id:
            # Try to read from credentials file
            try:
                with open(self._credentials_path) as f:
                    creds_data = json.load(f)
                    project_id = creds_data.get("project_id")
            except Exception:
                pass
            
            # Fallback to environment variable
            if not project_id:
                project_id = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")
        
        if not project_id:
            raise RoutingError(
                "GCP project ID not found. Set ANTHROPIC_VERTEX_PROJECT_ID environment variable "
                "or ensure project_id is in service account JSON."
            )
        
        self._project_id = project_id
        
        # Get location
        self._location = location or os.getenv("CLOUD_ML_REGION", "us-central1")
        
        # Initialize Vertex AI
        try:
            aiplatform.init(
                project=self._project_id,
                location=self._location,
                credentials=self._credentials,
            )
        except Exception as e:
            raise RoutingError(f"Failed to initialize Vertex AI: {e}")
        
        # Initialize GenerativeModel
        try:
            self._generative_model = GenerativeModel(self.model)
        except Exception as e:
            raise RoutingError(f"Failed to initialize GenerativeModel: {e}")

    def _build_routing_prompt(self, user_prompt: str) -> str:
        """
        Build the prompt for the LLM to classify the user's request.
        
        Args:
            user_prompt: The user's task description.
            
        Returns:
            str: The formatted prompt for the LLM.
        """
        repos = self.registry.get_all_repos()
        
        repo_descriptions = "\n".join([
            f"- **{repo.id}**: {repo.description.strip()}"
            for repo in repos
        ])
        
        return f"""You are a repository routing assistant. Your task is to analyze the user's request and determine which repository is the best match.

## Available Repositories:
{repo_descriptions}

## User's Task:
"{user_prompt}"

## Instructions:
1. Analyze the user's task and match it to the most relevant repository.
2. Consider keywords, technical stack, and the nature of the work described.
3. Return ONLY the repository ID that best matches the task.
4. If the task clearly doesn't match any repository, return "UNKNOWN".

## Response Format:
Return only the repository ID (e.g., "auth-service" or "frontend-dashboard"). No explanation needed."""

    def route(self, user_prompt: str) -> str:
        """
        Route a user prompt to the appropriate repository.
        
        Uses Google Vertex AI (Gemini) to classify the user's request and
        determine which repository is the best match.
        
        Args:
            user_prompt: The user's task description.
            
        Returns:
            str: The repository ID that best matches the task.
            
        Raises:
            RoutingError: If routing fails or no valid repository is found.
        """
        if not user_prompt or not user_prompt.strip():
            raise RoutingError("User prompt cannot be empty")
        
        routing_prompt = self._build_routing_prompt(user_prompt)
        
        try:
            # Generate content using Gemini
            response = self._generative_model.generate_content(
                routing_prompt,
                generation_config={
                    "max_output_tokens": 50,  # We only need a short response (repo_id)
                    "temperature": 0.1,  # Low temperature for deterministic routing
                },
            )
        except Exception as e:
            raise RoutingError(f"Vertex AI error during routing: {e}")
        
        # Extract the repo_id from the response
        if not response or not response.text:
            raise RoutingError("Empty response from routing LLM")
        
        # Get text from the response
        repo_id = response.text.strip().strip('"').strip("'")
        
        # Clean up the response - remove any markdown or extra text
        repo_id = repo_id.split("\n")[0].strip()
        
        # Handle edge cases
        if repo_id.upper() == "UNKNOWN":
            raise RoutingError(
                f"Could not match task to any repository. Task: '{user_prompt[:100]}...'"
            )
        
        # Validate the repo_id exists in registry
        valid_ids = self.registry.get_repo_ids()
        if repo_id not in valid_ids:
            # Try to extract a valid repo ID from the response
            for valid_id in valid_ids:
                if valid_id.lower() in repo_id.lower():
                    repo_id = valid_id
                    break
            else:
                raise RoutingError(
                    f"Invalid repository ID '{repo_id}' returned by router. "
                    f"Valid IDs: {', '.join(valid_ids)}"
                )
        
        return repo_id

    def route_with_confidence(self, user_prompt: str) -> tuple[str, RepoConfig]:
        """
        Route a user prompt and return both the repo_id and full config.
        
        Convenience method that returns the full RepoConfig along with the ID.
        
        Args:
            user_prompt: The user's task description.
            
        Returns:
            tuple[str, RepoConfig]: The repository ID and its full configuration.
        """
        repo_id = self.route(user_prompt)
        repo_config = self.registry.get_repo(repo_id)
        return repo_id, repo_config


__all__ = [
    "RepoRouter",
    "RoutingError",
]

