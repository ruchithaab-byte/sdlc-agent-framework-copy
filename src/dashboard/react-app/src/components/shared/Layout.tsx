import { Layout as AntLayout } from 'antd';
import { TopHeader } from './TopHeader';
import { Outlet } from 'react-router-dom';

const { Content } = AntLayout;

export function Layout() {
  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <TopHeader />
      <Content style={{ padding: 0 }}>
        <Outlet />
      </Content>
    </AntLayout>
  );
}

