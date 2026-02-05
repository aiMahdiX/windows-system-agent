"""
Streaming Handler - Handles streaming responses from Ollama
Processes real-time streaming responses from the Ollama AI model
"""

import requests
import json
import logging
from typing import Generator, Optional, Callable, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StreamingHandler:
    """Handles streaming responses from Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.stream_active = False
    
    def stream_generate(
        self,
        model: str,
        prompt: str,
        on_token: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream generation from Ollama with callbacks
        
        Args:
            model: Model name
            prompt: Input prompt
            on_token: Callback for each token (receives token string)
            on_complete: Callback on completion (receives full response)
            on_error: Callback on error (receives error message)
            **kwargs: Additional parameters for Ollama (temperature, top_k, etc)
            
        Yields:
            Each token as it arrives
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            **kwargs
        }
        
        full_response = []
        self.stream_active = True
        
        try:
            logger.info(f"Starting stream for model: {model}")
            
            response = requests.post(
                url,
                json=payload,
                stream=True,
                timeout=300  # 5 minute timeout for streaming
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if not self.stream_active:
                    break
                
                if line:
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        
                        if token:
                            full_response.append(token)
                            
                            # Call token callback
                            if on_token:
                                on_token(token)
                            
                            # Yield token
                            yield token
                        
                        # Check if done
                        if chunk.get("done", False):
                            break
                            
                    except json.JSONDecodeError as e:
                        error_msg = f"JSON decode error: {str(e)}"
                        logger.error(error_msg)
                        if on_error:
                            on_error(error_msg)
            
            # Call completion callback
            full_text = "".join(full_response)
            if on_complete:
                on_complete(full_text)
            
            logger.info(f"Stream completed. Response length: {len(full_text)}")
            
        except requests.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            logger.error(error_msg)
            if on_error:
                on_error(error_msg)
        
        finally:
            self.stream_active = False
    
    def stream_generate_json(
        self,
        model: str,
        prompt: str,
        on_json_chunk: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Stream generation and parse as JSON
        
        Args:
            model: Model name
            prompt: Input prompt with JSON schema instruction
            on_json_chunk: Callback when complete JSON object is parsed
            **kwargs: Additional Ollama parameters
            
        Returns:
            Complete parsed JSON object or None if parsing failed
        """
        buffer = ""
        complete_json = None
        
        def on_token(token: str):
            nonlocal buffer, complete_json
            buffer += token
            
            # Try to parse complete JSON objects in buffer
            try:
                # Look for complete JSON object
                import re
                json_match = re.search(r'\{[^{}]*\}', buffer)
                if json_match:
                    json_str = json_match.group(0)
                    obj = json.loads(json_str)
                    complete_json = obj
                    
                    if on_json_chunk:
                        on_json_chunk(obj)
                    
                    logger.debug(f"Parsed JSON chunk: {obj}")
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Consume stream
        response_text = ""
        for token in self.stream_generate(
            model,
            prompt,
            on_token=on_token,
            **kwargs
        ):
            response_text += token
        
        # Final attempt to parse complete JSON
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                complete_json = json.loads(json_match.group(0))
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return complete_json
    
    def stop_stream(self):
        """Stop active stream"""
        self.stream_active = False
        logger.info("Stream stopped")


class StreamBuffer:
    """Buffer for accumulating stream tokens with callbacks"""
    
    def __init__(self, callback_interval: int = 5):
        """
        Initialize buffer
        
        Args:
            callback_interval: Call on_buffer_full after N tokens
        """
        self.buffer = []
        self.callback_interval = callback_interval
        self.on_buffer_full = None
        self.on_complete = None
    
    def add_token(self, token: str):
        """Add token to buffer"""
        self.buffer.append(token)
        
        if len(self.buffer) >= self.callback_interval and self.on_buffer_full:
            chunk = "".join(self.buffer)
            self.on_buffer_full(chunk)
            self.buffer.clear()
    
    def flush(self):
        """Flush remaining tokens"""
        if self.buffer:
            chunk = "".join(self.buffer)
            if self.on_complete:
                self.on_complete(chunk)
            else:
                logger.info(f"Flushed: {chunk}")
            self.buffer.clear()
    
    def get_content(self) -> str:
        """Get all buffered content"""
        return "".join(self.buffer)
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()


class StreamClient:
    """High-level streaming client with event callbacks"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.handler = StreamingHandler(base_url)
        self.buffer = StreamBuffer(callback_interval=10)
        self.callbacks = {}
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for events: token, complete, error, json_chunk"""
        self.callbacks[event] = callback
        logger.info(f"Registered callback for event: {event}")
    
    def generate(self, model: str, prompt: str, **kwargs) -> str:
        """
        Generate with streaming and callbacks
        
        Returns:
            Complete response text
        """
        full_response = []
        
        def on_token(token: str):
            full_response.append(token)
            self.buffer.add_token(token)
            
            if "token" in self.callbacks:
                self.callbacks["token"](token)
        
        def on_complete(text: str):
            self.buffer.flush()
            
            if "complete" in self.callbacks:
                self.callbacks["complete"](text)
        
        def on_error(error: str):
            if "error" in self.callbacks:
                self.callbacks["error"](error)
        
        # Consume stream
        for _ in self.handler.stream_generate(
            model,
            prompt,
            on_token=on_token,
            on_complete=on_complete,
            on_error=on_error,
            **kwargs
        ):
            pass
        
        return "".join(full_response)
    
    def generate_json(self, model: str, prompt: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Generate JSON with streaming"""
        
        def on_json_chunk(obj: Dict[str, Any]):
            if "json_chunk" in self.callbacks:
                self.callbacks["json_chunk"](obj)
        
        return self.handler.stream_generate_json(
            model,
            prompt,
            on_json_chunk=on_json_chunk,
            **kwargs
        )
    
    def stop(self):
        """Stop streaming"""
        self.handler.stop_stream()


# Utility function for simple streaming
def stream_generate_simple(
    model: str,
    prompt: str,
    base_url: str = "http://localhost:11434",
    print_tokens: bool = True
) -> str:
    """Simple streaming generation with optional printing"""
    
    handler = StreamingHandler(base_url)
    full_response = []
    
    for token in handler.stream_generate(model, prompt):
        full_response.append(token)
        if print_tokens:
            print(token, end="", flush=True)
    
    print()  # Newline after streaming
    return "".join(full_response)
