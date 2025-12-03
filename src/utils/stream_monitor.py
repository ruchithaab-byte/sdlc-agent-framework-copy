"""
Stream monitoring utilities for tracking stream lifecycle and state.

Used to investigate hook execution issues with Vertex AI by monitoring
when streams open/close relative to hook execution.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass, field


@dataclass
class StreamEvent:
    """Represents a stream lifecycle event."""
    timestamp: float
    event_type: str  # 'open', 'close', 'read', 'write', 'error'
    stream_name: str  # 'stdin', 'stdout', 'stderr', 'message'
    details: Optional[Dict[str, Any]] = None


@dataclass
class StreamState:
    """Tracks the state of a stream."""
    name: str
    is_open: bool = False
    opened_at: Optional[float] = None
    closed_at: Optional[float] = None
    events: List[StreamEvent] = field(default_factory=list)
    bytes_read: int = 0
    bytes_written: int = 0


class StreamMonitor:
    """Monitors stream lifecycle and state for debugging hook execution."""
    
    def __init__(self):
        self.streams: Dict[str, StreamState] = {}
        self.events: List[StreamEvent] = []
        self.hook_events: List[Dict[str, Any]] = []
        self.message_events: List[Dict[str, Any]] = []
        self.start_time = time.time()
    
    def log_stream_event(
        self,
        stream_name: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a stream lifecycle event."""
        timestamp = time.time() - self.start_time
        
        event = StreamEvent(
            timestamp=timestamp,
            event_type=event_type,
            stream_name=stream_name,
            details=details or {}
        )
        
        self.events.append(event)
        
        # Update stream state
        if stream_name not in self.streams:
            self.streams[stream_name] = StreamState(name=stream_name)
        
        stream_state = self.streams[stream_name]
        stream_state.events.append(event)
        
        if event_type == 'open':
            stream_state.is_open = True
            stream_state.opened_at = timestamp
        elif event_type == 'close':
            stream_state.is_open = False
            stream_state.closed_at = timestamp
        elif event_type == 'read':
            stream_state.bytes_read += details.get('bytes', 0) if details else 0
        elif event_type == 'write':
            stream_state.bytes_written += details.get('bytes', 0) if details else 0
    
    def log_hook_event(
        self,
        hook_name: str,
        hook_type: str,  # 'attempted', 'executed', 'failed'
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a hook execution event."""
        timestamp = time.time() - self.start_time
        
        self.hook_events.append({
            "timestamp": timestamp,
            "hook_name": hook_name,
            "hook_type": hook_type,
            "details": details or {}
        })
    
    def log_message_event(
        self,
        message_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a message stream event."""
        timestamp = time.time() - self.start_time
        
        self.message_events.append({
            "timestamp": timestamp,
            "message_type": message_type,
            "details": details or {}
        })
    
    def get_stream_state(self, stream_name: str) -> Optional[StreamState]:
        """Get current state of a stream."""
        return self.streams.get(stream_name)
    
    def is_stream_open(self, stream_name: str) -> bool:
        """Check if a stream is currently open."""
        stream = self.streams.get(stream_name)
        return stream.is_open if stream else False
    
    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get a chronological timeline of all events."""
        timeline = []
        
        # Add stream events
        for event in self.events:
            timeline.append({
                "timestamp": event.timestamp,
                "type": "stream",
                "event": event.event_type,
                "stream": event.stream_name,
                "details": event.details
            })
        
        # Add hook events
        for event in self.hook_events:
            timeline.append({
                "timestamp": event["timestamp"],
                "type": "hook",
                "event": event["hook_type"],
                "hook": event["hook_name"],
                "details": event["details"]
            })
        
        # Add message events
        for event in self.message_events:
            timeline.append({
                "timestamp": event["timestamp"],
                "type": "message",
                "event": event["message_type"],
                "details": event["details"]
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return timeline
    
    def get_correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlation between stream events and hook execution."""
        analysis = {
            "streams_opened": [],
            "streams_closed": [],
            "hooks_attempted": [],
            "hooks_executed": [],
            "hooks_failed": [],
            "messages_received": [],
            "correlations": []
        }
        
        # Collect stream open/close events
        for event in self.events:
            if event.event_type == 'open':
                analysis["streams_opened"].append({
                    "timestamp": event.timestamp,
                    "stream": event.stream_name
                })
            elif event.event_type == 'close':
                analysis["streams_closed"].append({
                    "timestamp": event.timestamp,
                    "stream": event.stream_name
                })
        
        # Collect hook events
        for event in self.hook_events:
            if event["hook_type"] == "attempted":
                analysis["hooks_attempted"].append({
                    "timestamp": event["timestamp"],
                    "hook": event["hook_name"]
                })
            elif event["hook_type"] == "executed":
                analysis["hooks_executed"].append({
                    "timestamp": event["timestamp"],
                    "hook": event["hook_name"]
                })
            elif event["hook_type"] == "failed":
                analysis["hooks_failed"].append({
                    "timestamp": event["timestamp"],
                    "hook": event["hook_name"]
                })
        
        # Collect message events
        for event in self.message_events:
            analysis["messages_received"].append({
                "timestamp": event["timestamp"],
                "type": event["message_type"]
            })
        
        # Find correlations
        for hook_attempt in analysis["hooks_attempted"]:
            hook_time = hook_attempt["timestamp"]
            
            # Find closest stream close before hook attempt
            closes_before = [
                close for close in analysis["streams_closed"]
                if close["timestamp"] < hook_time
            ]
            closest_close = max(closes_before, key=lambda x: x["timestamp"]) if closes_before else None
            
            # Find closest stream open after hook attempt
            opens_after = [
                open_event for open_event in analysis["streams_opened"]
                if open_event["timestamp"] > hook_time
            ]
            closest_open = min(opens_after, key=lambda x: x["timestamp"]) if opens_after else None
            
            analysis["correlations"].append({
                "hook": hook_attempt["hook"],
                "hook_time": hook_time,
                "closest_close_before": closest_close,
                "closest_open_after": closest_open,
                "time_since_close": hook_time - closest_close["timestamp"] if closest_close else None,
                "time_until_open": closest_open["timestamp"] - hook_time if closest_open else None
            })
        
        return analysis
    
    def reset(self) -> None:
        """Reset all monitoring state."""
        self.streams.clear()
        self.events.clear()
        self.hook_events.clear()
        self.message_events.clear()
        self.start_time = time.time()


class StreamKeepAlive:
    """Wrapper to keep streams open during hook execution."""
    
    def __init__(self, monitor: StreamMonitor, keep_alive_duration: float = 5.0):
        self.monitor = monitor
        self.keep_alive_duration = keep_alive_duration
        self.original_close_methods = {}
    
    async def wrap_query(
        self,
        query_func,
        *args,
        **kwargs
    ) -> AsyncIterator[Any]:
        """Wrap query() function to keep streams open."""
        # Monitor stream state
        self.monitor.log_stream_event("query", "open", {"args": str(args)[:100]})
        
        try:
            # Execute query - handle both async function and direct async iterator
            if asyncio.iscoroutinefunction(query_func):
                message_stream = await query_func(*args, **kwargs)
            elif callable(query_func):
                message_stream = query_func(*args, **kwargs)
            else:
                message_stream = query_func
            
            # Collect all messages
            messages = []
            async for message in message_stream:
                messages.append(message)
                self.monitor.log_message_event("message_received", {
                    "message_type": type(message).__name__
                })
            
            # Keep stream "open" for hook execution window
            self.monitor.log_stream_event("query", "keep_alive_start")
            await asyncio.sleep(self.keep_alive_duration)
            self.monitor.log_stream_event("query", "keep_alive_end")
            
            # Yield messages
            for message in messages:
                yield message
                
        finally:
            self.monitor.log_stream_event("query", "close")
    
    def patch_stream_close(self, stream_obj, stream_name: str):
        """Patch a stream object to monitor close operations."""
        if stream_obj is None:
            return stream_obj
        
        original_close = getattr(stream_obj, 'close', None)
        if original_close is None:
            return stream_obj
        
        def monitored_close(*args, **kwargs):
            self.monitor.log_stream_event(stream_name, "close_attempted")
            # Don't actually close - keep it open
            self.monitor.log_stream_event(stream_name, "close_prevented")
            return None  # Don't call original close
        
        # Store original for restoration
        self.original_close_methods[stream_name] = original_close
        
        # Patch close method
        stream_obj.close = monitored_close
        
        return stream_obj


__all__ = ["StreamMonitor", "StreamKeepAlive", "StreamEvent", "StreamState"]

