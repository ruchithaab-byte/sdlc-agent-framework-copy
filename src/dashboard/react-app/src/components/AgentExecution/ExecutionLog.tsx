import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { ExecutionEvent } from '../../types';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import './ExecutionLog.css';

interface ExecutionLogProps {
  events: ExecutionEvent[];
}

export function ExecutionLog({ events }: ExecutionLogProps) {
  const columns: ColumnsType<ExecutionEvent> = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string) => {
        const date = new Date(timestamp);
        return <span className="table-cell">{date.toLocaleString()}</span>;
      },
    },
    {
      title: 'Session',
      dataIndex: 'session_id',
      key: 'session_id',
      width: 200,
      ellipsis: true,
      render: (text: string) => <span className="table-cell">{text}</span>,
    },
    {
      title: 'Event',
      dataIndex: 'hook_event',
      key: 'hook_event',
      width: 150,
      render: (text: string) => <span className="table-cell">{text}</span>,
    },
    {
      title: 'Tool',
      dataIndex: 'tool_name',
      key: 'tool_name',
      width: 150,
      render: (tool: string) => <span className="table-cell">{tool || '-'}</span>,
    },
    {
      title: 'Agent',
      dataIndex: 'agent_name',
      key: 'agent_name',
      width: 150,
      render: (agent: string) => <span className="table-cell">{agent || '-'}</span>,
    },
    {
      title: 'Phase',
      dataIndex: 'phase',
      key: 'phase',
      width: 120,
      render: (phase: string) => <span className="table-cell">{phase || '-'}</span>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag
          icon={status === 'success' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
          color={status === 'success' ? 'success' : 'error'}
          className="status-tag"
        >
          {status}
        </Tag>
      ),
    },
    {
      title: 'Duration (ms)',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 120,
      render: (duration: number) => (
        <span className="table-cell">{duration ? `${duration}ms` : '-'}</span>
      ),
    },
  ];

  return (
    <div className="execution-log-table">
      <Table
        columns={columns}
        dataSource={events}
        rowKey={(record) => `${record.timestamp}-${record.session_id}-${record.tool_name || ''}`}
        pagination={{ pageSize: 50, showSizeChanger: true }}
        scroll={{ y: 600 }}
        size="small"
        className="animated-table"
      />
    </div>
  );
}

