import React from 'react';
import { Empty } from 'antd';

export default function LogPanel({ logs }) {
  return (
    <div
      className="log-panel"
      style={{
        height: '400px',
        overflowY: 'auto',
        backgroundColor: '#fafafa',
        padding: '12px',
        borderRadius: '4px',
        fontFamily: 'monospace',
        fontSize: '12px',
      }}
    >
      {logs.length === 0 ? (
        <Empty description="暂无日志 (No logs)" />
      ) : (
        <div>
          {logs.map((log, index) => (
            <div
              key={index}
              className="log-line"
              style={{
                padding: '4px 0',
                borderBottom: '1px solid #e8e8e8',
                color: log.includes('✓') ? '#52c41a' : 
                       log.includes('Error') || log.includes('错误') ? '#ff4d4f' :
                       log.includes('---') ? '#1890ff' : '#333',
              }}
            >
              {log}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
