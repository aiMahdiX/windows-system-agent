"""
Function Executor - Allows Ollama to directly call system functions
Facilitates safe execution of system-level operations through the AI model
"""

import json
import re
import logging
from typing import Dict, Any, Callable, Optional
from system_controller import SystemController
from tool_caller import ToolCaller
from state_manager import StateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FunctionExecutor:
    """Execute system functions requested by the AI model"""
    
    # Available functions that Ollama can call
    AVAILABLE_FUNCTIONS = {
        "open_application": {
            "description": "Open an application by name",
            "params": {"app_name": "string - name of application to open"},
            "example": '{"function": "open_application", "app_name": "notepad"}'
        },
        "set_timer": {
            "description": "Set a countdown timer",
            "params": {"minutes": "number - minutes", "seconds": "number - seconds (optional)", "timer_id": "string - timer name (optional)"},
            "example": '{"function": "set_timer", "minutes": 10}'
        },
        "get_timer_status": {
            "description": "Get status of a timer",
            "params": {"timer_id": "string - timer name (optional, default is 'default')"},
            "example": '{"function": "get_timer_status", "timer_id": "kitchen"}'
        },
        "cancel_timer": {
            "description": "Cancel a running timer",
            "params": {"timer_id": "string - timer name (optional)"},
            "example": '{"function": "cancel_timer", "timer_id": "default"}'
        },
        "toggle_bluetooth": {
            "description": "Turn Bluetooth on/off",
            "params": {"action": "string - 'on', 'off', or 'toggle'"},
            "example": '{"function": "toggle_bluetooth", "action": "on"}'
        },
        "toggle_wifi": {
            "description": "Turn Wi-Fi on/off",
            "params": {"action": "string - 'on', 'off', or 'toggle'"},
            "example": '{"function": "toggle_wifi", "action": "off"}'
        },
        "change_background": {
            "description": "Change desktop background color",
            "params": {"color": "string - color name (e.g., 'blue', 'red')"},
            "example": '{"function": "change_background", "color": "blue"}'
        },
        "set_brightness": {
            "description": "Set screen brightness",
            "params": {"level": "number - 0-100"},
            "example": '{"function": "set_brightness", "level": 80}'
        },
        "set_volume": {
            "description": "Set system volume to specific level (0-100) or by text",
            "params": {"level": "number - 0-100", "level_text": "string - 'low', 'mid', 'high'"},
            "example": '{"function": "set_volume", "level": 50} or {"function": "set_volume", "level_text": "mid"}'
        },
        "control_volume": {
            "description": "Control system volume",
            "params": {"action": "string - 'mute', 'unmute', 'increase', 'decrease'", "level": "number - optional volume level"},
            "example": '{"function": "control_volume", "action": "mute"}'
        },
        "lock_screen": {
            "description": "Lock the screen",
            "params": {},
            "example": '{"function": "lock_screen"}'
        },
        "sleep_system": {
            "description": "Put system to sleep",
            "params": {},
            "example": '{"function": "sleep_system"}'
        },
        "shutdown_system": {
            "description": "Shutdown the system",
            "params": {},
            "example": '{"function": "shutdown_system"}'
        },
        "restart_system": {
            "description": "Restart the system",
            "params": {},
            "example": '{"function": "restart_system"}'
        },
        "toggle_airplane_mode": {
            "description": "Turn Airplane Mode on/off",
            "params": {"action": "string - 'on', 'off', or 'toggle'"},
            "example": '{"function": "toggle_airplane_mode", "action": "on"}'
        },
        "open_system_settings": {
            "description": "Open Windows Settings for a specific category",
            "params": {"setting_type": "string - e.g., 'display', 'sound', 'network'"},
            "example": '{"function": "open_system_settings", "setting_type": "display"}'
        },
        "get_system_info": {
            "description": "Get detailed system information",
            "params": {},
            "example": '{"function": "get_system_info"}'
        }
    }
    
    @staticmethod
    def get_function_definitions() -> str:
        """Get function definitions as formatted string for Ollama"""
        definitions = "Available Functions:\n"
        definitions += "================\n\n"
        
        for func_name, func_info in FunctionExecutor.AVAILABLE_FUNCTIONS.items():
            definitions += f"Function: {func_name}\n"
            definitions += f"Description: {func_info['description']}\n"
            definitions += f"Parameters: {json.dumps(func_info['params'])}\n"
            definitions += f"Example: {func_info['example']}\n\n"
        
        return definitions
    
    @staticmethod
    def parse_function_call(response: str) -> Dict[str, Any]:
        """Parse function call from model response"""
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{[^{}]*"function"[^{}]*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return {}
    
    @staticmethod
    def execute_function(function_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function call and return result"""
        func_name = function_call.get("function", "")
        
        try:
            if func_name == "set_timer":
                minutes = int(function_call.get("minutes", 0))
                seconds = int(function_call.get("seconds", 0))
                timer_id = function_call.get("timer_id", "default")
                result = SystemController.set_timer(minutes, seconds, timer_id)
                return result
            
            elif func_name == "get_timer_status":
                timer_id = function_call.get("timer_id", "default")
                result = SystemController.get_timer_status(timer_id)
                return result
            
            elif func_name == "cancel_timer":
                timer_id = function_call.get("timer_id", "default")
                result = SystemController.cancel_timer(timer_id)
                return result
            
            elif func_name == "open_application":
                app_name = function_call.get("app_name", "")
                result = SystemController.open_application(app_name)
                return {
                    "status": "success" if result else "failed",
                    "message": f"Application '{app_name}' opened" if result else f"Could not open '{app_name}'",
                    "function": func_name
                }
            
            elif func_name == "toggle_bluetooth":
                action = function_call.get("action", "toggle").lower()
                enable = action == "on" if action != "toggle" else None
                result = SystemController.toggle_bluetooth(enable)
                return {
                    "status": "success" if result else "failed",
                    "message": f"Bluetooth turned {action}" if result else "Could not toggle Bluetooth",
                    "function": func_name
                }
            
            elif func_name == "toggle_wifi":
                action = function_call.get("action", "toggle").lower()
                enable = action == "on" if action != "toggle" else None
                result = SystemController.toggle_wifi(enable)
                return {
                    "status": "success" if result else "failed",
                    "message": f"Wi-Fi turned {action}" if result else "Could not toggle Wi-Fi",
                    "function": func_name
                }
            
            elif func_name == "change_background":
                # Check if it's a file path or color name
                background_input = function_call.get("color", function_call.get("image_path", "blue"))
                
                # Try to use it as file path first (if it looks like a path)
                if "\\" in background_input or "/" in background_input or background_input.endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    result = SystemController.change_background(image_path=background_input)
                else:
                    # It's a color name
                    hex_color = SystemController.convert_color_name_to_hex(background_input)
                    result = SystemController.change_background(color=hex_color)
                
                return {
                    "status": "success" if result else "failed",
                    "message": f"Background changed to {background_input}" if result else "Could not change background",
                    "function": func_name
                }
            
            elif func_name == "set_brightness":
                level = function_call.get("level", 50)
                result = SystemController.set_brightness(int(level))
                return {
                    "status": "success" if result else "failed",
                    "message": f"Brightness set to {level}%" if result else "Could not set brightness",
                    "function": func_name
                }
            
            elif func_name == "set_volume":
                level = function_call.get("level")
                level_text = function_call.get("level_text")
                result = SystemController.set_volume(level=level, level_text=level_text)
                return {
                    "status": result.get("status", "failed"),
                    "message": result.get("message", "Could not set volume"),
                    "volume": result.get("volume"),
                    "function": func_name
                }
            
            elif func_name == "control_volume":
                action = function_call.get("action", "mute").lower()
                level = function_call.get("level")
                result = SystemController.control_volume(action, level=level)
                return {
                    "status": result.get("status", "failed") if isinstance(result, dict) else ("success" if result else "failed"),
                    "message": result.get("message", "Could not control volume") if isinstance(result, dict) else ("Volume controlled" if result else "Could not control volume"),
                    "function": func_name
                }
            
            elif func_name == "lock_screen":
                result = SystemController.lock_screen()
                return {
                    "status": "success" if result else "failed",
                    "message": "Screen locked" if result else "Could not lock screen",
                    "function": func_name
                }
            
            elif func_name == "sleep_system":
                result = SystemController.sleep_system()
                return {
                    "status": "success" if result else "failed",
                    "message": "System going to sleep" if result else "Could not put system to sleep",
                    "function": func_name
                }
            
            elif func_name == "shutdown_system":
                result = SystemController.shutdown_system()
                return {
                    "status": "success" if result else "failed",
                    "message": "System shutting down" if result else "Could not shutdown system",
                    "function": func_name
                }
            
            elif func_name == "restart_system":
                result = SystemController.restart_system()
                return {
                    "status": "success" if result else "failed",
                    "message": "System restarting" if result else "Could not restart system",
                    "function": func_name
                }
            
            elif func_name == "toggle_airplane_mode":
                action = function_call.get("action", "toggle").lower()
                enable = action == "on" if action != "toggle" else None
                result = SystemController.toggle_airplane_mode(enable)
                return {
                    "status": "success" if result else "failed",
                    "message": f"Airplane mode turned {action}" if result else "Could not toggle airplane mode",
                    "function": func_name
                }
            
            elif func_name == "open_system_settings":
                setting_type = function_call.get("setting_type", "")
                result = SystemController.open_system_settings(setting_type)
                return {
                    "status": "success" if result else "failed",
                    "message": f"Opened {setting_type} settings" if result else f"Could not open {setting_type}",
                    "function": func_name
                }
            
            elif func_name == "get_system_info":
                info = SystemController.get_system_info()
                return {
                    "status": "success",
                    "data": info,
                    "function": func_name
                }
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown function: {func_name}",
                    "function": func_name
                }
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing {func_name}: {error_msg}")
            return {
                "status": "error",
                "message": f"Error executing function: {error_msg}",
                "function": func_name,
                "error": error_msg
            }
    
    # ============ NEW PHASE 1 METHODS ============
    
    @staticmethod
    def execute_with_tool_caller(
        function_call: Dict[str, Any],
        tool_caller: Optional[ToolCaller] = None
    ) -> Dict[str, Any]:
        """Execute function using ToolCaller with retry logic"""
        
        if tool_caller is None:
            tool_caller = ToolCaller(FunctionExecutor)
        
        func_name = function_call.get("function", "")
        params = function_call.get("params", {})
        
        logger.info(f"Executing with retry logic: {func_name}")
        
        # Execute with retry logic
        result = tool_caller.execute_tool(func_name, params)
        
        return {
            "status": "success" if result.success else "failed",
            "message": result.message,
            "function": func_name,
            "execution_time_ms": result.execution_time_ms,
            "attempt": result.attempt,
            "data": result.data
        }
    
    @staticmethod
    def batch_execute(
        function_calls: list,
        use_retry: bool = True,
        use_state_manager: bool = True
    ) -> list:
        """Execute multiple function calls"""
        
        results = []
        state_manager = StateManager() if use_state_manager else None
        tool_caller = ToolCaller(FunctionExecutor) if use_retry else None
        
        logger.info(f"Batch executing {len(function_calls)} function calls")
        
        for call in function_calls:
            if use_retry:
                result = FunctionExecutor.execute_with_tool_caller(call, tool_caller)
            else:
                result = FunctionExecutor.execute_function(call)
            
            # Store in state manager
            if state_manager:
                state_manager.add_tool_call(
                    function_name=call.get("function"),
                    params=call.get("params"),
                    status=result.get("status"),
                    result=result,
                    execution_time_ms=result.get("execution_time_ms", 0)
                )
            
            results.append(result)
        
        logger.info(f"Batch execution completed: {len(results)} results")
        return results
    
    @staticmethod
    def get_execution_statistics() -> Dict[str, Any]:
        """Get execution statistics from state manager"""
        state_manager = StateManager()
        return state_manager.get_tool_statistics()
    
    @staticmethod
    def get_function_history(limit: int = 50) -> list:
        """Get function execution history"""
        state_manager = StateManager()
        try:
            return state_manager.get_tool_calls(limit=limit)
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "function": "get_function_history"
            }
