import { useState, useEffect } from 'react';
import { Card, Statistic, Table, Tabs, Select, Space, Tag, Spin, App } from 'antd';
import {
  UserOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  DeploymentUnitOutlined,
  FileTextOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useAuth } from '../contexts/AuthContext';
import { OutputsList } from '../components/Output';
import type { StructuredOutput } from '../types';
// Define types locally to avoid import issues
interface UserSummary {
  user_email: string;
  display_name?: string;
  total_sessions: number;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  total_duration_ms: number;
  total_tokens: number;
  total_cost_usd: number;
  agents_used: string[];
  phases_completed: string[];
  tools_used: Record<string, number>;
}

interface RepositorySummary {
  repository_id: number;
  repo_name: string;
  repo_path: string;
  total_users: number;
  total_sessions: number;
  total_executions: number;
  agents_used: string[];
  phases_completed: string[];
  user_summaries: UserSummary[];
}

interface Repository {
  id: number;
  repo_name: string;
  repo_path: string;
  git_remote_url?: string;
  git_branch?: string;
  first_seen_at: string;
  last_seen_at: string;
}

interface DeploymentArtifact {
  id: number;
  execution_log_id: number;
  artifact_url?: string;
  identifier?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface ChangelogArtifact {
  id: number;
  execution_log_id: number;
  artifact_type: 'pr' | 'commit';
  artifact_url?: string;
  identifier?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8766';

const { Option } = Select;

export function SummaryDashboard() {
  const { token } = useAuth();
  const { message } = App.useApp();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<number | null>(null);
  const [period, setPeriod] = useState<'today' | 'week' | 'month'>('today');
  const [summary, setSummary] = useState<RepositorySummary | null>(null);
  const [deployments, setDeployments] = useState<DeploymentArtifact[]>([]);
  const [changelog, setChangelog] = useState<ChangelogArtifact[]>([]);
  const [outputs, setOutputs] = useState<StructuredOutput[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      fetchRepositories();
    }
  }, [token]);

  useEffect(() => {
    if (selectedRepo && token) {
      fetchSummary(selectedRepo, period);
      fetchDeployments(selectedRepo);
      fetchChangelog(selectedRepo);
      fetchOutputs();
    }
  }, [selectedRepo, period, token]);

