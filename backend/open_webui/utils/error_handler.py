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
    PRICING_ERROR = "pricing_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"

class SanitizedError(Exception):
    """Custom exception for sanitized errors"""
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, original_error: Optional[Exception] = None):
        self.message = message
        self.category = category
        self.original_error = original_error
        super().__init__(self.message)

def sanitize_pricing_error(error: Exception) -> SanitizedError:
    """
    Handle pricing-related errors from the pricing module

    Args:
        error: The pricing exception

    Returns:
        SanitizedError with sanitized message
    """
    error_str = str(error).lower()

    # Log the original pricing error for debugging (but don't expose it)
    log.error(f"Pricing error: {error}")

    # All pricing-related errors get completely generic messages
    # No model names, service names, or internal details exposed
    if any(term in error_str for term in [
        "not found in litellm price map",
        "pricing information not available", 
        "pricing information incomplete",
        "unable to load pricing information",
        "service is temporarily unavailable",
        "service configuration is incomplete",
        "service configuration is temporarily unavailable",
        "the requested service is currently unavailable"
    ]):
        return SanitizedError(
            message="This service is temporarily unavailable. Please try again later.",
            category=ErrorCategory.PRICING_ERROR,
            original_error=error
        )

    # Generic fallback for any other pricing errors
    return SanitizedError(
        message="Unable to process your request at this time. Please try again later.",
        category=ErrorCategory.PRICING_ERROR,
        original_error=error
    )

def categorize_error(error_str: str) -> ErrorCategory:
    """Categorize error based on content"""
    error_lower = error_str.lower()

    # Pricing errors (check first to catch specific pricing issues)
    if any(keyword in error_lower for keyword in [
        'litellm price map', 'pricing information not available', 'unable to load pricing',
        'service is temporarily unavailable', 'service configuration is incomplete',
        'the requested service is currently unavailable'
    ]):
        return ErrorCategory.PRICING_ERROR

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

    # Model-specific errors (including "model not found") - now returns generic system error
    if any(keyword in error_lower for keyword in ['model not found', 'model', 'completion', 'generation', 'inference']):
        return ErrorCategory.MODEL_ERROR

    # System errors - catch internal service errors
    if any(keyword in error_lower for keyword in ['litellm', 'openai', 'ollama', 'open_webui', 'openwebui', 'system', 'internal']):
        return ErrorCategory.SYSTEM_ERROR

    return ErrorCategory.UNKNOWN

