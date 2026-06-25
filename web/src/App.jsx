import React from 'react';
import { Layout } from 'antd';
import DetectionPanel from './components/DetectionPanel';
import './index.css';

const { Header, Content, Footer } = Layout;

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="!bg-gradient-to-r from-blue-600 to-blue-800">
        <div className="flex items-center justify-center h-full">
          <h1 className="text-white text-3xl font-bold">跌倒检测系统 (Fall Detection System)</h1>
        </div>
      </Header>
      <Content className="p-8 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <DetectionPanel />
        </div>
      </Content>
      <Footer className="text-center bg-gray-100">
        Fall Detection System © 2026. Powered by React, Ant Design & Tailwind CSS
      </Footer>
    </Layout>
  );
}

export default App;
