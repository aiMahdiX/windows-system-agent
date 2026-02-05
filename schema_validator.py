"""
Schema Validator - Validates structured JSON outputs from Ollama
Ensures JSON responses conform to expected schemas for reliable parsing
"""

import json
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataType(Enum):
    """Supported data types for schema validation"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


class SchemaValidator:
    """Validates JSON outputs against defined schemas"""
    
    # Define schemas for different function outputs
    FUNCTION_SCHEMAS = {
        "tool_call": {
            "type": "object",
            "required": ["function", "params"],
            "properties": {
                "function": {"type": "string", "description": "Function name to call"},
                "params": {"type": "object", "description": "Function parameters"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "confidence": {"type": "number"},
                        "timestamp": {"type": "string"}
                    }
                }
            }
        },
        "timer": {
            "type": "object",
            "required": ["function"],
            "properties": {
                "function": {"type": "string", "enum": ["set_timer", "cancel_timer", "get_timer_status"]},
                "minutes": {"type": "integer", "minimum": 0},
                "seconds": {"type": "integer", "minimum": 0, "maximum": 59},
                "timer_id": {"type": "string"}
            }
        },
        "background_change": {
            "type": "object",
            "required": ["function"],
            "properties": {
                "function": {"type": "string", "enum": ["change_background"]},
                "color": {"type": "string"},
                "image_path": {"type": "string"}
            }
        },
        "application": {
            "type": "object",
            "required": ["function", "app_name"],
            "properties": {
                "function": {"type": "string", "enum": ["open_application"]},
                "app_name": {"type": "string"}
            }
        },
        "system_control": {
            "type": "object",
            "required": ["function", "action"],
            "properties": {
                "function": {"type": "string"},
                "action": {"type": "string", "enum": ["on", "off", "toggle", "mute", "unmute", "increase", "decrease"]}
            }
        },
        "volume_control": {
            "type": "object",
            "required": ["function"],
            "properties": {
                "function": {"type": "string", "enum": ["set_volume", "control_volume"]},
                "level": {"type": "integer", "minimum": 0, "maximum": 100},
                "level_text": {"type": "string"},
                "action": {"type": "string"}
            }
        },
        "response": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["success", "error", "pending", "scheduled"]},
                "message": {"type": "string"},
                "data": {"type": "object"},
                "function": {"type": "string"},
                "scheduled": {"type": "boolean"},
                "delay_seconds": {"type": "integer"}
            }
        }
    }

    @classmethod
    def validate(
        cls, 
        data: Any, 
        schema_name: str,
        strict: bool = False
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate data against schema
        
        Args:
            data: Data to validate
            schema_name: Name of schema to validate against
            strict: If True, only exact matches; if False, partial matches allowed
            
        Returns:
            Tuple of (is_valid, error_message, cleaned_data)
        """
        if schema_name not in cls.FUNCTION_SCHEMAS:
            return False, f"Unknown schema: {schema_name}", {}
        
        schema = cls.FUNCTION_SCHEMAS[schema_name]
        
        try:
            # Ensure data is dict
            if not isinstance(data, dict):
                return False, f"Expected object, got {type(data).__name__}", {}
            
            # Check required fields
            if "required" in schema:
                for required_field in schema["required"]:
                    if required_field not in data:
                        return False, f"Missing required field: {required_field}", {}
            
            # Validate properties
            cleaned_data = {}
            properties = schema.get("properties", {})
            
            for field, value in data.items():
                if field not in properties and strict:
                    return False, f"Unexpected field: {field}", {}
                
                if field in properties:
                    is_valid, error = cls._validate_property(
                        value, 
                        properties[field],
                        field
                    )
                    if not is_valid:
                        return False, error, {}
                    cleaned_data[field] = value
                else:
                    # Non-strict mode: include extra fields
                    cleaned_data[field] = value
            
            # Add required fields that are missing (for flexibility)
            for field in schema.get("required", []):
                if field not in cleaned_data:
                    if field in properties and "default" in properties[field]:
                        cleaned_data[field] = properties[field]["default"]
            
            return True, None, cleaned_data
            
        except Exception as e:
            return False, f"Validation error: {str(e)}", {}

    @classmethod
    def _validate_property(
        cls,
        value: Any,
        schema: Dict[str, Any],
        field_name: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate a single property"""
        
        value_type = schema.get("type")
        
        # Type validation
        if value_type == "string":
            if not isinstance(value, str):
                return False, f"Field '{field_name}' must be string, got {type(value).__name__}"
        
        elif value_type == "number":
            if not isinstance(value, (int, float)):
                return False, f"Field '{field_name}' must be number"
        
        elif value_type == "integer":
            if not isinstance(value, int) or isinstance(value, bool):
                return False, f"Field '{field_name}' must be integer"
            # Check min/max
            if "minimum" in schema and value < schema["minimum"]:
                return False, f"Field '{field_name}' below minimum {schema['minimum']}"
            if "maximum" in schema and value > schema["maximum"]:
                return False, f"Field '{field_name}' exceeds maximum {schema['maximum']}"
        
        elif value_type == "boolean":
            if not isinstance(value, bool):
                return False, f"Field '{field_name}' must be boolean"
        
        elif value_type == "array":
            if not isinstance(value, list):
                return False, f"Field '{field_name}' must be array"
        
        elif value_type == "object":
            if not isinstance(value, dict):
                return False, f"Field '{field_name}' must be object"
        
        elif value_type == "enum":
            enum_values = schema.get("enum", [])
            if value not in enum_values:
                return False, f"Field '{field_name}' must be one of {enum_values}"
        
        # Enum validation
        if "enum" in schema and value not in schema["enum"]:
            return False, f"Field '{field_name}' must be one of {schema['enum']}"
        
        return True, None

    @classmethod
    def parse_and_validate(
        cls,
        json_str: str,
        schema_name: str,
        strict: bool = False
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Parse JSON string and validate against schema
        
        Args:
            json_str: JSON string to parse
            schema_name: Name of schema to validate against
            strict: Strict validation mode
            
        Returns:
            Tuple of (is_valid, error_message, data)
        """
        try:
            # Try to extract JSON from text
            data = cls._extract_json(json_str)
            if data is None:
                return False, "Could not parse JSON from response", {}
            
            # Validate against schema
            return cls.validate(data, schema_name, strict)
            
        except json.JSONDecodeError as e:
            return False, f"JSON parse error: {str(e)}", {}
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", {}

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """Extract JSON object from text (handles markdown code blocks)"""
        import re
        
        # Try direct JSON parse first
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract from markdown code block
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object in text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None

    @classmethod
    def suggest_fix(cls, data: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """Suggest fixes for invalid data based on schema"""
        if schema_name not in cls.FUNCTION_SCHEMAS:
            return data
        
        schema = cls.FUNCTION_SCHEMAS[schema_name]
        fixed_data = dict(data)
        
        # Add missing required fields with defaults
        for field in schema.get("required", []):
            if field not in fixed_data:
                if field in schema.get("properties", {}):
                    prop = schema["properties"][field]
                    if prop.get("type") == "string":
                        fixed_data[field] = "unknown"
                    elif prop.get("type") == "integer":
                        fixed_data[field] = 0
                    elif prop.get("type") == "boolean":
                        fixed_data[field] = False
                    elif prop.get("type") == "object":
                        fixed_data[field] = {}
                    elif prop.get("type") == "array":
                        fixed_data[field] = []
                else:
                    # Field not in properties, use default
                    fixed_data[field] = {}
        
        return fixed_data

    @classmethod
    def create_schema_prompt(cls, schema_names: List[str]) -> str:
        """Create prompt text describing schemas for Ollama"""
        prompt_parts = ["You must ALWAYS respond with valid JSON matching one of these schemas:\n"]
        
        for schema_name in schema_names:
            if schema_name in cls.FUNCTION_SCHEMAS:
                schema = cls.FUNCTION_SCHEMAS[schema_name]
                prompt_parts.append(f"\n**{schema_name}:**")
                prompt_parts.append(json.dumps(schema, indent=2, ensure_ascii=False))
        
        prompt_parts.append("\n\nIMPORTANT: Always respond with ONLY valid JSON, no extra text.")
        
        return "\n".join(prompt_parts)
