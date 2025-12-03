import { Card, Empty } from 'antd';
import { GitlabOutlined } from '@ant-design/icons';
import './SectionCard.css';

export function Git() {
  return (
    <Card className="section-card">
      <Empty
        image={<GitlabOutlined style={{ fontSize: 64, color: '#6366f1' }} />}
        description={
          <span style={{ color: '#94a3b8' }}>Git integration coming soon</span>
        }
      />
    </Card>
  );
}

