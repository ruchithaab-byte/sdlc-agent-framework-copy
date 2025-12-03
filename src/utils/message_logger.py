"""
Message-level logging utility for agent execution.

Parses query() message stream and logs to database when hooks don't fire.
This is a fallback mechanism for Vertex AI backend where hooks may not work.
"""

from __future__ import annotations

import time
from typing import Any, AsyncIterator, Dict, Optional

from src.logging.execution_logger import ExecutionLogger


class MessageLogger:
    """Logs agent execution by parsing message stream."""
    
    def __init__(
        self,
        logger: Optional[ExecutionLogger] = None,
        user_email: Optional[str] = None,
        agent_name: Optional[str] = None,
        phase: Optional[str] = None
    ):
        """Initialize message logger.
        
        Args:
            logger: ExecutionLogger instance (creates new one if None)
            user_email: User email for logging (required if logger is None)
            agent_name: Name of the agent (e.g., "ArchGuard", "CodeCraft")
            phase: Phase of execution (e.g., "strategy", "build", "test")
        """
        self.logger = logger or ExecutionLogger(user_email=user_email)
        self.agent_name = agent_name
        self.phase = phase
        self.session_id: Optional[str] = None
        self.tool_use_tracker: Dict[str, Dict[str, Any]] = {}  # tool_use_id -> {tool_name, start_time, input_data}
        self.session_started = False
        self.session_ended = False
    
    def _extract_session_id(self, message: Any) -> Optional[str]:
        """Extract session_id from SystemMessage."""
        try:
            # Check if message has data attribute with session_id
            if hasattr(message, 'data') and isinstance(message.data, dict):
                return message.data.get('session_id')
            
            # Check if message has session_id attribute
            if hasattr(message, 'session_id'):
                return message.session_id
            
            # Try string representation parsing
            msg_str = str(message)
            if 'session_id' in msg_str:
                # Try to extract from string representation
                import re
                match = re.search(r"session_id['\"]?\s*[:=]\s*['\"]?([^'\",\s}]+)", msg_str)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return None
    
    def _is_system_message(self, message: Any) -> bool:
        """Check if message is a SystemMessage."""
        msg_str = str(message)
        return "SystemMessage" in msg_str or (hasattr(message, 'subtype') and message.subtype == 'init')
    
    def _is_tool_use_block(self, message: Any) -> bool:
        """Check if message is a ToolUseBlock."""
        msg_str = str(message)
        return "ToolUseBlock" in msg_str or (hasattr(message, 'name') and hasattr(message, 'input'))
    
    def _is_tool_result_block(self, message: Any) -> bool:
        """Check if message is a ToolResultBlock."""
        msg_str = str(message)
        return "ToolResultBlock" in msg_str or (hasattr(message, 'tool_use_id') and hasattr(message, 'content'))
    
    def _is_result_message(self, message: Any) -> bool:
        """Check if message is a ResultMessage (session end)."""
        msg_str = str(message)
        return "ResultMessage" in msg_str or (hasattr(message, 'subtype') and message.subtype == 'success')
    
    def _extract_tool_use_data(self, message: Any) -> Optional[Dict[str, Any]]:
        """Extract tool use data from ToolUseBlock."""
        try:
            # Try direct attribute access
            if hasattr(message, 'name') and hasattr(message, 'input'):
                tool_use_id = getattr(message, 'id', None) or getattr(message, 'tool_use_id', None)
                return {
                    "tool_name": message.name,
                    "tool_use_id": tool_use_id,
                    "input_data": message.input if hasattr(message, 'input') else {}
                }
            
            # Try parsing from string representation
            msg_str = str(message)
            import re
            
            # Extract tool name
            name_match = re.search(r"name=['\"]?([^'\",\s}]+)", msg_str)
            tool_name = name_match.group(1) if name_match else None
            
            # Extract tool_use_id
            id_match = re.search(r"id=['\"]?([^'\",\s}]+)", msg_str)
            tool_use_id = id_match.group(1) if id_match else None
            
            if tool_name:
                return {
                    "tool_name": tool_name,
                    "tool_use_id": tool_use_id,
                    "input_data": {}
                }
        except Exception as e:
            print(f"⚠️  Error extracting tool use data: {e}")
        return None
    
    def _extract_tool_result_data(self, message: Any) -> Optional[Dict[str, Any]]:
        """Extract tool result data from ToolResultBlock."""
        try:
            # Try direct attribute access
            if hasattr(message, 'tool_use_id'):
                return {
                    "tool_use_id": message.tool_use_id,
                    "content": getattr(message, 'content', None),
                    "is_error": getattr(message, 'is_error', False)
                }
            
            # Try parsing from string representation
            msg_str = str(message)
            import re
            
            # Extract tool_use_id
            id_match = re.search(r"tool_use_id=['\"]?([^'\",\s}]+)", msg_str)
            tool_use_id = id_match.group(1) if id_match else None
            
            # Check for error
            is_error = "is_error=True" in msg_str or "error" in msg_str.lower()
            
            if tool_use_id:
                return {
                    "tool_use_id": tool_use_id,
                    "content": None,
                    "is_error": is_error
                }
        except Exception as e:
            print(f"⚠️  Error extracting tool result data: {e}")
        return None
    
    async def log_message_stream(
        self,
        message_stream: AsyncIterator[Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process message stream and log to database.
        
        Args:
            message_stream: Async iterator of messages from query()
            session_id: Optional session_id (will be extracted if not provided)
        
        Returns:
            Dictionary with logging statistics
        """
        stats = {
            "messages_processed": 0,
            "session_start_logged": False,
            "session_end_logged": False,
            "tool_uses_logged": 0,
            "tool_results_logged": 0,
            "errors": []
        }
        
        async for message in message_stream:
            stats["messages_processed"] += 1
            
            try:
                # Extract session_id from SystemMessage
                if self._is_system_message(message):
                    extracted_session_id = self._extract_session_id(message)
                    if extracted_session_id:
                        self.session_id = extracted_session_id or session_id
                    
                    # Log SessionStart
                    if not self.session_started and self.session_id:
                        try:
                            self.logger.log_execution(
                                session_id=self.session_id,
                                hook_event="SessionStart",
                                agent_name=self.agent_name,
                                phase=self.phase,
                                metadata={"source": "message_logger", "message_type": "SystemMessage"}
                            )
                            self.session_started = True
                            stats["session_start_logged"] = True
                        except Exception as e:
                            stats["errors"].append(f"SessionStart logging error: {e}")
                
                # Handle ToolUseBlock
                elif self._is_tool_use_block(message):
                    tool_data = self._extract_tool_use_data(message)
                    if tool_data and self.session_id:
                        tool_use_id = tool_data.get("tool_use_id") or f"tool_{int(time.time() * 1000)}"
                        tool_name = tool_data.get("tool_name", "unknown")
                        
                        # Store for later matching with result
                        self.tool_use_tracker[tool_use_id] = {
                            "tool_name": tool_name,
                            "start_time": time.time(),
                            "input_data": tool_data.get("input_data", {})
                        }
                        
                        # Log PreToolUse
                        try:
                            self.logger.log_execution(
                                session_id=self.session_id,
                                hook_event="PreToolUse",
                                tool_name=tool_name,
                                agent_name=self.agent_name,
                                phase=self.phase,
                                input_data=tool_data.get("input_data"),
                                metadata={
                                    "tool_use_id": tool_use_id,
                                    "source": "message_logger"
                                }
                            )
                            stats["tool_uses_logged"] += 1
                        except Exception as e:
                            stats["errors"].append(f"PreToolUse logging error: {e}")
                
                # Handle ToolResultBlock
                elif self._is_tool_result_block(message):
                    result_data = self._extract_tool_result_data(message)
                    if result_data and self.session_id:
                        tool_use_id = result_data.get("tool_use_id")
                        
                        # Lookup tool info from tracker
                        tool_info = self.tool_use_tracker.get(tool_use_id, {})
                        tool_name = tool_info.get("tool_name", "unknown")
                        start_time = tool_info.get("start_time")
                        
                        # Calculate duration
                        duration_ms = None
                        if start_time:
                            duration_ms = int((time.time() - start_time) * 1000)
                        
                        is_error = result_data.get("is_error", False)
                        content = result_data.get("content")
                        
                        # Log PostToolUse
                        try:
                            self.logger.log_execution(
                                session_id=self.session_id,
                                hook_event="PostToolUse",
                                tool_name=tool_name,
                                agent_name=self.agent_name,
                                phase=self.phase,
                                status="error" if is_error else "success",
                                duration_ms=duration_ms,
                                input_data=tool_info.get("input_data"),
                                output_data={"content": content} if content else None,
                                error_message=str(content) if is_error else None,
                                metadata={
                                    "tool_use_id": tool_use_id,
                                    "source": "message_logger"
                                }
                            )
                            
                            # Update tool usage statistics
                            self.logger.update_tool_usage(
                                session_id=self.session_id,
                                tool_name=tool_name,
                                success=not is_error,
                                duration_ms=duration_ms or 0
                            )
                            
                            stats["tool_results_logged"] += 1
                            
                            # Remove from tracker
                            if tool_use_id in self.tool_use_tracker:
                                del self.tool_use_tracker[tool_use_id]
                        except Exception as e:
                            stats["errors"].append(f"PostToolUse logging error: {e}")
                
                # Handle ResultMessage (session end)
                elif self._is_result_message(message) and not self.session_ended:
                    if self.session_id:
                        try:
                            # Extract summary if available
                            summary = {}
                            if hasattr(message, 'usage'):
                                summary["usage"] = str(message.usage)
                            if hasattr(message, 'result'):
                                summary["result"] = str(message.result)[:500]  # Limit length
                            
                            self.logger.log_execution(
                                session_id=self.session_id,
                                hook_event="SessionEnd",
                                agent_name=self.agent_name,
                                phase=self.phase,
                                metadata={
                                    "source": "message_logger",
                                    "summary": summary
                                }
                            )
                            self.session_ended = True
                            stats["session_end_logged"] = True
                        except Exception as e:
                            stats["errors"].append(f"SessionEnd logging error: {e}")
            
            except Exception as e:
                stats["errors"].append(f"Message processing error: {e}")
        
        return stats


async def log_agent_execution(
    message_stream: AsyncIterator[Any],
    logger: Optional[ExecutionLogger] = None,
    user_email: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    phase: Optional[str] = None
) -> Dict[str, Any]:
    """Wrapper function to log agent execution from message stream.
    
    Args:
        message_stream: Async iterator of messages from query()
        logger: ExecutionLogger instance (creates new one if None)
        user_email: User email for logging (required if logger is None)
        session_id: Optional session_id (will be extracted if not provided)
        agent_name: Name of the agent (e.g., "ArchGuard", "CodeCraft")
        phase: Phase of execution (e.g., "strategy", "build", "test")
    
    Returns:
        Dictionary with logging statistics
    """
    message_logger = MessageLogger(
        logger=logger,
        user_email=user_email,
        agent_name=agent_name,
        phase=phase
    )
    return await message_logger.log_message_stream(message_stream, session_id=session_id)


__all__ = ["MessageLogger", "log_agent_execution"]

