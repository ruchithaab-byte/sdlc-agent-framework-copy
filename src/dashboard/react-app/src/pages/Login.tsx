import { useState } from 'react';
import { Form, Input, Button, Card, Tabs, App } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, Navigate } from 'react-router-dom';

export function Login() {
  const [loginLoading, setLoginLoading] = useState(false);
  const [registerLoading, setRegisterLoading] = useState(false);
  const { login, register, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const { message } = App.useApp();

  // Show loading while checking authentication
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh' 
      }}>
        <div>Loading...</div>
      </div>
    );
  }

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onLogin = async (values: { email: string; password: string }) => {
    setLoginLoading(true);
    try {
      await login(values.email, values.password);
      message.success('Login successful!');
      navigate('/', { replace: true });
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setLoginLoading(false);
    }
  };

  const onRegister = async (values: { email: string; password: string; display_name?: string }) => {
    setRegisterLoading(true);
    try {
      await register(values.email, values.password, values.display_name);
      message.success('Registration successful!');
      navigate('/', { replace: true });
    } catch (error) {
      message.error(error instanceof Error ? error.message : 'Registration failed');
    } finally {
      setRegisterLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      padding: '20px'
    }}>
      <Card style={{ width: 400, maxWidth: '100%' }}>
        <h1 style={{ textAlign: 'center', marginBottom: 24 }}>SDLC Agent Framework</h1>
        
        <Tabs
          items={[
            {
              key: 'login',
              label: 'Login',
              children: (
                <Form
                  name="login"
                  onFinish={onLogin}
                  autoComplete="off"
                  layout="vertical"
                >
                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: 'Please input your email!' },
                      { type: 'email', message: 'Please enter a valid email!' }
                    ]}
                  >
                    <Input 
                      prefix={<MailOutlined />} 
                      placeholder="Email" 
                      size="large"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[{ required: true, message: 'Please input your password!' }]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password"
                      size="large"
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button 
                      type="primary" 
                      htmlType="submit" 
                      block 
                      size="large"
                      loading={loginLoading}
                      icon={<UserOutlined />}
                    >
                      Login
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
            {
              key: 'register',
              label: 'Register',
              children: (
                <Form
                  name="register"
                  onFinish={onRegister}
                  autoComplete="off"
                  layout="vertical"
                >
                  <Form.Item
                    name="email"
                    rules={[
                      { required: true, message: 'Please input your email!' },
                      { type: 'email', message: 'Please enter a valid email!' }
                    ]}
                  >
                    <Input 
                      prefix={<MailOutlined />} 
                      placeholder="Email" 
                      size="large"
                    />
                  </Form.Item>

                  <Form.Item
                    name="display_name"
                  >
                    <Input 
                      prefix={<UserOutlined />} 
                      placeholder="Display Name (optional)" 
                      size="large"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: 'Please input your password!' },
                      { min: 8, message: 'Password must be at least 8 characters!' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="Password (min 8 chars)"
                      size="large"
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button 
                      type="primary" 
                      htmlType="submit" 
                      block 
                      size="large"
                      loading={registerLoading}
                    >
                      Register
                    </Button>
                  </Form.Item>
                </Form>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}

