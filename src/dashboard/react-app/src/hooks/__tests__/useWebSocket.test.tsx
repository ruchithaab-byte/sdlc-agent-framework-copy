import { renderHook, act, waitFor } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';
import WS from 'jest-websocket-mock';

describe('useWebSocket Hook Regression Tests', () => {
  let server: WS;
  const mockUrl = 'ws://localhost:8765';

  beforeEach(() => {
    server = new WS(mockUrl);
  });

  afterEach(() => {
    WS.clean();
  });

  test('should handle initial connection and receive initial data', async () => {
    const { result } = renderHook(() => useWebSocket());

    await server.connected;
    expect(result.current.isConnected).toBe(true);
    expect(result.current.error).toBe(null);

    // Send initial data
    const initialData = {
      type: 'initial_data',
      executions: [
        { id: '1', status: 'success', duration_ms: 100 },
        { id: '2', status: 'error', duration_ms: 200 }
      ]
    };

    act(() => {
      server.send(JSON.stringify(initialData));
    });

    await waitFor(() => {
      expect(result.current.events).toHaveLength(2);
      expect(result.current.events[0].id).toBe('2'); // Reversed order
    });
  });

  test('should handle new execution events', async () => {
    const { result } = renderHook(() => useWebSocket());
    await server.connected;

    const newExecution = {
      type: 'new_execution',
      data: { id: '3', status: 'success', duration_ms: 150 }
    };

    act(() => {
      server.send(JSON.stringify(newExecution));
    });

    await waitFor(() => {
      expect(result.current.events).toContainEqual(newExecution.data);
    });
  });

  test('should handle malformed messages without crashing', async () => {
    const { result } = renderHook(() => useWebSocket());
    await server.connected;

    act(() => {
      server.send('invalid json');
    });

    // Should not crash and maintain connection
    expect(result.current.isConnected).toBe(true);
    expect(result.current.events).toHaveLength(0);
  });

  test('should handle reconnection on disconnect', async () => {
    jest.useFakeTimers();
    const { result } = renderHook(() => useWebSocket());

    await server.connected;
    expect(result.current.isConnected).toBe(true);

    // Simulate disconnect
    server.close();

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });

    // Fast-forward reconnection delay
    jest.advanceTimersByTime(1000);

    // New server instance for reconnection
    const newServer = new WS(mockUrl);
    await newServer.connected;

    expect(result.current.isConnected).toBe(true);

    newServer.close();
    jest.useRealTimers();
  });

  test('should cleanup on unmount', async () => {
    const { result, unmount } = renderHook(() => useWebSocket());
    await server.connected;

    const closeSpy = jest.spyOn(WebSocket.prototype, 'close');

    unmount();

    expect(closeSpy).toHaveBeenCalled();
    closeSpy.mockRestore();
  });

  test('should limit events array to 1000 items', async () => {
    const { result } = renderHook(() => useWebSocket());
    await server.connected;

    // Send 1005 events
    for (let i = 0; i < 1005; i++) {
      act(() => {
        server.send(JSON.stringify({
          type: 'new_execution',
          data: { id: `event-${i}`, status: 'success' }
        }));
      });
    }

    await waitFor(() => {
      expect(result.current.events).toHaveLength(1000);
    });
  });
});