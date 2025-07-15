import logging
import re
import time
from typing import Optional, Any
from enum import Enum

log = logging.getLogger(__name__)

class ErrorCategory(Enum):
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    INVALID_REQUEST = "invalid_request"
    MODEL_ERROR = "model_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"

class SanitizedError(Exception):
    """Custom exception for sanitized errors"""
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, original_error: Optional[Exception] = None):
        self.message = message
        self.category = category
        self.original_error = original_error
        super().__init__(self.message)

def categorize_error(error_str: str) -> ErrorCategory:
    """Categorize error based on content"""
    error_lower = error_str.lower()

    # Network/connection errors
    if any(keyword in error_lower for keyword in ['connection', 'network', 'timeout', 'unreachable', 'dns', 'failed to connect']):
        return ErrorCategory.NETWORK

    # Authentication errors
    if any(keyword in error_lower for keyword in ['unauthorized', 'forbidden', 'authentication', 'token', 'api key', 'invalid key']):
        return ErrorCategory.AUTHENTICATION

    # Rate limiting errors
    if any(keyword in error_lower for keyword in ['rate limit', 'quota', 'too many requests', 'throttle', 'rate exceeded']):
        return ErrorCategory.RATE_LIMIT

    # Invalid request errors
    if any(keyword in error_lower for keyword in ['invalid', 'bad request', 'validation', 'missing', 'malformed']):
        return ErrorCategory.INVALID_REQUEST

    # Model-specific errors (including "model not found")
    if any(keyword in error_lower for keyword in ['model not found', 'model', 'completion', 'generation', 'inference']):
        return ErrorCategory.MODEL_ERROR

    # System errors - catch internal service errors
    if any(keyword in error_lower for keyword in ['litellm', 'openai', 'ollama', 'open_webui', 'openwebui', 'system', 'internal']):
        return ErrorCategory.SYSTEM_ERROR

    return ErrorCategory.UNKNOWN

def remove_sensitive_info(error_message: str) -> str:
    """Remove sensitive service names and internal details"""

    # Patterns to remove/replace
    sensitive_patterns = [
        (r'litellm[.\w]*', 'AI service'),
        (r'openai[.\w]*', 'AI service'),
        (r'ollama[.\w]*', 'AI service'),
        (r'open[_\s-]?webui[.\w]*', 'system'),
        (r'api[_\s-]?key[.\w]*', 'credentials'),
        (r'bearer[_\s-]?token[.\w]*', 'credentials'),
        (r'localhost:\d+', 'service'),
        (r'127\.0\.0\.1:\d+', 'service'),
        (r'http[s]?://[^\s]+', 'service endpoint'),
        (r'traceback[^\n]*', ''),
        (r'file\s+"[^"]*"[^\n]*', ''),
        (r'line\s+\d+[^\n]*', ''),
        (r'\.py:\d+', ''),
        (r'in\s+\w+\s*\([^)]*\)', ''),
    ]

    cleaned_message = error_message
    for pattern, replacement in sensitive_patterns:
        cleaned_message = re.sub(pattern, replacement, cleaned_message, flags=re.IGNORECASE)

    # Remove empty lines and extra spaces
    cleaned_message = re.sub(r'\n\s*\n', '\n', cleaned_message)
    cleaned_message = re.sub(r'\s+', ' ', cleaned_message).strip()

    return cleaned_message

def get_user_friendly_message(category: ErrorCategory, original_error: str = "") -> str:
    """Get user-friendly message based on error category"""

    messages = {
        ErrorCategory.NETWORK: "Unable to connect to the AI service. Please check your internet connection and try again.",
        ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials and try again.",
        ErrorCategory.RATE_LIMIT: "Service is currently busy due to high demand. Please wait a moment and try again.",
        ErrorCategory.INVALID_REQUEST: "Invalid request format. Please check your input and try again.",
        ErrorCategory.MODEL_ERROR: "The AI model encountered an issue processing your request. Please try again or use a different model.",
        ErrorCategory.SYSTEM_ERROR: "A system error occurred. Please try again later.",
        ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again."
    }

    return messages.get(category, messages[ErrorCategory.UNKNOWN])

def sanitize_error(error: Exception, user_facing: bool = True) -> SanitizedError:
    """
    Main function to sanitize errors for user consumption

    Args:
        error: The original exception
        user_facing: Whether this error will be shown to users

    Returns:
        SanitizedError with clean message
    """

    # Log the original error for debugging
    log.error(f"Original error: {type(error).__name__}: {str(error)}")

    if not user_facing:
        # For internal use, return sanitized but more detailed error
        return SanitizedError(
            message=remove_sensitive_info(str(error)),
            category=ErrorCategory.SYSTEM_ERROR,
            original_error=error
        )

    # For user-facing errors, return generic friendly message
    error_str = str(error)
    category = categorize_error(error_str)
    user_message = get_user_friendly_message(category, error_str)

    return SanitizedError(
        message=user_message,
        category=category,
        original_error=error
    )

def handle_api_error(error: Exception) -> dict:
    """
    Handle API errors and return standardized response format

    Returns:
        Dict with error details for API response
    """
    sanitized = sanitize_error(error, user_facing=True)

    return {
        "error": sanitized.message,
        "category": sanitized.category.value,
        "timestamp": time.time()
    }

def handle_model_not_found_error(model_id: str = "") -> SanitizedError:
    """
    Handle specific model not found errors

    Args:
        model_id: The model ID that was not found

    Returns:
        SanitizedError with user-friendly message
    """
    if model_id:
        log.error(f"Model not found: {model_id}")
    else:
        log.error("Model not found (no ID provided)")

    return SanitizedError(
        message="The requested model is not available. Please try selecting a different model.",
        category=ErrorCategory.MODEL_ERROR,
        original_error=None
    )

def is_model_not_found_error(error: Exception) -> bool:
    """Check if error is a model not found error"""
    error_str = str(error).lower()
    return "model not found" in error_str or "model" in error_str and "not found" in error_str

def sanitize_litellm_error(error: Exception) -> SanitizedError:
    """
    Specifically handle LiteLLM errors to remove service references

    Args:
        error: The LiteLLM exception

    Returns:
        SanitizedError with sanitized message
    """
    error_str = str(error).lower()

    # Log the original LiteLLM error for debugging
    log.error(f"LiteLLM error: {error}")

    # Check for specific LiteLLM error patterns
    if "api" in error_str and ("key" in error_str or "token" in error_str):
        return SanitizedError(
            message="Authentication failed. Please check your API configuration.",
            category=ErrorCategory.AUTHENTICATION,
            original_error=error
        )

    if "rate limit" in error_str or "quota" in error_str:
        return SanitizedError(
            message="Service is currently busy due to high demand. Please wait a moment and try again.",
            category=ErrorCategory.RATE_LIMIT,
            original_error=error
        )

    if "timeout" in error_str or "connection" in error_str:
        return SanitizedError(
            message="Unable to connect to the AI service. Please check your internet connection and try again.",
            category=ErrorCategory.NETWORK,
            original_error=error
        )

    if "model" in error_str and ("not found" in error_str or "not available" in error_str):
        return SanitizedError(
            message="The requested model is not available. Please try selecting a different model.",
            category=ErrorCategory.MODEL_ERROR,
            original_error=error
        )

    # Default generic message for other LiteLLM errors
    return SanitizedError(
        message="An unexpected error occurred while processing your request. Please try again.",
        category=ErrorCategory.UNKNOWN,
        original_error=error
    )
