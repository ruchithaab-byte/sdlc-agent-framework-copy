import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag, Select, Space, Spin, Alert } from 'antd';
import {
  DollarOutlined,
  RiseOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { AgentCostSummary, AgentCostsResponse, CostTotals } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import './CostDashboard.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8766';

export function CostDashboard() {
  const { token } = useAuth();
  const [costsData, setCostsData] = useState<AgentCostsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<string>('today');

  const fetchCosts = async (selectedPeriod: string) => {
    if (!token) {
      setError('Authentication required');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/agents/costs?period=${selectedPeriod}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data: AgentCostsResponse = await response.json();
        setCostsData(data);
        setError(null);
      } else {
        throw new Error('Failed to fetch cost data');
      }
    } catch (err) {
      setError('Failed to load cost data');
      console.error('Error fetching costs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCosts(period);
  }, [period, token]);

  // Get status based on budget utilization
  const getStatus = (utilization: number | null) => {
    if (utilization === null) return { color: 'default', icon: null, text: 'No Budget' };
    if (utilization >= 100) return { color: 'error', icon: <ExclamationCircleOutlined />, text: 'Over Budget' };
    if (utilization >= 80) return { color: 'warning', icon: <WarningOutlined />, text: 'Warning' };
    return { color: 'success', icon: <CheckCircleOutlined />, text: 'OK' };
  };

  const columns: ColumnsType<AgentCostSummary> = [
    {
      title: 'Agent',
      dataIndex: 'agent_id',
      key: 'agent_id',
      render: (text: string) => (
        <span style={{ fontWeight: 500, textTransform: 'capitalize' }}>{text}</span>
      ),
    },
    {
      title: 'Executions',
      dataIndex: 'execution_count',
      key: 'execution_count',
      align: 'center',
      sorter: (a, b) => a.execution_count - b.execution_count,
    },
    {
      title: 'Total Cost',
      dataIndex: 'total_cost_usd',
      key: 'total_cost_usd',
      align: 'right',
      sorter: (a, b) => a.total_cost_usd - b.total_cost_usd,
      render: (value: number) => (
        <span style={{ fontFamily: 'monospace' }}>${value.toFixed(4)}</span>
      ),
    },
    {
      title: 'Budget',
      dataIndex: 'budget_usd',
      key: 'budget_usd',
      align: 'right',
      render: (value: number | null) => (
        <span style={{ fontFamily: 'monospace', color: value ? 'inherit' : '#999' }}>
          {value ? `$${value.toFixed(2)}` : '—'}
        </span>
      ),
    },
    {
      title: 'Usage',
      key: 'usage',
      width: 180,
      render: (_, record) => {
        if (!record.budget_utilization_percent) return <span style={{ color: '#999' }}>—</span>;
        const pct = Math.min(record.budget_utilization_percent, 100);
        const status = getStatus(record.budget_utilization_percent);
        return (
          <Progress
            percent={pct}
            size="small"
            status={status.color === 'error' ? 'exception' : status.color === 'warning' ? 'active' : 'success'}
            format={() => `${record.budget_utilization_percent?.toFixed(1)}%`}
          />
        );
      },
      sorter: (a, b) => (a.budget_utilization_percent ?? 0) - (b.budget_utilization_percent ?? 0),
    },
    {
      title: 'Status',
      key: 'status',
      align: 'center',
      render: (_, record) => {
        const status = getStatus(record.budget_utilization_percent);
        return (
          <Tag color={status.color as string} icon={status.icon}>
            {status.text}
          </Tag>
        );
      },
    },
    {
      title: 'Avg Cost',
      dataIndex: 'avg_cost_usd',
      key: 'avg_cost_usd',
      align: 'right',
      render: (value: number) => (
        <span style={{ fontFamily: 'monospace', fontSize: '12px', color: '#666' }}>
          ${value.toFixed(4)}
        </span>
      ),
    },
  ];

  const totals: CostTotals = costsData?.totals ?? {
    total_cost_usd: 0,
    total_budget_usd: 0,
    total_executions: 0,
    budget_utilization_percent: null,
  };

  const utilizationColor =
    (totals.budget_utilization_percent ?? 0) >= 80 ? '#ff4d4f' : '#52c41a';

  if (!token) {
    return (
      <Card className="cost-dashboard-card">
        <Alert
          message="Authentication Required"
          description="Please log in to view cost data."
          type="warning"
          showIcon
        />
      </Card>
    );
  }

  return (
    <Card
      className="cost-dashboard-card"
      title={
        <Space>
          <DollarOutlined />
          <span>Cost Dashboard</span>
        </Space>
      }
      extra={
        <Space>
          <Select
            value={period}
            onChange={setPeriod}
            style={{ width: 120 }}
            size="small"
            options={[
              { value: 'today', label: 'Today' },
              { value: 'week', label: 'This Week' },
              { value: 'month', label: 'This Month' },
              { value: 'all', label: 'All Time' },
            ]}
          />
          <a onClick={() => fetchCosts(period)}>
            <ReloadOutlined />
          </a>
        </Space>
      }
    >
      {loading ? (
        <div className="loading-container">
          <Spin size="large" />
          <p>Loading cost data...</p>
        </div>
      ) : error ? (
        <Alert
          title="Error"
          description={error}
          type="error"
          showIcon
          action={
            <a onClick={() => fetchCosts(period)}>
              <ReloadOutlined /> Retry
            </a>
          }
        />
      ) : (
        <>
          {/* Summary Statistics */}
          <Row gutter={[24, 24]} className="stats-row">
            <Col xs={24} sm={12} md={6}>
              <Card className="stat-card">
                <Statistic
                  title="Total Cost"
                  value={totals.total_cost_usd}
                  precision={4}
                  prefix={<DollarOutlined />}
                  styles={{ content: { color: utilizationColor } }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card className="stat-card">
                <Statistic
                  title="Total Budget"
                  value={totals.total_budget_usd}
                  precision={2}
                  prefix={<DollarOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card className="stat-card">
                <Statistic
                  title="Budget Utilization"
                  value={totals.budget_utilization_percent ?? 0}
                  precision={1}
                  suffix="%"
                  prefix={
                    (totals.budget_utilization_percent ?? 0) >= 80 ? (
                      <WarningOutlined />
                    ) : (
                      <RiseOutlined />
                    )
                  }
                  styles={{ content: { color: utilizationColor } }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card className="stat-card">
                <Statistic
                  title="Total Executions"
                  value={totals.total_executions}
                  prefix={<RiseOutlined />}
                />
              </Card>
            </Col>
          </Row>

          {/* Budget Utilization Bar */}
          <Card className="utilization-card" size="small">
            <div className="utilization-header">
              <span>Overall Budget Utilization</span>
              <span style={{ color: utilizationColor }}>
                ${totals.total_cost_usd.toFixed(4)} / ${totals.total_budget_usd.toFixed(2)}
              </span>
            </div>
            <Progress
              percent={Math.min(totals.budget_utilization_percent ?? 0, 100)}
              status={
                (totals.budget_utilization_percent ?? 0) >= 100
                  ? 'exception'
                  : (totals.budget_utilization_percent ?? 0) >= 80
                  ? 'active'
                  : 'success'
              }
              strokeColor={utilizationColor}
            />
          </Card>

          {/* Per-Agent Table */}
          <Table
            columns={columns}
            dataSource={costsData?.agents ?? []}
            rowKey="agent_id"
            pagination={false}
            size="small"
            className="costs-table"
          />
        </>
      )}
    </Card>
  );
}

export default CostDashboard;

