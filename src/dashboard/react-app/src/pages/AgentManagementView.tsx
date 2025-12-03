import { useState } from 'react';
import { Tabs } from 'antd';
import { TeamOutlined, DollarOutlined } from '@ant-design/icons';
import { AgentProfilesSection } from '../components/Agent';
import { CostDashboard } from '../components/Cost';

export function AgentManagementView() {
  const [activeTab, setActiveTab] = useState('profiles');

  return (
    <div className="agent-management-view" style={{ height: '100%' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        tabPosition="left"
        className="agent-tabs"
        style={{ height: '100%', background: 'transparent' }}
        items={[
          {
            key: 'profiles',
            label: (
              <span><TeamOutlined /> Agent Profiles</span>
            ),
            children: (
              <div style={{ height: '100%', overflowY: 'auto', paddingRight: '16px' }}>
                <AgentProfilesSection />
              </div>
            ),
          },
          {
            key: 'budget',
            label: (
              <span><DollarOutlined /> Budget & Costs</span>
            ),
            children: (
              <div style={{ height: '100%', overflowY: 'auto', paddingRight: '16px' }}>
                <CostDashboard />
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}

