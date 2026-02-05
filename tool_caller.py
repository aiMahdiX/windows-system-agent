"""
Tool Caller - Advanced tool calling with retry logic and error handling
Handles function execution with retry mechanisms and comprehensive error management
"""

import json
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CallStatus(Enum):
    """Status of a tool call"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    TIMEOUT = "timeout"


@dataclass
class ToolCall:
    """Represents a tool call"""
    function: str
    params: Dict[str, Any]
    status: CallStatus = CallStatus.PENDING
    timestamp: str = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ToolCallResult:
    """Result of executing a tool call"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    function: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    attempt: int = 1


class ToolCaller:
    """Manages tool calling with retry logic and error handling"""
    
    def __init__(self, function_executor: Any = None):
        """
        Initialize ToolCaller
        
        Args:
            function_executor: FunctionExecutor instance for executing functions
        """
        self.function_executor = function_executor
        self.call_history: List[ToolCall] = []
        self.retry_config = {
            "max_attempts": 3,
            "backoff_factor": 1.5,
            "timeout": 30
        }
    
    def execute_tool(
        self,
        function: str,
        params: Dict[str, Any],
        max_attempts: int = None,
        timeout: int = None
    ) -> ToolCallResult:
        """
        Execute a tool with retry logic
        
        Args:
            function: Function name
            params: Function parameters
            max_attempts: Max retry attempts
            timeout: Execution timeout in seconds
            
        Returns:
            ToolCallResult with execution details
        """
        import time
        
        if max_attempts is None:
            max_attempts = self.retry_config["max_attempts"]
        
        if timeout is None:
            timeout = self.retry_config["timeout"]
        
        tool_call = ToolCall(
            function=function,
            params=params,
            max_attempts=max_attempts
        )
        
        start_time = time.time()
        
        while tool_call.attempts < max_attempts:
            tool_call.attempts += 1
            tool_call.status = CallStatus.EXECUTING if tool_call.attempts == 1 else CallStatus.RETRYING
            
            try:
                logger.info(f"Executing {function} (attempt {tool_call.attempts}/{max_attempts})")
                
                # Execute function
                if self.function_executor:
                    result = self.function_executor.execute_function({
                        "function": function,
                        **params
                    })
                else:
                    result = self._execute_directly(function, params)
                
                execution_time = (time.time() - start_time) * 1000
                
                tool_call.status = CallStatus.SUCCESS
                tool_call.result = result
                
                self.call_history.append(tool_call)
                
                logger.info(f"✓ {function} succeeded in {execution_time:.0f}ms")
                
                return ToolCallResult(
                    success=True,
                    message=result.get("message", "Success"),
                    data=result.get("data"),
                    function=function,
                    execution_time_ms=execution_time,
                    attempt=tool_call.attempts
                )
                
            except TimeoutError:
                tool_call.status = CallStatus.TIMEOUT
                tool_call.error = "Execution timeout"
                logger.warning(f"⏱ {function} timed out (attempt {tool_call.attempts})")
                
                if tool_call.attempts >= max_attempts:
                    break
                
                # Exponential backoff
                wait_time = self.retry_config["backoff_factor"] ** (tool_call.attempts - 1)
                logger.info(f"Retrying after {wait_time}s...")
                time.sleep(wait_time)
                
            except Exception as e:
                error_msg = str(e)
                tool_call.error = error_msg
                
                logger.warning(f"✗ {function} failed: {error_msg} (attempt {tool_call.attempts})")
                
                if tool_call.attempts >= max_attempts:
                    tool_call.status = CallStatus.FAILED
                    break
                
                # Exponential backoff before retry
                wait_time = self.retry_config["backoff_factor"] ** (tool_call.attempts - 1)
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        # Final failure
        execution_time = (time.time() - start_time) * 1000
        self.call_history.append(tool_call)
        
        logger.error(f"✗ {function} failed after {tool_call.attempts} attempts: {tool_call.error}")
        
        return ToolCallResult(
            success=False,
            message=f"Failed after {tool_call.attempts} attempts",
            error=tool_call.error,
            function=function,
            execution_time_ms=execution_time,
            attempt=tool_call.attempts
        )
    
    def _execute_directly(self, function: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback direct execution without function_executor"""
        return {
            "status": "pending",
            "message": f"Function {function} is pending execution",
            "function": function
        }
    
    def batch_execute(
        self,
        tools: List[Dict[str, Any]],
        parallel: bool = False
    ) -> List[ToolCallResult]:
        """
        Execute multiple tools
        
        Args:
            tools: List of {"function": name, "params": dict}
            parallel: Execute in parallel (requires threading/async)
            
        Returns:
            List of ToolCallResult
        """
        results = []
        
        if parallel:
            # For now, sequential execution
            # TODO: Implement parallel execution with threading
            logger.warning("Parallel execution not yet implemented, using sequential")
        
        for tool in tools:
            result = self.execute_tool(
                tool["function"],
                tool.get("params", {})
            )
            results.append(result)
        
        return results
    
    def get_call_history(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get execution history"""
        history = [
            {
                "function": call.function,
                "params": call.params,
                "status": call.status.value,
                "timestamp": call.timestamp,
                "attempts": call.attempts,
                "error": call.error,
                "result": call.result
            }
            for call in self.call_history
        ]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def clear_history(self):
        """Clear call history"""
        self.call_history.clear()
        logger.info("Call history cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.call_history:
            return {"total": 0}
        
        successful = sum(1 for call in self.call_history if call.status == CallStatus.SUCCESS)
        failed = sum(1 for call in self.call_history if call.status == CallStatus.FAILED)
        avg_attempts = sum(call.attempts for call in self.call_history) / len(self.call_history)
        
        return {
            "total": len(self.call_history),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self.call_history) if self.call_history else 0,
            "avg_attempts": avg_attempts,
            "functions": list(set(call.function for call in self.call_history))
        }
    
    def set_retry_config(self, max_attempts: int = None, backoff_factor: float = None, timeout: int = None):
        """Update retry configuration"""
        if max_attempts is not None:
            self.retry_config["max_attempts"] = max_attempts
        if backoff_factor is not None:
            self.retry_config["backoff_factor"] = backoff_factor
        if timeout is not None:
            self.retry_config["timeout"] = timeout
        
        logger.info(f"Retry config updated: {self.retry_config}")
