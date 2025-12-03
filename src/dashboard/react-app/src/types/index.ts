// ============================================================================
// Execution Events (WebSocket)
// ============================================================================

export interface ExecutionEvent {
  timestamp: string;
  session_id: string;
  hook_event: string;
  tool_name?: string;
  agent_name?: string;
  phase?: string;
  status: 'success' | 'error';
  duration_ms?: number;
  // SDK Capabilities - Cost tracking
  cost_usd?: number;
  budget_exceeded?: boolean;
}

export interface WebSocketMessage {
  type: 'initial_data' | 'new_execution';
  executions?: ExecutionEvent[];
  data?: ExecutionEvent;
}

export interface Agent {
  name: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  lastExecution?: ExecutionEvent;
}

// ============================================================================
// Agent Profiles (from AGENT_PROFILES config)
// ============================================================================

export interface AgentProfile {
  agent_id: string;
  model_profile: 'build' | 'strategy';
  max_turns: number;
  permission_mode: 'default' | 'acceptEdits' | 'bypassPermissions';
  output_schema: string | null;
  system_prompt_file: string | null;
  hooks_profile: string;
  budget_usd: number | null;
  mcp_servers: string[];
  extra_allowed_tools: string[];
}

// ============================================================================
// Cost Tracking
// ============================================================================

export interface AgentCostSummary {
  agent_id: string;
  execution_count: number;
  total_cost_usd: number;
  total_tokens: number;
  avg_cost_usd: number;
  budget_usd: number | null;
  budget_utilization_percent: number | null;
}

export interface CostTotals {
  total_cost_usd: number;
  total_budget_usd: number;
  total_executions: number;
  budget_utilization_percent: number | null;
}

export interface AgentCostsResponse {
  period: string;
  agents: AgentCostSummary[];
  totals: CostTotals;
}

// ============================================================================
// Structured Outputs
// ============================================================================

export interface StructuredOutput {
  id: number;
  execution_log_id: number;
  artifact_type: string;
  identifier: string | null;
  created_at: string;
  agent_id?: string;
  session_id: string;
  status: string;
  output_schema: string | null;
  structured_output: Record<string, unknown> | null;
}

export interface AgentOutputsResponse {
  agent_id: string;
  output_schema: string | null;
  outputs: StructuredOutput[];
}

export interface RecentOutputsResponse {
  outputs: StructuredOutput[];
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiError {
  error: string;
}