  const fetchRepositories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/summary/repositories`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setRepositories(data);
        if (data.length > 0 && !selectedRepo) {
          setSelectedRepo(data[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch repositories:', error);
      message.error('Failed to load repositories');
    }
  };

  const fetchSummary = async (repoId: number, period: string) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/summary/repository/${repoId}?period=${period}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      } else {
        message.error('Failed to load summary');
      }
    } catch (error) {
      console.error('Failed to fetch summary:', error);
      message.error('Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  const fetchDeployments = async (repoId: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/summary/deployments/${repoId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setDeployments(data);
      }
    } catch (error) {
      console.error('Failed to fetch deployments:', error);
    }
  };

  const fetchChangelog = async (repoId: number) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/summary/changelog/${repoId}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setChangelog(data);
      }
    } catch (error) {
      console.error('Failed to fetch changelog:', error);
    }
  };

  const fetchOutputs = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/agents/outputs?limit=20`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setOutputs(data.outputs || []);
      }
    } catch (error) {
      console.error('Failed to fetch outputs:', error);
    }
  };

  // Helper function to strip @users.noreply.github.com suffix from email
  const formatEmailDisplay = (email: string): string => {
    if (email.endsWith('@users.noreply.github.com')) {
      return email.replace('@users.noreply.github.com', '');
    }
    return email;
  };

  const userColumns: ColumnsType<UserSummary> = [
    {
      title: 'User',
      key: 'user',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>
            {record.display_name || formatEmailDisplay(record.user_email)}
          </div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
            {formatEmailDisplay(record.user_email)}
          </div>
        </div>
      ),
    },
    {
      title: 'Sessions',
      dataIndex: 'total_sessions',
      align: 'center',
    },
    {
      title: 'Executions',
      dataIndex: 'total_executions',
      align: 'center',
    },
    {
      title: 'Success Rate',
      key: 'success_rate',
      align: 'center',
      render: (_, record) => {
        const rate =
          record.total_executions > 0
            ? ((record.successful_executions / record.total_executions) * 100).toFixed(1)
            : '0';
        const rateNum = parseFloat(rate);
        return (
          <Tag
            color={
              rateNum >= 90 ? 'green' : rateNum >= 70 ? 'orange' : 'red'
            }
          >
            {rate}%
          </Tag>
        );
      },
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record) => {
        const seconds = Math.floor(record.total_duration_ms / 1000);
        const minutes = Math.floor(seconds / 60);
        return `${minutes}m ${seconds % 60}s`;
      },
    },
    {
      title: 'Tokens',
      dataIndex: 'total_tokens',
      align: 'right',
      render: (value) => value.toLocaleString(),
    },
    {
      title: 'Cost',
      dataIndex: 'total_cost_usd',
      align: 'right',
      render: (value) => `$${value.toFixed(2)}`,
    },
    {
      title: 'Agents',
      key: 'agents',
      render: (_, record) => (
        <Space wrap>
          {record.agents_used.map((agent) => (
            <Tag key={agent} color="blue">
              {agent}
            </Tag>
          ))}
        </Space>
      ),
    },
  ];

  if (!token) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div>Please log in to view the dashboard.</div>
      </div>
    );
  }

  if (repositories.length === 0 && !loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div>No repositories found. Run an agent to start tracking executions.</div>
      </div>
    );
  }

  if (!summary && loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Loading dashboard...</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <div>Select a repository to view summary.</div>
      </div>
    );
  }

  const successRate =
    summary.total_executions > 0
      ? ((summary.user_summaries.reduce((acc, u) => acc + u.successful_executions, 0) /
          summary.total_executions) *
          100).toFixed(1)
      : 0;

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Header Controls */}
        <Card>
          <Space>
            <Select
              value={selectedRepo}
              onChange={setSelectedRepo}
              style={{ width: 300 }}
              placeholder="Select Repository"
            >
              {repositories.map((repo) => (
                <Option key={repo.id} value={repo.id}>
                  {repo.repo_name} ({repo.repo_path})
                </Option>
              ))}
            </Select>
            <Select value={period} onChange={setPeriod} style={{ width: 150 }}>
              <Option value="today">Today</Option>
              <Option value="week">This Week</Option>
              <Option value="month">This Month</Option>
            </Select>
          </Space>
        </Card>

        {/* Summary Statistics */}
        <Card title={`${summary.repo_name} - ${period.charAt(0).toUpperCase() + period.slice(1)} Summary`}>
          <Space size="large" wrap>
            <Statistic
              title="Total Users"
              value={summary.total_users}
              prefix={<UserOutlined />}
            />
            <Statistic
              title="Total Sessions"
              value={summary.total_sessions}
              prefix={<RocketOutlined />}
            />
            <Statistic title="Total Executions" value={summary.total_executions} />
            <Statistic
              title="Success Rate"
              value={successRate}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined />}
            />
          </Space>
        </Card>

        {/* Main Content Tabs */}
        <Card>
          <Tabs
            items={[
              {
                key: 'users',
                label: 'User Progress',
                children: (
                  <Table
                    columns={userColumns}
                    dataSource={summary.user_summaries}
                    rowKey="user_email"
                    loading={loading}
                    pagination={false}
                  />
                ),
              },
              {
                key: 'deployments',
                label: (
                  <span>
                    <DeploymentUnitOutlined /> Deployments ({deployments.length})
                  </span>
                ),
                children: (
                  <Table
                    dataSource={deployments}
                    rowKey="id"
                    columns={[
                      {
                        title: 'Deployment URL',
                        dataIndex: 'artifact_url',
                        render: (url) =>
                          url ? (
                            <a href={url} target="_blank" rel="noopener noreferrer">
                              {url}
                            </a>
                          ) : (
                            'N/A'
                          ),
                      },
                      {
                        title: 'Identifier',
                        dataIndex: 'identifier',
                      },
                      {
                        title: 'Created At',
                        dataIndex: 'created_at',
                        render: (date) => new Date(date).toLocaleString(),
                      },
                    ]}
                    pagination={{ pageSize: 10 }}
                  />
                ),
              },
              {
                key: 'changelog',
                label: (
                  <span>
                    <FileTextOutlined /> Changelog ({changelog.length})
                  </span>
                ),
                children: (
                  <Table
                    dataSource={changelog}
                    rowKey="id"
                    columns={[
                      {
                        title: 'Type',
                        dataIndex: 'artifact_type',
                        render: (type) => (
                          <Tag color={type === 'pr' ? 'blue' : 'green'}>
                            {type.toUpperCase()}
                          </Tag>
                        ),
                      },
                      {
                        title: 'URL',
                        dataIndex: 'artifact_url',
                        render: (url) =>
                          url ? (
                            <a href={url} target="_blank" rel="noopener noreferrer">
                              {url}
                            </a>
                          ) : (
                            'N/A'
                          ),
                      },
                      {
                        title: 'Identifier',
                        dataIndex: 'identifier',
                      },
                      {
                        title: 'Created At',
                        dataIndex: 'created_at',
                        render: (date) => new Date(date).toLocaleString(),
                      },
                    ]}
                    pagination={{ pageSize: 10 }}
                  />
                ),
              },
              {
                key: 'activity',
                label: 'Activity Breakdown',
                children: (
                  <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Card title="Agents Used">
                      <Space wrap>
                        {summary.agents_used.map((agent) => (
                          <Tag key={agent} color="blue" style={{ fontSize: '14px', padding: '4px 12px' }}>
                            {agent}
                          </Tag>
                        ))}
                      </Space>
                    </Card>
                    <Card title="Phases Completed">
                      <Space wrap>
                        {summary.phases_completed.map((phase) => (
                          <Tag key={phase} color="green" style={{ fontSize: '14px', padding: '4px 12px' }}>
                            {phase}
                          </Tag>
                        ))}
                      </Space>
                    </Card>
                  </Space>
                ),
              },
              {
                key: 'outputs',
                label: (
                  <span>
                    <CodeOutlined /> Structured Outputs ({outputs.length})
                  </span>
                ),
                children: (
                  <OutputsList 
                    outputs={outputs} 
                    emptyText="No structured outputs recorded yet. Run agents with output schemas to see results here."
                  />
                ),
              },
            ]}
          />
        </Card>
      </Space>
    </div>
  );
}

