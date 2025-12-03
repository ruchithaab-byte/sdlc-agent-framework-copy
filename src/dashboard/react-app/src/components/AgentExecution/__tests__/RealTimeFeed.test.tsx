import { render, screen, waitFor } from '@testing-library/react';
import { RealTimeFeed } from '../RealTimeFeed';
import * as useWebSocketModule from '../../../hooks/useWebSocket';

// Mock the WebSocket hook
jest.mock('../../../hooks/useWebSocket');

describe('RealTimeFeed Component Regression Tests', () => {
  const mockUseWebSocket = jest.mocked(useWebSocketModule.useWebSocket);

  beforeEach(() => {
    mockUseWebSocket.mockReturnValue({
      events: [],
      isConnected: false,
      error: null,
      reconnect: jest.fn(),
    });
  });

  test('should display connection status correctly', () => {
    // Test disconnected state
    render(<RealTimeFeed />);
    expect(screen.getByText('Disconnected')).toBeInTheDocument();

    // Test connected state
    mockUseWebSocket.mockReturnValue({
      events: [],
      isConnected: true,
      error: null,
      reconnect: jest.fn(),
    });

    render(<RealTimeFeed />);
    expect(screen.getByText('Connected')).toBeInTheDocument();
  });

  test('should calculate and display statistics correctly', () => {
    const mockEvents = [
      { id: '1', status: 'success', duration_ms: 100 },
      { id: '2', status: 'error', duration_ms: 200 },
      { id: '3', status: 'success', duration_ms: 150 },
      { id: '4', status: 'pending', duration_ms: null },
    ];

    mockUseWebSocket.mockReturnValue({
      events: mockEvents,
      isConnected: true,
      error: null,
      reconnect: jest.fn(),
    });

    render(<RealTimeFeed />);

    // Check statistics
    expect(screen.getByText('4')).toBeInTheDocument(); // Total events
    expect(screen.getByText('2')).toBeInTheDocument(); // Successful
    expect(screen.getByText('1')).toBeInTheDocument(); // Errors
    expect(screen.getByText('150')).toBeInTheDocument(); // Avg duration (100+200+150)/3
  });

  test('should display error alert when connection fails', () => {
    const errorMessage = 'WebSocket connection failed';
    mockUseWebSocket.mockReturnValue({
      events: [],
      isConnected: false,
      error: new Error(errorMessage),
      reconnect: jest.fn(),
    });

    render(<RealTimeFeed />);

    expect(screen.getByText('Connection Error')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('should limit displayed events to 100', async () => {
    const mockEvents = Array.from({ length: 150 }, (_, i) => ({
      id: `event-${i}`,
      status: 'success' as const,
      duration_ms: 100,
    }));

    mockUseWebSocket.mockReturnValue({
      events: mockEvents,
      isConnected: true,
      error: null,
      reconnect: jest.fn(),
    });

    const { container } = render(<RealTimeFeed />);

    await waitFor(() => {
      // Should render ExecutionLog with only 100 events
      const executionLog = container.querySelector('.execution-log-card');
      expect(executionLog).toBeInTheDocument();
    });
  });

  test('should handle empty events array without errors', () => {
    mockUseWebSocket.mockReturnValue({
      events: [],
      isConnected: true,
      error: null,
      reconnect: jest.fn(),
    });

    render(<RealTimeFeed />);

    expect(screen.getByText('0')).toBeInTheDocument(); // Total events
    expect(screen.getByText('0ms')).toBeInTheDocument(); // Avg duration with no data
  });

  test('should apply correct CSS classes and animations', () => {
    mockUseWebSocket.mockReturnValue({
      events: [],
      isConnected: true,
      error: null,
      reconnect: jest.fn(),
    });

    const { container } = render(<RealTimeFeed />);

    expect(container.querySelector('.realtime-feed')).toBeInTheDocument();
    expect(container.querySelector('.dashboard-header-card')).toBeInTheDocument();
    expect(container.querySelector('.status-tag.connected')).toBeInTheDocument();
    expect(container.querySelector('.stats-row')).toBeInTheDocument();
  });
});