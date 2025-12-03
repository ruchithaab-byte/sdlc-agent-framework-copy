import { useState, useEffect } from 'react';
import { Row, Col, Card, Spin, Alert, Space, Select, Switch, Table, Tag, Progress, Tooltip } from 'antd';
import { TeamOutlined, ReloadOutlined, AppstoreOutlined, TableOutlined } from '@ant-design/icons';
import { AgentProfileCard } from './AgentProfileCard';
import type { AgentProfile, AgentCostSummary, AgentCostsResponse } from '../../types';
import type { ColumnsType } from 'antd/es/table';
import { useAuth } from '../../contexts/AuthContext';
import './AgentProfilesSection.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8766';

// Better categorization based on agent purpose
type AgentCategory = 'planning' | 'development' | 'operations' | 'support';

interface CategorizedAgent {
  category: AgentCategory;
  categoryName: string;
  categoryIcon: string;
  categoryDescription: string;
  agents: AgentProfile[];
}

const categorizeAgents = (profiles: AgentProfile[]): CategorizedAgent[] => {
  const categories: Record<AgentCategory, AgentProfile[]> = {
    planning: [],
    development: [],
    operations: [],
    support: [],
  };

  profiles.forEach((profile) => {
    const agentId = profile.agent_id.toLowerCase();
    
    // Planning & Strategy Agents
    if (['productspec', 'archguard', 'sprintmaster'].includes(agentId)) {
      categories.planning.push(profile);
    }
    // Development Agents
    else if (['codecraft', 'qualityguard'].includes(agentId)) {
      categories.development.push(profile);
    }
    // Operations Agents
    else if (['infraops', 'sentinel', 'sre-triage'].includes(agentId)) {
      categories.operations.push(profile);
    }
    // Support Agents
    else if (['docuscribe', 'finops'].includes(agentId)) {
      categories.support.push(profile);
    }
    // Fallback to model_profile if not explicitly categorized
    else {
      if (profile.model_profile === 'strategy') {
        categories.planning.push(profile);
      } else {
        categories.development.push(profile);
      }
    }
  });

  return [
    {
      category: 'planning',
      categoryName: 'Planning & Strategy',
      categoryIcon: '📊',
      categoryDescription: 'Requirements, architecture, and sprint planning',
      agents: categories.planning,
    },
    {
      category: 'development',
      categoryName: 'Code Development',
      categoryIcon: '💻',
      categoryDescription: 'Code generation, quality checks, and testing',
      agents: categories.development,
    },
    {
      category: 'operations',
      categoryName: 'Operations & Security',
      categoryIcon: '🔒',
      categoryDescription: 'Infrastructure, security, and incident response',
      agents: categories.operations,
    },
    {
      category: 'support',
      categoryName: 'Documentation & Analysis',
      categoryIcon: '📚',
      categoryDescription: 'Documentation, cost analysis, and reporting',
      agents: categories.support,
    },
  ].filter((cat) => cat.agents.length > 0);
};

