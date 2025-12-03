import { Row, Col, Statistic, Badge } from 'antd';
import './QuickStatsBar.css';

export interface QuickStats {
  connected: boolean;
  activeAgents: number;
  eventsToday: number;
  budgetPercent: number;
  totalCost: number;
}

interface QuickStatsBarProps {
  stats: QuickStats;
}

export function QuickStatsBar({ stats }: QuickStatsBarProps) {
  return (
    <div className="quick-stats-bar">
      <Row gutter={24} align="middle" style={{ width: '100%', maxWidth: '1600px', margin: '0 auto' }}>
        <Col xs={24} sm={4} md={3}>
          <div className="connection-status-container">
            <Badge status={stats.connected ? 'success' : 'error'} dot style={{ marginRight: 8 }} />
            <span className={`connection-label ${stats.connected ? 'connected' : 'disconnected'}`}>
              {stats.connected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </Col>
        
        <Col xs={12} sm={5} md={5}>
          <Statistic 
            title="Active Agents" 
            value={stats.activeAgents} 
            styles={{ content: { fontSize: '18px', fontWeight: 600 } }}
            className="quick-stat"
          />
        </Col>
        
        <Col xs={12} sm={5} md={5}>
          <Statistic 
            title="Events Today" 
            value={stats.eventsToday} 
            styles={{ content: { fontSize: '18px', fontWeight: 600 } }}
            className="quick-stat"
          />
        </Col>
        
        <Col xs={12} sm={5} md={5}>
          <Statistic 
            title="Total Cost" 
            value={stats.totalCost} 
            precision={2}
            prefix="$"
            styles={{ content: { fontSize: '18px', fontWeight: 600 } }}
            className="quick-stat"
          />
        </Col>

        <Col xs={12} sm={5} md={6}>
          <Statistic 
            title="Budget Used" 
            value={stats.budgetPercent} 
            precision={1}
            suffix="%" 
            styles={{ 
              content: {
                fontSize: '18px',
                fontWeight: 600,
                color: stats.budgetPercent >= 100 ? '#ff4d4f' : stats.budgetPercent >= 80 ? '#faad14' : '#52c41a'
              }
            }}
            className="quick-stat"
          />
        </Col>
      </Row>
    </div>
  );
}

