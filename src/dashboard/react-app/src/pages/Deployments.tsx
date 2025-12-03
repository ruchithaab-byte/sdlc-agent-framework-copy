import { Card, Empty } from 'antd';
import { RocketOutlined } from '@ant-design/icons';
import './SectionCard.css';

export function Deployments() {
  return (
    <Card className="section-card">
      <Empty
        image={<RocketOutlined style={{ fontSize: 64, color: '#6366f1' }} />}
        description={
          <span style={{ color: '#94a3b8' }}>Deployment integration coming soon</span>
        }
      />
    </Card>
  );
}

