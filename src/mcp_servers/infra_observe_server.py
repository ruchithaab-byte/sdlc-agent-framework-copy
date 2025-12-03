"""
Infrastructure Observation MCP Server.

Provides tools and resources for:
    - Terraform analysis (code_execution_terraform_analyze)
    - Docker build/push (docker_build_push)
    - Secret rotation (rotate_secret)
    - Feature flag management (toggle_feature_flag)
    - Observability metrics (check_langfuse_score)
    - Cost analysis (code_execution_cost_analysis)

This server follows the same pattern as linear_server.py and other
Python MCP servers in this project.
"""

from __future__ import annotations

import json
import os
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class InfraObserveConfig:
    """Configuration for infrastructure observation operations."""
    
    # Terraform
    terraform_state_bucket: str = ""
    terraform_state_key: str = "terraform.tfstate"
    
    # AWS
    aws_region: str = "us-east-1"
    guardduty_detector_id: str = ""
    
    # HashiCorp Vault
    vault_addr: str = "http://localhost:8200"
    vault_token: str = ""
    
    # Unleash Feature Flags
    unleash_url: str = "http://localhost:4242"
    unleash_api_token: str = ""
    
    # Langfuse Observability
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    
    # Docker
    docker_registry: str = "docker.io"
    
    @classmethod
    def from_env(cls) -> "InfraObserveConfig":
        """Load configuration from environment variables."""
        return cls(
            terraform_state_bucket=os.getenv("TERRAFORM_STATE_BUCKET", ""),
            terraform_state_key=os.getenv("TERRAFORM_STATE_KEY", "terraform.tfstate"),
            aws_region=os.getenv("AWS_REGION", "us-east-1"),
            guardduty_detector_id=os.getenv("GUARDDUTY_DETECTOR_ID", ""),
            vault_addr=os.getenv("VAULT_ADDR", "http://localhost:8200"),
            vault_token=os.getenv("VAULT_TOKEN", ""),
            unleash_url=os.getenv("UNLEASH_URL", "http://localhost:4242"),
            unleash_api_token=os.getenv("UNLEASH_API_TOKEN", ""),
            langfuse_host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
            langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            docker_registry=os.getenv("DOCKER_REGISTRY", "docker.io"),
        )


@dataclass
class TerraformFinding:
    """A finding from Terraform plan analysis."""
    severity: str
    category: str
    resource: str
    message: str
    recommendation: str


@dataclass
class CostRecommendation:
    """A cost optimization recommendation."""
    id: str
    category: str
    service: str
    description: str
    estimated_monthly_savings: float
    effort: str
    details: Optional[str] = None


