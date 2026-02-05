import requests
import json
import re
import os
import logging
from typing import Dict, Any, List, Optional, Generator
from datetime import datetime
from schema_validator import SchemaValidator
from tool_caller import ToolCaller
from streaming_handler import StreamingHandler, StreamClient
from state_manager import StateManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaAgent:
    """Agent that communicates with Ollama AI model"""
    
    def __init__(self, model_name: str = None, base_url: str = "http://localhost:11434", use_streaming: bool = False):
        self.base_url = base_url
        self.conversation_history = []
        self.available_models = []  # Cache for available models
        self.config_file = "config.json"
        self.use_streaming = use_streaming
        
        # Initialize components
        self.schema_validator = SchemaValidator()
        self.tool_caller = ToolCaller()
        self.streaming_handler = StreamingHandler(base_url)
        self.stream_client = StreamClient(base_url)
        self.state_manager = StateManager()
        
        # Load model from config or use default
        if model_name:
            self.model_name = model_name
        else:
            self.model_name = self._load_model_from_config() or "mistral"
        
        logger.info(f"OllamaAgent initialized with model: {self.model_name}")
    
    def _extract_delay(self, user_input: str) -> Dict[str, Any]:
        """Extract delay information from user input"""
        # Pattern to match: "after X seconds/minutes/hours" or "in X seconds/minutes/hours"
        pattern = r'\b(after|in)\s+(\d+)\s+(second|minute|hour)s?'
        match = re.search(pattern, user_input, re.IGNORECASE)
        
        if match:
            number = int(match.group(2))
            unit = match.group(3).lower()
            
            # Convert to seconds
            if "second" in unit:
                delay_seconds = number
            elif "minute" in unit:
                delay_seconds = number * 60
            elif "hour" in unit:
                delay_seconds = number * 3600
            else:
                delay_seconds = 0
            
            # Format display string
            if delay_seconds >= 3600:
                hours = delay_seconds // 3600
                delay_display = f"{hours} hour{'s' if hours > 1 else ''}"
            elif delay_seconds >= 60:
                minutes = delay_seconds // 60
                delay_display = f"{minutes} minute{'s' if minutes > 1 else ''}"
            else:
                delay_display = f"{delay_seconds} second{'s' if delay_seconds > 1 else ''}"
            
            # Remove the delay part from input to get the clean command
            clean_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE).strip()
            
            return {
                "has_delay": True,
                "delay_seconds": delay_seconds,
                "delay_display": delay_display,
                "clean_input": clean_input
            }
        
        return {"has_delay": False, "delay_seconds": 0, "clean_input": user_input, "delay_display": ""}
    
    def _load_model_from_config(self) -> str:
        """Load the last used model from config.json"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("ollama", {}).get("model", "mistral")
        except Exception as e:
            print(f"Error loading model from config: {e}")
        return "mistral"
    
    def _save_model_to_config(self, model_name: str) -> bool:
        """Save the selected model to config.json"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if "ollama" not in config:
                config["ollama"] = {}
            
            config["ollama"]["model"] = model_name
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving model to config: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Fetch list of available models from Ollama"""
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            models = data.get("models", [])
            
            # Extract model names
            model_names = [model.get("name", "") for model in models if model.get("name")]
            self.available_models = sorted(model_names)
            return self.available_models
            
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def set_model(self, model_name: str) -> bool:
        """Switch to a different model"""
        # Verify model exists in available models
        if not self.available_models:
            self.get_available_models()
        
        if model_name in self.available_models or not self.available_models:
            self.model_name = model_name
            self.conversation_history = []  # Clear history when switching models
            self._save_model_to_config(model_name)  # Save preference to config
            return True
        return False
        
    def send_request(self, prompt: str) -> str:
        """Send request to Ollama and get response"""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
                "top_p": 0.9,
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve)"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def execute_function(self, user_input: str) -> Dict[str, Any]:
        """Use Ollama to understand the user's intent and return a function call"""
        from function_executor import FunctionExecutor
        from system_controller import SystemController
        
        # First, check if this is a delayed/scheduled command
        delay_info = self._extract_delay(user_input)
        if delay_info["has_delay"]:
            # Remove the delay part from the command
            clean_input = delay_info["clean_input"]
            delay_seconds = delay_info["delay_seconds"]
            
            # Recursively process the cleaned command without delay
            result = self.execute_function(clean_input)
            
            # If it's a function call, schedule it instead of executing immediately
            if result.get("status") == "success" and "function" in result:
                # Schedule the function to run after delay
                return {
                    "status": "success",
                    "message": f"⏱️ Will execute in {delay_info['delay_display']}",
                    "scheduled": True,
                    "delay": delay_seconds,
                    "original_result": result
                }
            return result
        
        # Get available functions
        function_defs = FunctionExecutor.get_function_definitions()
        
        system_prompt = f"""You are an intelligent OS assistant with access to system functions.
You understand English commands.

{function_defs}

User Command: "{user_input}"

IMPORTANT INSTRUCTIONS:

1. For "set_volume" or "control_volume" functions:
   - User says "set volume to 50" → {{"function": "set_volume", "level": 50}}
   - User says "set volume to middle" → {{"function": "set_volume", "level_text": "mid"}}
   - User says "set volume low" → {{"function": "set_volume", "level_text": "low"}}
   - User says "set volume high" → {{"function": "set_volume", "level_text": "high"}}
   - User says "mute volume" → {{"function": "control_volume", "action": "mute"}}
   - User says "unmute volume" → {{"function": "control_volume", "action": "unmute"}}

2. For "set_timer" function:
   - If the user says "set timer for 10 minutes", respond with {{"function": "set_timer", "minutes": 10}}
   - If the user says "set timer for 30 seconds", respond with {{"function": "set_timer", "seconds": 30}}
   - You can optionally add a timer_id: {{"function": "set_timer", "minutes": 10, "timer_id": "kitchen"}}

3. For "change_background" function:
   - If the user provides a file path (contains backslash \\ or forward slash /), use it as "image_path"
   - If the user provides a color name (blue, red, green, etc.), use it as "color"

Decide if the user is asking for a system function or just having a conversation:

1. If it's a clear system command, respond with JSON:
{{"function": "function_name", "param1": "value1"}}

2. If it's a question or general conversation, respond with:
{{"type": "chat", "response": "Your conversational response here"}}

Examples:
- "set volume to 50" → {{"function": "set_volume", "level": 50}}
- "mute volume" → {{"function": "control_volume", "action": "mute"}}
- "open notepad" → {{"function": "open_application", "app_name": "notepad"}}
- "set timer for 10 minutes" → {{"function": "set_timer", "minutes": 10}}
- "change background to blue" → {{"function": "change_background", "color": "blue"}}

Respond only with JSON, no other text."""
        
        response = self.send_request(system_prompt)
        
        # Try to parse JSON response
        try:
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                # Check if this is a chat response
                if parsed.get("type") == "chat":
                    return {
                        "status": "success",
                        "message": parsed.get("response", "I'm here to help!"),
                        "is_chat": True
                    }
                
                # Check if this is a function call
                if parsed.get("function"):
                    function_call = parsed
                    result = FunctionExecutor.execute_function(function_call)
                    return result
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # If we can't parse, return a default error that will trigger chat fallback
        return {
            "status": "error",
            "message": "Could not understand the command.",
            "raw_response": response
        }
    
    def parse_command(self, user_input: str) -> Dict[str, Any]:
        """Parse user input to understand the intent and extract parameters"""
        
        system_prompt = """You are an intelligent OS assistant.
Users give you natural language commands and you must interpret them.

Possible commands:
1. Change background - examples: "change background to blue", "set wallpaper to red"
2. Change brightness - examples: "set brightness to 80", "make screen bright"
3. Control volume - examples: "mute volume", "increase volume", "lower sound"
4. Open application - examples: "open notepad", "launch calculator"
5. Change settings - examples: "turn on Wi-Fi", "disable Bluetooth"
6. Show system info - examples: "show system information", "what's my computer specs"

For command "{user_input}", respond with JSON:
{{
    "action": "action_name",
    "parameter1": "value1",
    "parameter2": "value2",
    "confidence": 0-100,
    "explanation": "Brief explanation"
}}"""
        
        response = self.send_request(system_prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return {
            "action": "unknown",
            "confidence": 0,
            "explanation": response
        }
    
    def chat(self, user_message: str) -> str:
        """Chat with the agent"""
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Create context from history
        context = "Conversation history:\n"
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            context += f"{role}: {msg['content']}\n"
        
        prompt = f"""{context}

Assistant (provide a short and helpful response):"""
        
        response = self.send_request(prompt)
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    # ============ NEW PHASE 1 METHODS ============
    
    def send_request_streaming(
        self,
        prompt: str,
        on_token: Optional[callable] = None,
        on_complete: Optional[callable] = None
    ) -> str:
        """Send request with streaming support"""
        logger.info(f"Streaming request with model: {self.model_name}")
        
        full_response = []
        
        def token_handler(token: str):
            full_response.append(token)
            if on_token:
                on_token(token)
        
        def complete_handler(text: str):
            if on_complete:
                on_complete(text)
        
        # Use streaming handler
        for token in self.streaming_handler.stream_generate(
            self.model_name,
            prompt,
            on_token=token_handler,
            on_complete=complete_handler
        ):
            pass
        
        return "".join(full_response)
    
    def execute_function_with_schema(self, user_input: str, schema_name: str = "tool_call") -> Dict[str, Any]:
        """Execute function with JSON schema validation"""
        from function_executor import FunctionExecutor
        
        # Check for delays first
        delay_info = self._extract_delay(user_input)
        if delay_info["has_delay"]:
            clean_input = delay_info["clean_input"]
            delay_seconds = delay_info["delay_seconds"]
            
            # Recursively process cleaned command
            result = self.execute_function_with_schema(clean_input, schema_name)
            
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "message": f"⏱️ Will execute in {delay_info['delay_display']}",
                    "scheduled": True,
                    "delay": delay_seconds,
                    "original_result": result
                }
            return result
        
        # Get function definitions and build prompt with schema
        function_defs = FunctionExecutor.get_function_definitions()
        schema_prompt = self.schema_validator.create_schema_prompt([schema_name, "response"])
        
        system_prompt = f"""You are an intelligent OS assistant with access to system functions.

{function_defs}

{schema_prompt}

User Command: "{user_input}"

IMPORTANT: Always respond with valid JSON matching the tool_call schema.
Only respond with JSON, no markdown or other text."""
        
        # Use streaming if enabled
        if self.use_streaming:
            response = self.send_request_streaming(system_prompt)
        else:
            response = self.send_request(system_prompt)
        
        # Validate response with schema
        is_valid, error, cleaned_data = self.schema_validator.parse_and_validate(
            response,
            schema_name,
            strict=False
        )
        
        if not is_valid:
            logger.warning(f"Schema validation failed: {error}")
            # Try to suggest fix
            try:
                data = json.loads(response)
                fixed_data = self.schema_validator.suggest_fix(data, schema_name)
                is_valid, error, cleaned_data = self.schema_validator.validate(fixed_data, schema_name)
            except:
                pass
        
        if not is_valid:
            logger.error(f"Could not validate response: {error}")
            return {
                "status": "error",
                "message": "Could not understand the command",
                "error": error
            }
        
        # Execute the validated function call
        if cleaned_data.get("function"):
            result = FunctionExecutor.execute_function(cleaned_data)
            
            # Store in state manager
            self.state_manager.add_conversation(
                user_input=user_input,
                model_response=json.dumps(cleaned_data),
                model_used=self.model_name,
                function_called=cleaned_data.get("function"),
                function_params=cleaned_data.get("params"),
                execution_status=result.get("status")
            )
            
            return result
        
        return {
            "status": "error",
            "message": "No function found in response"
        }
    
    def get_conversation_from_state(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history from state manager"""
        return self.state_manager.get_conversation_history(limit=limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics from state manager"""
        return self.state_manager.get_statistics()
    
    def export_conversation_state(self, export_path: str = "export.json") -> str:
        """Export all conversation state"""
        return self.state_manager.export_data(export_path)
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get tool execution statistics"""
        return self.state_manager.get_tool_statistics()
