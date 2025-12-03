import { useState, useMemo } from 'react';
import { Card, Collapse, Tag, Space, Typography, Button, Tooltip, Empty } from 'antd';
import {
  CodeOutlined,
  CopyOutlined,
  CheckOutlined,
  ExpandAltOutlined,
  CompressOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type { StructuredOutput } from '../../types';
import './StructuredOutputViewer.css';

const { Text, Paragraph } = Typography;

interface StructuredOutputViewerProps {
  output: StructuredOutput;
  defaultExpanded?: boolean;
}

interface JsonViewerProps {
  data: unknown;
  depth?: number;
  expanded?: boolean;
}

// Schema type badge colors
const schemaColors: Record<string, string> = {
  quality_review: 'cyan',
  security_scan: 'red',
  sprint_plan: 'purple',
  code_craft: 'blue',
  architecture_review: 'orange',
  incident_triage: 'volcano',
  cost_analysis: 'green',
};

// Recursive JSON viewer with collapsible nodes
function JsonViewer({ data, depth = 0, expanded = true }: JsonViewerProps) {
  const [isExpanded, setIsExpanded] = useState(expanded && depth < 2);

  if (data === null) {
    return <span className="json-null">null</span>;
  }

  if (data === undefined) {
    return <span className="json-undefined">undefined</span>;
  }

  if (typeof data === 'boolean') {
    return <span className="json-boolean">{data.toString()}</span>;
  }

  if (typeof data === 'number') {
    return <span className="json-number">{data}</span>;
  }

  if (typeof data === 'string') {
    // Check if it's a long string
    if (data.length > 100) {
      return (
        <Paragraph
          className="json-string"
          ellipsis={{ rows: 2, expandable: true, symbol: 'more' }}
        >
          "{data}"
        </Paragraph>
      );
    }
    return <span className="json-string">"{data}"</span>;
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return <span className="json-bracket">[]</span>;
    }

    return (
      <div className="json-array">
        <span
          className="json-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼' : '▶'}
        </span>
        <span className="json-bracket">[</span>
        <span className="json-count">{data.length} items</span>
        {isExpanded && (
          <div className="json-content" style={{ marginLeft: 16 }}>
            {data.map((item, index) => (
              <div key={index} className="json-item">
                <span className="json-index">{index}:</span>
                <JsonViewer data={item} depth={depth + 1} expanded={depth < 1} />
                {index < data.length - 1 && <span className="json-comma">,</span>}
              </div>
            ))}
          </div>
        )}
        <span className="json-bracket">]</span>
      </div>
    );
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data);
    if (entries.length === 0) {
      return <span className="json-bracket">{'{}'}</span>;
    }

    return (
      <div className="json-object">
        <span
          className="json-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '▼' : '▶'}
        </span>
        <span className="json-bracket">{'{'}</span>
        <span className="json-count">{entries.length} keys</span>
        {isExpanded && (
          <div className="json-content" style={{ marginLeft: 16 }}>
            {entries.map(([key, value], index) => (
              <div key={key} className="json-item">
                <span className="json-key">"{key}"</span>
                <span className="json-colon">: </span>
                <JsonViewer data={value} depth={depth + 1} expanded={depth < 1} />
                {index < entries.length - 1 && <span className="json-comma">,</span>}
              </div>
            ))}
          </div>
        )}
        <span className="json-bracket">{'}'}</span>
      </div>
    );
  }

  return <span>{String(data)}</span>;
}

export function StructuredOutputViewer({ output, defaultExpanded = false }: StructuredOutputViewerProps) {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'tree' | 'raw'>('tree');

  const jsonString = useMemo(() => {
    try {
      return JSON.stringify(output.structured_output, null, 2);
    } catch {
      return '{}';
    }
  }, [output.structured_output]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(jsonString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (!output.structured_output) {
    return (
      <Card className="output-viewer-card" size="small">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="No structured output available"
        />
      </Card>
    );
  }

  return (
    <Card
      className="output-viewer-card"
      size="small"
      title={
        <Space>
          <FileTextOutlined />
          <span>Structured Output</span>
          {output.output_schema && (
            <Tag color={schemaColors[output.output_schema] || 'default'}>
              {output.output_schema}
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space size="small">
          <Tooltip title={viewMode === 'tree' ? 'View raw JSON' : 'View tree'}>
            <Button
              size="small"
              icon={viewMode === 'tree' ? <CodeOutlined /> : <ExpandAltOutlined />}
              onClick={() => setViewMode(viewMode === 'tree' ? 'raw' : 'tree')}
            />
          </Tooltip>
          <Tooltip title={copied ? 'Copied!' : 'Copy JSON'}>
            <Button
              size="small"
              icon={copied ? <CheckOutlined /> : <CopyOutlined />}
              onClick={handleCopy}
            />
          </Tooltip>
        </Space>
      }
    >
      <div className="output-meta">
        <Text type="secondary" className="meta-item">
          Session: <code>{output.session_id.slice(0, 8)}...</code>
        </Text>
        <Text type="secondary" className="meta-item">
          {output.agent_id && (
            <>Agent: <Tag size="small">{output.agent_id}</Tag></>
          )}
        </Text>
        <Text type="secondary" className="meta-item">
          {new Date(output.created_at).toLocaleString()}
        </Text>
      </div>

      <div className="output-content">
        {viewMode === 'tree' ? (
          <div className="json-tree">
            <JsonViewer data={output.structured_output} expanded={defaultExpanded} />
          </div>
        ) : (
          <pre className="json-raw">{jsonString}</pre>
        )}
      </div>
    </Card>
  );
}

// Compact list view for multiple outputs
interface OutputsListProps {
  outputs: StructuredOutput[];
  emptyText?: string;
}

export function OutputsList({ outputs, emptyText = 'No outputs available' }: OutputsListProps) {
  if (outputs.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={emptyText}
      />
    );
  }

  return (
    <Collapse
      className="outputs-list"
      accordion
      items={outputs.map((output, index) => ({
        key: output.id || index,
        label: (
          <Space>
            {output.agent_id && (
              <Tag style={{ textTransform: 'capitalize' }}>{output.agent_id}</Tag>
            )}
            {output.output_schema && (
              <Tag color={schemaColors[output.output_schema] || 'default'}>
                {output.output_schema}
              </Tag>
            )}
            <Text type="secondary" style={{ fontSize: 12 }}>
              {new Date(output.created_at).toLocaleString()}
            </Text>
          </Space>
        ),
        children: <StructuredOutputViewer output={output} defaultExpanded />,
      }))}
    />
  );
}

export default StructuredOutputViewer;