class InfraObserveMCPServer:
    """
    MCP server for infrastructure observation, deployment, and security operations.
    
    Provides the following tools matching ClaudeCodeArtifacts.md Table 6:
    - code_execution_terraform_analyze
    - docker_build_push
    - rotate_secret
    - toggle_feature_flag
    - check_langfuse_score
    - code_execution_cost_analysis
    """
    
    def __init__(self, config: Optional[InfraObserveConfig] = None) -> None:
        self.config = config or InfraObserveConfig.from_env()
    
    # =========================================================================
    # Tool: code_execution_terraform_analyze
    # =========================================================================
    
    async def terraform_analyze(
        self,
        plan_json: str,
        check_types: Optional[List[str]] = None,
        severity: str = "medium",
    ) -> Dict[str, Any]:
        """
        Analyze Terraform plan JSON for security risks, compliance issues,
        and best practice violations.
        
        Args:
            plan_json: JSON output from `terraform plan -json` or `terraform show -json`
            check_types: Types of checks to perform. Defaults to all.
                Options: security, compliance, cost, best_practices, drift
            severity: Minimum severity level to report. Defaults to "medium".
                Options: critical, high, medium, low, all
        
        Returns:
            Analysis results with findings and summary.
        """
        try:
            plan = json.loads(plan_json)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}", "status": "error"}
        
        checks = check_types or ["security", "compliance", "cost", "best_practices"]
        findings: List[TerraformFinding] = []
        
        resource_changes = plan.get("resource_changes", [])
        
        for change in resource_changes:
            resource_type = change.get("type", "")
            resource_name = change.get("name", "")
            actions = change.get("change", {}).get("actions", [])
            after = change.get("change", {}).get("after", {})
            
            # Security checks
            if "security" in checks:
                findings.extend(self._check_security(resource_type, resource_name, after))
            
            # Compliance checks
            if "compliance" in checks and "create" in actions:
                findings.extend(self._check_compliance(resource_type, resource_name, after))
            
            # Cost checks
            if "cost" in checks:
                findings.extend(self._check_cost(resource_type, resource_name, after))
            
            # Best practices checks
            if "best_practices" in checks:
                findings.extend(self._check_best_practices(resource_type, resource_name, change))
        
        # Filter by severity
        severity_order = ["critical", "high", "medium", "low"]
        if severity != "all":
            min_idx = severity_order.index(severity)
            findings = [f for f in findings if severity_order.index(f.severity) <= min_idx]
        
        # Sort by severity
        findings.sort(key=lambda f: severity_order.index(f.severity))
        
        return {
            "status": "success",
            "summary": {
                "total_findings": len(findings),
                "critical": sum(1 for f in findings if f.severity == "critical"),
                "high": sum(1 for f in findings if f.severity == "high"),
                "medium": sum(1 for f in findings if f.severity == "medium"),
                "low": sum(1 for f in findings if f.severity == "low"),
            },
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "resource": f.resource,
                    "message": f.message,
                    "recommendation": f.recommendation,
                }
                for f in findings
            ],
            "resources_analyzed": len(resource_changes),
        }
    
    def _check_security(
        self, resource_type: str, resource_name: str, after: Dict
    ) -> List[TerraformFinding]:
        """Check for security issues in Terraform resources."""
        findings = []
        resource_id = f"{resource_type}.{resource_name}"
        
        # Public S3 buckets
        if resource_type == "aws_s3_bucket":
            acl = after.get("acl", "")
            if acl in ("public-read", "public-read-write"):
                findings.append(TerraformFinding(
                    severity="critical",
                    category="security",
                    resource=resource_id,
                    message="S3 bucket has public ACL",
                    recommendation="Use private ACL and configure bucket policies for specific access",
                ))
        
        # Open security groups
        if resource_type in ("aws_security_group", "aws_security_group_rule"):
            for ingress in after.get("ingress", []):
                cidr_blocks = ingress.get("cidr_blocks", [])
                from_port = ingress.get("from_port", 0)
                if "0.0.0.0/0" in cidr_blocks:
                    if from_port == 22:
                        findings.append(TerraformFinding(
                            severity="high",
                            category="security",
                            resource=resource_id,
                            message="SSH port 22 is open to the world",
                            recommendation="Restrict SSH access to specific IP ranges or use a bastion host",
                        ))
                    elif from_port == 3389:
                        findings.append(TerraformFinding(
                            severity="high",
                            category="security",
                            resource=resource_id,
                            message="RDP port 3389 is open to the world",
                            recommendation="Restrict RDP access to specific IP ranges",
                        ))
        
        # Unencrypted storage
        if resource_type in ("aws_ebs_volume", "aws_rds_instance", "aws_rds_cluster"):
            if after.get("encrypted") is False or after.get("storage_encrypted") is False:
                findings.append(TerraformFinding(
                    severity="high",
                    category="security",
                    resource=resource_id,
                    message="Resource is not encrypted at rest",
                    recommendation="Enable encryption using KMS",
                ))
        
        return findings
    
    def _check_compliance(
        self, resource_type: str, resource_name: str, after: Dict
    ) -> List[TerraformFinding]:
        """Check for compliance issues (missing tags, etc.)."""
        findings = []
        resource_id = f"{resource_type}.{resource_name}"
        
        # Check for required tags
        tags = after.get("tags", {}) or {}
        required_tags = ["Environment", "Owner", "CostCenter"]
        missing_tags = [tag for tag in required_tags if tag not in tags]
        
        if missing_tags and resource_type.startswith("aws_"):
            findings.append(TerraformFinding(
                severity="medium",
                category="compliance",
                resource=resource_id,
                message=f"Missing required tags: {', '.join(missing_tags)}",
                recommendation="Add required tags for resource tracking and cost allocation",
            ))
        
        return findings
    
    def _check_cost(
        self, resource_type: str, resource_name: str, after: Dict
    ) -> List[TerraformFinding]:
        """Check for cost optimization opportunities."""
        findings = []
        resource_id = f"{resource_type}.{resource_name}"
        
        # Large instance types
        if resource_type == "aws_instance":
            instance_type = after.get("instance_type", "")
            if "xlarge" in instance_type or "metal" in instance_type:
                findings.append(TerraformFinding(
                    severity="low",
                    category="cost",
                    resource=resource_id,
                    message=f"Large instance type: {instance_type}",
                    recommendation="Consider if this instance size is necessary or if reserved instances could reduce cost",
                ))
        
        return findings
    
    def _check_best_practices(
        self, resource_type: str, resource_name: str, change: Dict
    ) -> List[TerraformFinding]:
        """Check for best practice violations."""
        findings = []
        resource_id = f"{resource_type}.{resource_name}"
        
        # Check for hardcoded credentials
        after_str = json.dumps(change.get("change", {}).get("after", {}))
        if "AKIA" in after_str or "aws_access_key" in after_str.lower():
            findings.append(TerraformFinding(
                severity="critical",
                category="best_practices",
                resource=resource_id,
                message="Potential hardcoded AWS credentials detected",
                recommendation="Use IAM roles, secrets manager, or environment variables instead",
            ))
        
        return findings
    
    # =========================================================================
    # Tool: docker_build_push
    # =========================================================================
    
    async def docker_build_push(
        self,
        dockerfile_path: str,
        context_path: str,
        image_name: str,
        tag: str,
        build_args: Optional[Dict[str, str]] = None,
        target: Optional[str] = None,
        push: bool = True,
        platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a Docker image and optionally push it to the configured registry.
        
        Args:
            dockerfile_path: Path to the Dockerfile
            context_path: Build context path
            image_name: Name for the image (e.g., "my-service")
            tag: Tag for the image (e.g., "v1.0.0")
            build_args: Build arguments as key-value pairs
            target: Target stage for multi-stage builds
            push: Whether to push after building. Defaults to True.
            platform: Target platform (e.g., "linux/amd64,linux/arm64")
        
        Returns:
            Build result with commands and metadata.
        """
        registry = self.config.docker_registry
        full_image_name = f"{registry}/{image_name}:{tag}"
        
        # Build the docker command
        build_cmd = ["docker", "build", "-f", dockerfile_path, "-t", full_image_name]
        
        if build_args:
            for key, value in build_args.items():
                build_cmd.extend(["--build-arg", f"{key}={value}"])
        
        if target:
            build_cmd.extend(["--target", target])
        
        if platform:
            build_cmd.extend(["--platform", platform])
        
        build_cmd.append(context_path)
        
        return {
            "status": "simulated",
            "build_command": " ".join(build_cmd),
            "push_command": f"docker push {full_image_name}" if push else None,
            "image": {
                "name": image_name,
                "tag": tag,
                "full_name": full_image_name,
                "registry": registry,
            },
            "message": f"Image {full_image_name} would be built{' and pushed' if push else ''}",
            "metadata": {
                "dockerfile": dockerfile_path,
                "context": context_path,
                "build_args": build_args or {},
                "target": target,
                "platform": platform or "linux/amd64",
            },
        }
    
    # =========================================================================
    # Tool: rotate_secret
    # =========================================================================
    
    async def rotate_secret(
        self,
        secret_path: str,
        provider: str,
        rotation_type: str,
        new_value: Optional[str] = None,
        secret_length: int = 32,
        deprecate_old: bool = True,
        notify_services: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Rotate a secret in HashiCorp Vault or AWS Secrets Manager.
        
        Args:
            secret_path: Path to the secret (e.g., "secret/data/my-app/db-password")
            provider: Secret management provider ("vault" or "aws")
            rotation_type: "generate" for new random secret, "manual" requires new_value
            new_value: New secret value (required if rotation_type is "manual")
            secret_length: Length for generated secrets. Defaults to 32.
            deprecate_old: Whether to mark old version as deprecated. Defaults to True.
            notify_services: Service names to notify about the rotation
        
        Returns:
            Rotation result with status and metadata.
        """
        if rotation_type == "manual" and not new_value:
            return {
                "status": "error",
                "error": "new_value is required when rotation_type is 'manual'",
            }
        
        # Generate secret if needed
        if rotation_type == "generate":
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            generated_secret = "".join(secrets.choice(alphabet) for _ in range(secret_length))
        else:
            generated_secret = "[PROVIDED_VALUE]"
        
        result: Dict[str, Any] = {
            "status": "simulated",
            "provider": provider,
            "secret_path": secret_path,
            "rotation": {
                "type": rotation_type,
                "new_version_created": True,
                "old_version_deprecated": deprecate_old,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            "security_note": "Secret value is not logged. Verify rotation through your secret manager UI.",
        }
        
        if provider == "vault":
            result["vault"] = {
                "addr": self.config.vault_addr,
                "command": f"vault kv put {secret_path} value=[GENERATED]" if rotation_type == "generate" else f"vault kv put {secret_path} value=[PROVIDED]",
            }
        elif provider == "aws":
            result["aws"] = {
                "region": self.config.aws_region,
                "command": f"aws secretsmanager update-secret --secret-id {secret_path} --secret-string '[VALUE]'",
            }
        
        if notify_services:
            result["notifications"] = {
                "services": notify_services,
                "status": "pending",
                "message": f"Rotation notification would be sent to: {', '.join(notify_services)}",
            }
        
        return result
    
    # =========================================================================
    # Tool: toggle_feature_flag
    # =========================================================================
    
    async def toggle_feature_flag(
        self,
        flag_name: str,
        action: str,
        environment: str,
        strategy: Optional[Dict[str, Any]] = None,
        rollout_percentage: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Toggle a feature flag in Unleash.
        
        Args:
            flag_name: Name of the feature flag
            action: Action to perform ("enable", "disable", "update_strategy")
            environment: Target environment (e.g., "production", "staging")
            strategy: Strategy configuration for update_strategy action
            rollout_percentage: Percentage for gradual rollout (0-100)
            reason: Reason for the change (for audit logging)
        
        Returns:
            Toggle result with API details and rollback instructions.
        """
        endpoint = f"{self.config.unleash_url}/api/admin/projects/default/features/{flag_name}/environments/{environment}"
        
        api_payload: Dict[str, Any] = {}
        
        if action == "enable":
            api_payload = {"enabled": True}
        elif action == "disable":
            api_payload = {"enabled": False}
        elif action == "update_strategy":
            if rollout_percentage is not None:
                api_payload = {
                    "strategies": [{
                        "name": "flexibleRollout",
                        "parameters": {
                            "rollout": str(rollout_percentage),
                            "stickiness": "default",
                            "groupId": flag_name,
                        },
                    }],
                }
            elif strategy:
                api_payload = {
                    "strategies": [{
                        "name": strategy.get("name", "default"),
                        "parameters": strategy.get("parameters", {}),
                    }],
                }
        
        # Determine rollback command
        if action == "enable":
            rollback = f'toggle_feature_flag(flag_name="{flag_name}", action="disable", environment="{environment}")'
        elif action == "disable":
            rollback = f'toggle_feature_flag(flag_name="{flag_name}", action="enable", environment="{environment}")'
        else:
            rollback = "Restore previous strategy configuration"
        
        result: Dict[str, Any] = {
            "status": "simulated",
            "flag": {
                "name": flag_name,
                "environment": environment,
                "action": action,
            },
            "api": {
                "endpoint": endpoint,
                "method": "PATCH",
                "payload": api_payload,
            },
            "audit": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "reason": reason or "No reason provided",
                "user": "agent",
            },
            "rollback": {"command": rollback},
        }
        
        if environment == "production":
            result["warning"] = "This change affects production traffic. Monitor metrics closely after deployment."
        
        return result
    
    # =========================================================================
    # Tool: check_langfuse_score
    # =========================================================================
    
    async def check_langfuse_score(
        self,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        time_range: Optional[Dict[str, str]] = None,
        metrics: Optional[List[str]] = None,
        group_by: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Query Langfuse for LLM quality scores, latency metrics, and cost data.
        
        Args:
            trace_id: Specific trace ID to query
            session_id: Session ID to filter traces
            time_range: Time range with "start" and "end" keys in ISO format
            metrics: Metrics to retrieve. Defaults to all.
                Options: quality_score, latency, token_usage, cost, error_rate, user_feedback
            group_by: Group results by dimension (model, trace_name, user_id, hour, day)
            limit: Maximum number of results. Defaults to 100.
        
        Returns:
            Metrics summary and recommendations.
        """
        requested_metrics = metrics or ["quality_score", "latency", "token_usage", "cost", "error_rate"]
        
        # Build query params
        query_params: Dict[str, str] = {"limit": str(limit)}
        if trace_id:
            query_params["traceId"] = trace_id
        if session_id:
            query_params["sessionId"] = session_id
        if time_range:
            query_params["fromTimestamp"] = time_range.get("start", "")
            query_params["toTimestamp"] = time_range.get("end", "")
        if group_by:
            query_params["groupBy"] = group_by
        
        # Simulated metrics data
        metrics_data: Dict[str, Any] = {}
        
        if "quality_score" in requested_metrics:
            metrics_data["quality_score"] = {
                "mean": 0.87,
                "p50": 0.89,
                "p95": 0.72,
                "p99": 0.58,
                "trend": "stable",
            }
        
        if "latency" in requested_metrics:
            metrics_data["latency"] = {
                "mean": 2340,
                "p50": 1890,
                "p95": 5200,
                "p99": 8500,
                "unit": "ms",
                "trend": "increasing",
            }
        
        if "token_usage" in requested_metrics:
            metrics_data["token_usage"] = {
                "total": 1_500_000,
                "input": 1_200_000,
                "output": 300_000,
                "avg_per_trace": 1203,
            }
        
        if "cost" in requested_metrics:
            metrics_data["cost"] = {
                "total": 45.30,
                "currency": "USD",
                "by_model": {
                    "claude-3-5-sonnet": 38.50,
                    "claude-3-haiku": 6.80,
                },
            }
        
        if "error_rate" in requested_metrics:
            metrics_data["error_rate"] = {
                "rate": 0.02,
                "total_errors": 25,
                "top_errors": [
                    {"type": "rate_limit", "count": 15},
                    {"type": "timeout", "count": 7},
                    {"type": "invalid_response", "count": 3},
                ],
            }
        
        # Generate recommendations
        recommendations = []
        if metrics_data.get("latency", {}).get("trend") == "increasing":
            recommendations.append("Consider implementing caching or optimizing prompts to reduce latency")
        if metrics_data.get("error_rate", {}).get("rate", 0) > 0.05:
            recommendations.append("Error rate is above threshold. Review error logs for root cause.")
        
        return {
            "status": "simulated",
            "query": {
                "host": self.config.langfuse_host,
                "params": query_params,
                "metrics_requested": requested_metrics,
            },
            "data": {
                "summary": {
                    "total_traces": 1247,
                    "avg_quality_score": 0.87,
                    "avg_latency_ms": 2340,
                    "total_tokens": 1_500_000,
                    "estimated_cost": 45.30,
                    "error_rate": 0.02,
                },
                "metrics": metrics_data,
                "alerts": [
                    {
                        "severity": "warning",
                        "message": "Latency p95 has increased 15% in the last hour",
                        "metric": "latency",
                    },
                ],
            },
            "recommendations": recommendations,
        }
    
    # =========================================================================
    # Tool: code_execution_cost_analysis
    # =========================================================================
    
    async def cost_analysis(
        self,
        time_range: Dict[str, str],
        group_by: Optional[List[str]] = None,
        tag_key: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_recommendations: bool = True,
        compare_with_previous_period: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze cloud infrastructure costs and identify optimization opportunities.
        
        Args:
            time_range: Time range with "start" and "end" keys in YYYY-MM-DD format
            group_by: Dimensions to group costs by.
                Options: SERVICE, LINKED_ACCOUNT, REGION, INSTANCE_TYPE, USAGE_TYPE, TAG
            tag_key: Tag key for TAG grouping (e.g., "Environment", "Team")
            filters: Filters with services, regions, and tags
            include_recommendations: Include cost optimization recommendations. Defaults to True.
            compare_with_previous_period: Include comparison. Defaults to True.
        
        Returns:
            Cost analysis with breakdown and recommendations.
        """
        dimensions = group_by or ["SERVICE"]
        
        # Simulated cost data
        breakdown_by_service = [
            {"service": "Amazon EC2", "cost": 6500.00, "percentage": 42.2},
            {"service": "Amazon RDS", "cost": 3200.00, "percentage": 20.8},
            {"service": "Amazon S3", "cost": 1800.00, "percentage": 11.7},
            {"service": "AWS Lambda", "cost": 1200.00, "percentage": 7.8},
            {"service": "Amazon EKS", "cost": 1100.00, "percentage": 7.1},
            {"service": "Other", "cost": 1620.50, "percentage": 10.5},
        ]
        
        breakdown_by_region = None
        if "REGION" in dimensions:
            breakdown_by_region = [
                {"region": "us-east-1", "cost": 9500.00, "percentage": 61.6},
                {"region": "eu-west-1", "cost": 4200.00, "percentage": 27.2},
                {"region": "ap-southeast-1", "cost": 1720.50, "percentage": 11.2},
            ]
        
        recommendations = None
        potential_savings = None
        
        if include_recommendations:
            recommendations = [
                CostRecommendation(
                    id="ec2-rightsizing",
                    category="Right Sizing",
                    service="Amazon EC2",
                    description="15 instances are underutilized (avg CPU < 10%)",
                    estimated_monthly_savings=850.00,
                    effort="medium",
                ),
                CostRecommendation(
                    id="reserved-instances",
                    category="Commitment Discounts",
                    service="Amazon EC2",
                    description="On-demand usage could benefit from Reserved Instances",
                    estimated_monthly_savings=1200.00,
                    effort="low",
                    details="23 instances running consistently for 90+ days",
                ),
                CostRecommendation(
                    id="s3-lifecycle",
                    category="Storage Optimization",
                    service="Amazon S3",
                    description="2.5TB of data not accessed in 90+ days",
                    estimated_monthly_savings=180.00,
                    effort="low",
                    details="Implement lifecycle policy to transition to S3 Glacier",
                ),
                CostRecommendation(
                    id="unused-resources",
                    category="Unused Resources",
                    service="Multiple",
                    description="Unused EBS volumes and unattached Elastic IPs detected",
                    estimated_monthly_savings=320.00,
                    effort="low",
                ),
            ]
            potential_savings = {
                "total": 2550.00,
                "percentage_of_spend": 16.5,
            }
        
        return {
            "status": "simulated",
            "query": {
                "region": self.config.aws_region,
                "time_range": time_range,
                "dimensions": dimensions,
                "filters": filters or {},
            },
            "data": {
                "summary": {
                    "total_cost": 15420.50,
                    "currency": "USD",
                    "period_start": time_range["start"],
                    "period_end": time_range["end"],
                    "previous_period_cost": 14200.00 if compare_with_previous_period else None,
                    "percentage_change": 8.6 if compare_with_previous_period else None,
                },
                "breakdown": {
                    "by_service": breakdown_by_service,
                    "by_region": breakdown_by_region,
                },
                "trends": {
                    "daily_average": 514.02,
                    "projected_month_end": 15934.50,
                    "budget_utilization": 77.1,
                    "budget_limit": 20000.00,
                },
                "recommendations": [
                    {
                        "id": r.id,
                        "category": r.category,
                        "service": r.service,
                        "description": r.description,
                        "estimated_monthly_savings": r.estimated_monthly_savings,
                        "effort": r.effort,
                        "details": r.details,
                    }
                    for r in (recommendations or [])
                ],
                "potential_savings": potential_savings,
            },
            "export_formats": {
                "csv": f"aws ce get-cost-and-usage --time-period Start={time_range['start']},End={time_range['end']} --output csv",
                "json": f"aws ce get-cost-and-usage --time-period Start={time_range['start']},End={time_range['end']} --output json",
            },
        }
    
    # =========================================================================
    # Resources (Read-only data)
    # =========================================================================
    
    async def get_terraform_state(self) -> Dict[str, Any]:
        """
        Get current Terraform infrastructure state.
        Resource URI: terraform://state
        """
        return {
            "version": 4,
            "terraform_version": "1.6.0",
            "serial": 42,
            "outputs": {
                "api_gateway_url": {"value": "https://api.example.com", "type": "string"},
                "database_endpoint": {"value": "db.example.com:5432", "type": "string"},
                "kubernetes_cluster_name": {"value": "prod-eks-cluster", "type": "string"},
            },
            "resources": [
                {
                    "type": "aws_eks_cluster",
                    "name": "main",
                    "instances": [{"attributes": {"name": "prod-eks-cluster", "version": "1.28", "status": "ACTIVE"}}],
                },
                {
                    "type": "aws_rds_instance",
                    "name": "main",
                    "instances": [{"attributes": {"identifier": "prod-postgres", "engine": "postgres", "multi_az": True}}],
                },
            ],
            "metadata": {
                "backend": {"type": "s3", "bucket": self.config.terraform_state_bucket},
                "last_modified": datetime.utcnow().isoformat() + "Z",
            },
        }
    
    async def get_guardduty_findings(self) -> Dict[str, Any]:
        """
        Get active security findings from AWS GuardDuty.
        Resource URI: aws://guardduty/findings
        """
        return {
            "detector_id": self.config.guardduty_detector_id,
            "findings": [
                {
                    "id": "finding-001",
                    "type": "UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration",
                    "severity": 8.0,
                    "title": "Credentials used from outside AWS",
                    "description": "AWS credentials were used from an IP address outside of AWS",
                    "resource": {"type": "AccessKey", "id": "AKIA..."},
                    "created_at": "2024-01-15T10:30:00Z",
                },
            ],
            "summary": {"critical": 0, "high": 1, "medium": 3, "low": 5},
        }
    
    async def get_metrics(self, metric_type: str = "all") -> Dict[str, Any]:
        """
        Get real-time performance metrics.
        Resource URI: context7://metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metrics": {
                "rps": {"value": 1250, "unit": "requests/second"},
                "latency_p50": {"value": 45, "unit": "ms"},
                "latency_p99": {"value": 230, "unit": "ms"},
                "error_rate": {"value": 0.02, "unit": "percentage"},
                "cpu_utilization": {"value": 65, "unit": "percentage"},
                "memory_utilization": {"value": 72, "unit": "percentage"},
            },
        }
    
    async def get_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        Get distributed trace details.
        Resource URI: xray://traces/{id}
        """
        return {
            "trace_id": trace_id,
            "duration_ms": 234,
            "status": "OK",
            "segments": [
                {"name": "api-gateway", "duration_ms": 5, "status": "OK"},
                {"name": "auth-service", "duration_ms": 45, "status": "OK"},
                {"name": "user-service", "duration_ms": 120, "status": "OK"},
                {"name": "database", "duration_ms": 64, "status": "OK"},
            ],
        }


# Example usage
async def example_usage() -> None:
    """Demonstrate server usage."""
    server = InfraObserveMCPServer()
    
    # Example: Terraform analysis
    result = await server.terraform_analyze(
        plan_json='{"resource_changes": []}',
        check_types=["security", "compliance"],
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())

