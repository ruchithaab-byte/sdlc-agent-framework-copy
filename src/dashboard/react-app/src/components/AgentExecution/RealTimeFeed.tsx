import { Card, Statistic, Row, Col, Tag, Alert } from 'antd';
import { useWebSocket } from '../../hooks/useWebSocket';
import { ExecutionLog } from './ExecutionLog';
import { WifiOutlined, DisconnectOutlined } from '@ant-design/icons';
import { useEffect, useState } from 'react';
import type { ExecutionEvent } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import './RealTimeFeed.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8766';

export function RealTimeFeed() {
  const { events, isConnected, error } = useWebSocket();
  const { token } = useAuth();
  const [recentEvents, setRecentEvents] = useState<ExecutionEvent[]>([]);
  const [apiCostData, setApiCostData] = useState<{ total_cost_usd: number }>({ total_cost_usd: 0 });

  useEffect(() => {
    setRecentEvents(events.slice(0, 100));
  }, [events]);

  // Fetch real cost data from API
  useEffect(() => {
    const fetchCostData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/agents/costs?period=today`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (response.ok) {
          const data = await response.json();
          setApiCostData(data.totals || { total_cost_usd: 0 });
        }
      } catch (e) {
        console.warn('Failed to fetch cost data:', e);
      }
    };

    fetchCostData();
    // Refresh cost data every 30 seconds
    const interval = setInterval(fetchCostData, 30000);
    return () => clearInterval(interval);
  }, [token]);

  const stats = {
    total: events.length,
    success: events.filter((e) => e.status === 'success').length,
    errors: events.filter((e) => e.status === 'error').length,
    avgDuration: events.length > 0
      ? Math.round(
          events
            .filter((e) => e.duration_ms)
            .reduce((sum, e) => sum + (e.duration_ms || 0), 0) /
            events.filter((e) => e.duration_ms).length
        )
      : 0,
    // Use API cost data instead of WebSocket events (which don't have cost data)
    totalCost: apiCostData.total_cost_usd || 0,
    budgetWarnings: events.filter((e) => e.budget_exceeded).length,
  };

  const statCards = [
    {
      title: 'Total Events',
      value: stats.total,
      color: '#6366f1',
      icon: '📊',
      delay: 0,
    },
    {
      title: 'Successful',
      value: stats.success,
      color: '#10b981',
      icon: '✅',
      delay: 0.1,
    },
    {
      title: 'Errors',
      value: stats.errors,
      color: '#ef4444',
      icon: '❌',
      delay: 0.2,
    },
    {
      title: 'Avg Duration',
      value: stats.avgDuration,
      suffix: 'ms',
      color: '#8b5cf6',
      icon: '⏱️',
      delay: 0.3,
    },
    {
      title: 'Total Cost',
      value: stats.totalCost,
      prefix: '$',
      precision: 4,
      color: '#059669',
      icon: '💰',
      delay: 0.4,
    },
    {
      title: 'Budget Warnings',
      value: stats.budgetWarnings,
      color: stats.budgetWarnings > 0 ? '#dc2626' : '#6b7280',
      icon: '⚠️',
      delay: 0.5,
    },
  ];

  return (
    <div className="realtime-feed">
      <Card className="dashboard-header-card">
        <div className="dashboard-header">
          <div className="header-content">
            <h1 className="dashboard-title">Agent Execution Dashboard</h1>
            <p className="dashboard-subtitle">Real-time monitoring of agent activities</p>
          </div>
          <div className="connection-status">
            {isConnected ? (
              <Tag 
                icon={<WifiOutlined />} 
                color="success"
                className="status-tag connected"
              >
                Connected
              </Tag>
            ) : (
              <Tag 
                icon={<DisconnectOutlined />} 
                color="error"
                className="status-tag disconnected"
              >
                Disconnected
              </Tag>
            )}
          </div>
        </div>

        {error && (
          <Alert
            title="Connection Error"
            description={error.message}
            type="error"
            closable
            className="error-alert"
            style={{ marginBottom: '24px', animation: 'slideUp 0.4s ease-out' }}
          />
        )}

        <Row gutter={[16, 16]} className="stats-row">
          {statCards.map((stat) => (
            <Col xs={24} sm={12} md={6} lg={4} key={stat.title}>
              <Card 
                className="stat-card"
                style={{ 
                  animationDelay: `${stat.delay}s`,
                  borderLeft: `3px solid ${stat.color}`,
                }}
              >
                <div className="stat-icon" style={{ color: stat.color }}>
                  {stat.icon}
                </div>
                <Statistic
                  title={stat.title}
                  value={stat.value}
                  suffix={stat.suffix}
                  prefix={stat.prefix}
                  precision={stat.precision}
                  styles={{ 
                    content: { 
                      color: stat.color,
                      fontSize: '24px',
                      fontWeight: 600,
                    }
                  }}
                  className="statistic-animated"
                />
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      <Card 
        title={<span className="card-title">Execution Log</span>}
        className="execution-log-card"
        style={{ animationDelay: '0.4s' }}
      >
        <ExecutionLog events={recentEvents} />
      </Card>
    </div>
  );
}