def remove_sensitive_info(error_message: str) -> str:
    """Remove sensitive service names, model names, and internal details"""

    # Patterns to remove/replace - comprehensive model name and service sanitization
    sensitive_patterns = [
        # Service names
        (r'litellm[.\w]*', 'service'),
        (r'openai[.\w]*', 'service'),
        (r'ollama[.\w]*', 'service'),
        (r'open[_\s-]?webui[.\w]*', 'system'),
        (r'anthropic[.\w]*', 'service'),
        (r'google[.\w]*', 'service'),
        (r'mistral[.\w]*', 'service'),
        
        # Model names - be very aggressive about hiding these
        (r'gpt-[0-9a-z.-]+', 'AI model'),
        (r'claude-[0-9a-z.-]+', 'AI model'),
        (r'gemini-[0-9a-z.-]+', 'AI model'),
        (r'llama[0-9a-z.-]*', 'AI model'),
        (r'mistral[0-9a-z.-]*', 'AI model'),
        (r'qwen[0-9a-z.-]*', 'AI model'),
        (r'deepseek[0-9a-z.-]*', 'AI model'),
        (r'mixtral[0-9a-z.-]*', 'AI model'),
        (r'phi[0-9a-z.-]*', 'AI model'),
        (r'codellama[0-9a-z.-]*', 'AI model'),
        (r'vicuna[0-9a-z.-]*', 'AI model'),
        (r'alpaca[0-9a-z.-]*', 'AI model'),
        (r'palm[0-9a-z.-]*', 'AI model'),
        (r'bard[0-9a-z.-]*', 'AI model'),
        
        # Generic model patterns
        (r'model\s+[\'"`][^\'"`]+[\'"`]', 'requested service'),
        (r'model\s+[\'"]\w+[\'"]\s+not\s+found', 'requested service not found'),
        (r'[\'"]\w*gpt\w*[\'"]', 'AI model'),
        (r'[\'"]\w*claude\w*[\'"]', 'AI model'),
        (r'[\'"]\w*llama\w*[\'"]', 'AI model'),
        
        # URLs and endpoints
        (r'api[_\s-]?key[.\w]*', 'credentials'),
        (r'bearer[_\s-]?token[.\w]*', 'credentials'),
        (r'localhost:\d+', 'service'),
        (r'127\.0\.0\.1:\d+', 'service'),
        (r'http[s]?://[^\s]+', 'service endpoint'),
        (r'github\.com[^\s]*', 'external service'),
        (r'raw\.githubusercontent\.com[^\s]*', 'external service'),
        (r'huggingface\.co[^\s]*', 'external service'),
        
        # Credentials and tokens - remove actual values
        (r'api[_\s-]?key[_\s-]+[a-zA-Z0-9]{3,}', 'credentials'),
        (r'bearer[_\s-]?token[_\s-]+[a-zA-Z0-9]{3,}', 'credentials'),
        (r'token[_\s-]+[a-zA-Z0-9]{3,}', 'credentials'),
        (r'key[_\s-]+[a-zA-Z0-9]{3,}', 'credentials'),
        (r'for\s+API\s+key\s+[a-zA-Z0-9]+', 'for credentials'),
        (r'API\s+key\s+[a-zA-Z0-9]+', 'credentials'),
        (r'credentials\s+[a-zA-Z0-9]+', 'credentials'),  # Remove any remaining tokens after "credentials"
        (r'\b[a-zA-Z0-9]{20,}\b', 'credentials'),  # Long alphanumeric strings (likely tokens)
        
        # System internals
        (r'traceback[^\n]*', ''),
        (r'file\s+"[^"]*"[^\n]*', ''),
        (r'line\s+\d+[^\n]*', ''),
        (r'\.py:\d+', ''),
        (r'in\s+\w+\s*\([^)]*\)', ''),
        
        # Price map specific
        (r'price\s+map', 'service configuration'),
        (r'pricing\s+information', 'service information'),
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
        ErrorCategory.NETWORK: "Unable to connect to the service. Please check your internet connection and try again.",
        ErrorCategory.AUTHENTICATION: "Authentication failed. Please contact support.",
        ErrorCategory.RATE_LIMIT: "Service is currently busy due to high demand. Please wait a moment and try again.",
        ErrorCategory.INVALID_REQUEST: "Invalid request format. Please check your input and try again.",
        ErrorCategory.MODEL_ERROR: "The requested service is currently unavailable. Please try again later.",
        ErrorCategory.PRICING_ERROR: "This service is temporarily unavailable. Please try again later.",
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

    # Check for pricing errors first - expanded pattern matching
    error_str_lower = str(error).lower()
    if any(term in error_str_lower for term in [
        "litellm price map", "pricing information not available", "pricing information incomplete",
        "unable to load pricing information", "service is temporarily unavailable",
        "service configuration is incomplete", "service configuration is temporarily unavailable",
        "the requested service is currently unavailable"
    ]):
        return sanitize_pricing_error(error)

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
        message="The requested service is currently unavailable. Please try again later.",
        category=ErrorCategory.MODEL_ERROR,
        original_error=None
    )

def is_model_not_found_error(error: Exception) -> bool:
    """Check if error is a model not found error"""
    error_str = str(error).lower()
    return "model not found" in error_str or "model" in error_str and "not found" in error_str

def sanitize_litellm_error(error: Exception) -> SanitizedError:
    """
    Specifically handle service errors to remove all references to services and models

    Args:
        error: The service exception

    Returns:
        SanitizedError with sanitized message
    """
    error_str = str(error).lower()

    # Log the original service error for debugging (but don't expose it)
    log.error(f"Service error: {error}")

    # All service errors get completely generic messages
    if any(term in error_str for term in ["api", "key", "token", "auth"]):
        return SanitizedError(
            message="Authentication failed. Please contact support.",
            category=ErrorCategory.AUTHENTICATION,
            original_error=error
        )

    if any(term in error_str for term in ["rate limit", "quota", "throttl"]):
        return SanitizedError(
            message="Service is currently busy. Please wait a moment and try again.",
            category=ErrorCategory.RATE_LIMIT,
            original_error=error
        )

    if any(term in error_str for term in ["timeout", "connection"]):
        return SanitizedError(
            message="Service is temporarily unavailable. Please try again later.",
            category=ErrorCategory.NETWORK,
            original_error=error
        )

    if any(term in error_str for term in ["model", "not found", "not available"]):
        return SanitizedError(
            message="The requested service is currently unavailable. Please try again later.",
            category=ErrorCategory.MODEL_ERROR,
            original_error=error
        )

    # Default generic message for other service errors
    return SanitizedError(
        message="Service is temporarily unavailable. Please try again later.",
        category=ErrorCategory.UNKNOWN,
        original_error=error
    )