export function AgentProfilesSection() {
  const { token } = useAuth();
  const [profiles, setProfiles] = useState<AgentProfile[]>([]);
  const [costSummaries, setCostSummaries] = useState<Record<string, AgentCostSummary>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [costPeriod, setCostPeriod] = useState<string>('today');
  const [viewMode, setViewMode] = useState<'card' | 'table'>('card');

  // Fetch agent profiles (public endpoint)
  const fetchProfiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/profiles`);
      if (response.ok) {
        const data = await response.json();
        setProfiles(data);
      } else {
        throw new Error('Failed to fetch profiles');
      }
    } catch (err) {
      setError('Failed to load agent profiles');
      console.error('Error fetching profiles:', err);
    }
  };

  // Fetch cost summaries (requires auth)
  const fetchCosts = async (period: string) => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/costs?period=${period}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data: AgentCostsResponse = await response.json();
        // Convert array to map for easy lookup
        const costsMap: Record<string, AgentCostSummary> = {};
        data.agents.forEach((agent) => {
          costsMap[agent.agent_id] = agent;
        });
        setCostSummaries(costsMap);
      }
    } catch (err) {
      console.error('Error fetching costs:', err);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchProfiles();
      await fetchCosts(costPeriod);
      setLoading(false);
    };
    loadData();
  }, [token]);

  useEffect(() => {
    fetchCosts(costPeriod);
  }, [costPeriod, token]);

  const categorizedAgents = categorizeAgents(profiles);

  // Table columns for table view
  const tableColumns: ColumnsType<AgentProfile & { costSummary?: AgentCostSummary }> = [
    {
      title: 'Agent',
      dataIndex: 'agent_id',
      key: 'agent_id',
      render: (text: string) => (
        <Space>
          <span style={{ fontSize: '16px' }}>🤖</span>
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Category',
      key: 'category',
      render: (_: any, record: AgentProfile) => {
        const category = categorizedAgents.find((cat) =>
          cat.agents.some((a) => a.agent_id === record.agent_id)
        );
        return category ? (
          <Tag color="blue">
            {category.categoryIcon} {category.categoryName}
          </Tag>
        ) : (
          <Tag>{record.model_profile}</Tag>
        );
      },
    },
    {
      title: 'Model Profile',
      dataIndex: 'model_profile',
      key: 'model_profile',
      render: (profile: string) => (
        <Tag color={profile === 'build' ? 'blue' : 'purple'}>{profile}</Tag>
      ),
    },
    {
      title: 'Budget',
      key: 'budget',
      render: (_: any, record: AgentProfile) => {
        const costSummary = costSummaries[record.agent_id];
        const currentCost = costSummary?.total_cost_usd ?? 0;
        const budget = record.budget_usd;
        
        if (!budget) return <Tag>No Budget</Tag>;
        
        const percent = Math.min((currentCost / budget) * 100, 100);
        const status = percent >= 100 ? 'exception' : percent >= 80 ? 'active' : 'success';
        
        return (
          <Space direction="vertical" size={0} style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
              <span>${currentCost.toFixed(4)}</span>
              <span>/ ${budget.toFixed(2)}</span>
            </div>
            <Progress
              percent={percent}
              status={status}
              size="small"
              showInfo={false}
              style={{ marginTop: 4 }}
            />
          </Space>
        );
      },
    },
    {
      title: 'Capabilities',
      key: 'capabilities',
      render: (_: any, record: AgentProfile) => (
        <Space wrap size={[4, 4]}>
          <Tooltip title={`Max turns: ${record.max_turns}`}>
            <Tag size="small">🔄 {record.max_turns}</Tag>
          </Tooltip>
          {record.output_schema && (
            <Tooltip title={`Schema: ${record.output_schema}`}>
              <Tag size="small" color="cyan">📋</Tag>
            </Tooltip>
          )}
          {record.system_prompt_file && (
            <Tooltip title="Custom persona">
              <Tag size="small" color="gold">💬</Tag>
            </Tooltip>
          )}
          {record.mcp_servers.length > 0 && (
            <Tooltip title={`${record.mcp_servers.length} MCP server(s)`}>
              <Tag size="small" color="magenta">🔌 {record.mcp_servers.length}</Tag>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: 'Executions',
      key: 'executions',
      render: (_: any, record: AgentProfile) => {
        const costSummary = costSummaries[record.agent_id];
        if (!costSummary) return '-';
        return (
          <Space direction="vertical" size={0}>
            <span>{costSummary.execution_count} runs</span>
            <span style={{ fontSize: '11px', color: '#999' }}>
              avg ${costSummary.avg_cost_usd.toFixed(4)}
            </span>
          </Space>
        );
      },
    },
  ];

  if (loading) {
    return (
      <Card className="agents-section-card">
        <div className="loading-container">
          <Spin size="large" />
          <p>Loading agent profiles...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="agents-section-card">
        <Alert
          title="Error"
          description={error}
          type="error"
          showIcon
          action={
            <a onClick={() => window.location.reload()}>
              <ReloadOutlined /> Retry
            </a>
          }
        />
      </Card>
    );
  }

  return (
    <Card
      className="agents-section-card"
      title={
        <Space>
          <TeamOutlined />
          <span>SDLC Agent Profiles</span>
          <span className="agent-count">({profiles.length} agents)</span>
        </Space>
      }
      extra={
        <Space>
          <Select
            value={costPeriod}
            onChange={setCostPeriod}
            style={{ width: 120 }}
            size="small"
            options={[
              { value: 'today', label: 'Today' },
              { value: 'week', label: 'This Week' },
              { value: 'month', label: 'This Month' },
              { value: 'all', label: 'All Time' },
            ]}
          />
          <Space>
            <AppstoreOutlined style={{ color: viewMode === 'card' ? '#1890ff' : '#999' }} />
            <Switch
              checked={viewMode === 'table'}
              onChange={(checked) => setViewMode(checked ? 'table' : 'card')}
              checkedChildren={<TableOutlined />}
              unCheckedChildren={<AppstoreOutlined />}
            />
            <TableOutlined style={{ color: viewMode === 'table' ? '#1890ff' : '#999' }} />
          </Space>
        </Space>
      }
    >
      {viewMode === 'card' ? (
        // Card View
        categorizedAgents.map((category) => (
          <div key={category.category} className="agent-group">
            <h4 className="group-title">
              <span className="group-icon">{category.categoryIcon}</span>
              {category.categoryName}
              <span className="group-subtitle">{category.categoryDescription}</span>
            </h4>
            <Row gutter={[16, 16]}>
              {category.agents.map((profile) => (
                <Col xs={24} sm={12} md={12} lg={8} xl={6} key={profile.agent_id}>
                  <AgentProfileCard
                    profile={profile}
                    costSummary={costSummaries[profile.agent_id]}
                  />
                </Col>
              ))}
            </Row>
          </div>
        ))
      ) : (
        // Table View
        <Table
          columns={tableColumns}
          dataSource={profiles.map((p) => ({
            ...p,
            costSummary: costSummaries[p.agent_id],
          }))}
          rowKey="agent_id"
          pagination={false}
          size="small"
        />
      )}
    </Card>
  );
}

export default AgentProfilesSection;
