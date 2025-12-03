import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme, App as AntApp, Tabs } from 'antd';
import { ThunderboltOutlined, TeamOutlined, BarChartOutlined } from '@ant-design/icons';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ProtectedRoute } from './components/shared/ProtectedRoute';
import { Layout } from './components/shared/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { SummaryDashboard } from './pages/SummaryDashboard';
import { AgentManagementView } from './pages/AgentManagementView';
import { QuickStatsBar } from './components/shared/QuickStatsBar';
import type { QuickStats } from './components/shared/QuickStatsBar';
import { useWebSocket } from './hooks/useWebSocket';
import './index.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8766';

// Single Page Application Component
function SinglePageApp() {
  const [activeTab, setActiveTab] = useState('realtime');
  const { events, isConnected } = useWebSocket();
  const { token } = useAuth();
  const [quickStats, setQuickStats] = useState<QuickStats>({
    connected: false,
    activeAgents: 0,
    eventsToday: 0,
    budgetPercent: 0,
    totalCost: 0
  });

  // Calculate stats from WebSocket events + fetch cost data
  useEffect(() => {
    const fetchCostStats = async () => {
      if (!token) return;
      try {
        const response = await fetch(`${API_BASE_URL}/api/agents/costs?period=today`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          const totals = data.totals || {};
          setQuickStats(prev => ({
            ...prev,
            budgetPercent: totals.budget_utilization_percent || 0,
            totalCost: totals.total_cost_usd || 0
          }));
        }
      } catch (e) {
        console.error("Failed to fetch cost stats", e);
      }
    };

    fetchCostStats();
    // Refresh cost stats every minute
    const interval = setInterval(fetchCostStats, 60000);
    return () => clearInterval(interval);
  }, [token]);

  // Update real-time stats from events
  useEffect(() => {
    const activeAgents = new Set(events.map(e => e.agent_name)).size;
    setQuickStats(prev => ({
      ...prev,
      connected: isConnected,
      activeAgents,
      eventsToday: events.length // Assuming events array is resetted daily or we just show session events
    }));
  }, [events, isConnected]);

  const tabItems = [
    {
      key: 'realtime',
      label: (
        <span className="tab-label">
          <ThunderboltOutlined />
          Real-Time Feed
        </span>
      ),
      children: <Dashboard />,
    },
    {
      key: 'agents',
      label: (
        <span className="tab-label">
          <TeamOutlined />
          Agent Hub
        </span>
      ),
      children: <AgentManagementView />,
    },
    {
      key: 'analytics',
      label: (
        <span className="tab-label">
          <BarChartOutlined />
          Analytics
        </span>
      ),
      children: <SummaryDashboard />,
    },
  ];

  return (
    <div className={`app-container`}>
      <QuickStatsBar stats={quickStats} />
      
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        type="card"
        size="large"
        className="primary-navigation-tabs"
        tabBarGutter={8}
        style={{ marginTop: '24px' }}
      />
    </div>
  );
}

function AppContent() {
  const { theme: currentTheme } = useTheme();

  useEffect(() => {
    document.body.className = currentTheme;
  }, [currentTheme]);

  const darkTheme = {
    algorithm: theme.darkAlgorithm,
    token: {
      colorPrimary: '#6366f1',
      colorBgBase: '#0f172a',
      colorBgContainer: '#1e293b',
      colorBgElevated: '#334155',
      colorText: '#f1f5f9',
      colorTextSecondary: '#cbd5e1',
      colorBorder: '#334155',
      borderRadius: 8,
      wireframe: false,
    },
    components: {
      Card: {
        headerBg: '#1e293b',
        actionsBg: '#1e293b',
      },
      Table: {
        headerBg: '#1e293b',
        rowHoverBg: '#334155',
      },
      Menu: {
        itemHoverBg: '#334155',
        itemSelectedBg: '#475569',
      },
    },
  };

  const lightTheme = {
    algorithm: theme.defaultAlgorithm,
    token: {
      colorPrimary: '#6366f1',
      colorBgBase: '#ffffff',
      colorBgContainer: '#f8fafc',
      colorBgElevated: '#ffffff',
      colorText: '#1e293b',
      colorTextSecondary: '#64748b',
      colorBorder: '#e2e8f0',
      borderRadius: 8,
      wireframe: false,
    },
    components: {
      Card: {
        headerBg: '#ffffff',
        actionsBg: '#f8fafc',
      },
      Table: {
        headerBg: '#f8fafc',
        rowHoverBg: '#f1f5f9',
      },
      Menu: {
        itemHoverBg: '#f1f5f9',
        itemSelectedBg: '#e2e8f0',
      },
    },
  };

  return (
    <ConfigProvider theme={currentTheme === 'dark' ? darkTheme : lightTheme}>
      <AntApp>
        <BrowserRouter>
          <AuthProvider>
            <Routes>
              {/* Public route - Login page */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected single page application */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<SinglePageApp />} />
              </Route>
              
              {/* Catch all - redirect to login */}
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
