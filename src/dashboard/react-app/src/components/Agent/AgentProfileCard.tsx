import { Card, Tag, Progress, Tooltip, Space, Badge } from 'antd';
import {
  DollarOutlined,
  CodeOutlined,
  SafetyOutlined,
  RocketOutlined,
  SettingOutlined,
  FileTextOutlined,
  ApiOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import type { AgentProfile, AgentCostSummary } from '../../types';
import './AgentProfileCard.css';

interface AgentProfileCardProps {
  profile: AgentProfile;
  costSummary?: AgentCostSummary;
  isActive?: boolean;
}

// Agent icons based on agent type
const getAgentIcon = (agentId: string) => {
  switch (agentId) {
    case 'sentinel':
      return <SafetyOutlined />;
    case 'codecraft':
      return <CodeOutlined />;
    case 'infraops':
      return <RocketOutlined />;
    case 'qualityguard':
      return <ThunderboltOutlined />;
    default:
      return <SettingOutlined />;
  }
};

// Model profile colors
const getModelColor = (profile: string) => {
  return profile === 'build' ? '#1890ff' : '#722ed1';
};

// Permission mode colors
const getPermissionColor = (mode: string) => {
  switch (mode) {
    case 'acceptEdits':
      return 'green';
    case 'bypassPermissions':
      return 'red';
    default:
      return 'default';
  }
};

export function AgentProfileCard({ profile, costSummary, isActive }: AgentProfileCardProps) {
  const currentCost = costSummary?.total_cost_usd ?? 0;
  const budgetPercent = profile.budget_usd
    ? Math.min((currentCost / profile.budget_usd) * 100, 100)
    : 0;

  const budgetStatus: 'success' | 'exception' | 'active' | 'normal' =
    budgetPercent >= 100
      ? 'exception'
      : budgetPercent >= 80
      ? 'active'
      : 'success';

  const statusColor =
    budgetPercent >= 100
      ? '#ff4d4f'
      : budgetPercent >= 80
      ? '#faad14'
      : '#52c41a';

  return (
    <Badge.Ribbon
      text={isActive ? 'Running' : ''}
      color={isActive ? 'green' : 'transparent'}
      style={{ display: isActive ? 'block' : 'none' }}
    >
      <Card
        className="agent-profile-card"
        title={
          <Space className="card-title-space">
            <span className="agent-icon" style={{ color: getModelColor(profile.model_profile) }}>
              {getAgentIcon(profile.agent_id)}
            </span>
            <span className="agent-name">{profile.agent_id}</span>
          </Space>
        }
        extra={
          <Tag color={getModelColor(profile.model_profile)}>
            {profile.model_profile}
          </Tag>
        }
        size="small"
      >
        {/* Budget Progress */}
        {profile.budget_usd ? (
          <div className="budget-section">
            <div className="budget-header">
              <span className="budget-label">
                <DollarOutlined /> Budget
              </span>
              <span className="budget-amount" style={{ color: statusColor, fontWeight: 600 }}>
                ${currentCost.toFixed(4)} / ${profile.budget_usd.toFixed(2)}
              </span>
            </div>
            <Progress
              percent={budgetPercent}
              status={budgetStatus}
              size="small"
              showInfo={false}
              strokeColor={statusColor}
            />
            {costSummary && (
              <div className="cost-details">
                <span>{costSummary.execution_count} executions</span>
                <span>avg ${costSummary.avg_cost_usd.toFixed(4)}</span>
              </div>
            )}
          </div>
        ) : (
          <div className="budget-section">
            <div className="budget-header">
              <span className="budget-label">
                <DollarOutlined /> Budget
              </span>
              <span className="budget-amount" style={{ color: '#999' }}>
                No budget set
              </span>
            </div>
          </div>
        )}

        {/* Capabilities Tags */}
        <div className="capabilities-section">
          <Space wrap size={[4, 4]}>
            <Tooltip title="Max conversation turns">
              <Tag className="capability-tag">🔄 {profile.max_turns} turns</Tag>
            </Tooltip>

            <Tooltip title={`Permission mode: ${profile.permission_mode}`}>
              <Tag color={getPermissionColor(profile.permission_mode)} className="capability-tag">
                🔐 {profile.permission_mode}
              </Tag>
            </Tooltip>

            {profile.output_schema && (
              <Tooltip title={`Structured output: ${profile.output_schema}`}>
                <Tag color="cyan" className="capability-tag">
                  <FileTextOutlined /> {profile.output_schema}
                </Tag>
              </Tooltip>
            )}

            {profile.system_prompt_file && (
              <Tooltip title="Custom system prompt enabled">
                <Tag color="gold" className="capability-tag">
                  💬 Persona
                </Tag>
              </Tooltip>
            )}

            {profile.mcp_servers.length > 0 && (
              <Tooltip title={`MCP Servers: ${profile.mcp_servers.join(', ')}`}>
                <Tag color="magenta" className="capability-tag">
                  <ApiOutlined /> {profile.mcp_servers.length} MCP
                </Tag>
              </Tooltip>
            )}

            {profile.hooks_profile !== 'default' && (
              <Tooltip title={`Hooks profile: ${profile.hooks_profile}`}>
                <Tag color="purple" className="capability-tag">
                  🪝 {profile.hooks_profile}
                </Tag>
              </Tooltip>
            )}
          </Space>
        </div>

        {/* Extra Tools */}
        {profile.extra_allowed_tools.length > 0 && (
          <div className="extra-tools-section">
            <Tooltip
              title={
                <div>
                  <strong>Extra Tools:</strong>
                  <ul style={{ margin: '4px 0', paddingLeft: 16 }}>
                    {profile.extra_allowed_tools.map((tool) => (
                      <li key={tool}>{tool}</li>
                    ))}
                  </ul>
                </div>
              }
            >
              <Tag color="geekblue" className="capability-tag">
                🔧 +{profile.extra_allowed_tools.length} tools
              </Tag>
            </Tooltip>
          </div>
        )}
      </Card>
    </Badge.Ribbon>
  );
}

export default AgentProfileCard;

