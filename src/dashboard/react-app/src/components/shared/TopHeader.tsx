import { Tooltip, Switch, Dropdown, Button, Avatar } from 'antd';
import { LinkOutlined, BookOutlined, BugOutlined, DatabaseOutlined, SafetyOutlined, SunOutlined, MoonOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import type { MenuProps } from 'antd';
import './TopHeader.css';

const externalLinks = [
  {
    key: 'backstage',
    label: 'Backstage',
    icon: <LinkOutlined />,
    url: 'https://backstage.io',
  },
  {
    key: 'mintlify',
    label: 'Mintlify',
    icon: <BookOutlined />,
    url: 'https://mintlify.com',
  },
  {
    key: 'linear',
    label: 'Linear',
    icon: <BugOutlined />,
    url: 'https://linear.app',
  },
  {
    key: 'langfuse',
    label: 'Langfuse',
    icon: <DatabaseOutlined />,
    url: 'https://langfuse.com',
  },
  {
    key: 'kwalitee',
    label: 'Kwalitee',
    icon: <SafetyOutlined />,
    url: 'https://kwalitee.com',
  },
];

export function TopHeader() {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Helper function to strip @users.noreply.github.com suffix from email
  const formatEmailDisplay = (email?: string): string => {
    if (!email) return '';
    if (email.endsWith('@users.noreply.github.com')) {
      return email.replace('@users.noreply.github.com', '');
    }
    return email;
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'user-info',
      label: (
        <div style={{ padding: '4px 0' }}>
          <div style={{ fontWeight: 500 }}>{user?.display_name || formatEmailDisplay(user?.email)}</div>
          <div style={{ fontSize: '12px', color: '#8c8c8c' }}>{formatEmailDisplay(user?.email)}</div>
        </div>
      ),
      disabled: true,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      label: 'Logout',
      icon: <LogoutOutlined />,
      onClick: handleLogout,
    },
  ];

  return (
    <header className={`top-header ${theme}`}>
      <div className="header-container">
        <div className="header-logo-section">
          <img 
            src="/julley-logo.jpeg" 
            alt="Julley Logo" 
            className="header-logo-image"
          />
          <div className="header-banner">
            <span className="banner-text">Julley Agentic Coding Studio</span>
          </div>
        </div>
        <nav className="header-nav">
          {externalLinks.map((link) => (
            <Tooltip key={link.key} title={link.label} placement="bottom">
              <a
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="external-link"
              >
                <span className="nav-link-icon">{link.icon}</span>
                <span className="nav-link-text">{link.label}</span>
              </a>
            </Tooltip>
          ))}
          <div className="nav-divider" />
          <Tooltip title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'} placement="bottom">
            <div className="theme-toggle">
              <Switch
                checked={theme === 'dark'}
                onChange={toggleTheme}
                checkedChildren={<MoonOutlined />}
                unCheckedChildren={<SunOutlined />}
                className="theme-switch"
              />
            </div>
          </Tooltip>
          <div className="nav-divider" />
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button 
              type="text" 
              icon={<Avatar size="small" icon={<UserOutlined />} />}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                color: theme === 'dark' ? '#f1f5f9' : '#1e293b',
                padding: '12px 16px',
              }}
            >
              <span style={{ fontSize: '13px', fontWeight: 500 }}>
                {user?.display_name || formatEmailDisplay(user?.email)}
              </span>
            </Button>
          </Dropdown>
        </nav>
      </div>
    </header>
  );
}

