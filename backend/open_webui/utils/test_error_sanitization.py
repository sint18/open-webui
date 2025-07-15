import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from open_webui.utils.error_handler import (
    sanitize_error,
    ErrorCategory,
    handle_model_not_found_error,
    is_model_not_found_error,
    sanitize_litellm_error
)

def test_error_sanitization():
    print("Testing Error Sanitization...")
    print("=" * 50)

    # Test 1: LiteLLM error
    print("Test 1: LiteLLM Error")
    litellm_error = Exception("litellm.exceptions.APIError: OpenAI API error occurred at localhost:8080")
    sanitized = sanitize_error(litellm_error)
    print(f"Original: {litellm_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 2: Connection error
    print("Test 2: Connection Error")
    connection_error = Exception("Connection timeout to http://127.0.0.1:11434/api/chat")
    sanitized = sanitize_error(connection_error)
    print(f"Original: {connection_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 3: Authentication error
    print("Test 3: Authentication Error")
    auth_error = Exception("Unauthorized: Invalid API key provided for OpenAI service")
    sanitized = sanitize_error(auth_error)
    print(f"Original: {auth_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 4: Rate limit error
    print("Test 4: Rate Limit Error")
    rate_error = Exception("Rate limit exceeded for model requests. Please try again later.")
    sanitized = sanitize_error(rate_error)
    print(f"Original: {rate_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 5: OpenWebUI reference
    print("Test 5: OpenWebUI Reference")
    webui_error = Exception("OpenWebUI failed to process request in open_webui.main module")
    sanitized = sanitize_error(webui_error)
    print(f"Original: {webui_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 6: Model not found error
    print("Test 6: Model Not Found Error")
    model_error = Exception("Model not found")
    sanitized = sanitize_error(model_error)
    print(f"Original: {model_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 7: Specific model not found with ID
    print("Test 7: Specific Model Not Found Error")
    specific_model_error = handle_model_not_found_error("llama3.2:7b")
    print(f"Model ID: llama3.2:7b")
    print(f"Sanitized: {specific_model_error.message}")
    print(f"Category: {specific_model_error.category.value}")
    print("-" * 30)

    # Test 8: LiteLLM model error
    print("Test 8: LiteLLM Model Error")
    litellm_model_error = Exception("litellm.exceptions.NotFoundError: model 'gpt-4-turbo' not found")
    sanitized = sanitize_litellm_error(litellm_model_error)
    print(f"Original: {litellm_model_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 9: LiteLLM API key error
    print("Test 9: LiteLLM API Key Error")
    litellm_auth_error = Exception("litellm.exceptions.AuthenticationError: Invalid API key provided")
    sanitized = sanitize_litellm_error(litellm_auth_error)
    print(f"Original: {litellm_auth_error}")
    print(f"Sanitized: {sanitized.message}")
    print(f"Category: {sanitized.category.value}")
    print("-" * 30)

    # Test 10: Model not found detection
    print("Test 10: Model Not Found Detection")
    test_errors = [
        Exception("Model not found"),
        Exception("The model 'gpt-4' was not found"),
        Exception("Connection timeout"),
        Exception("Model completion failed")
    ]

    for i, error in enumerate(test_errors):
        is_model_error = is_model_not_found_error(error)
        print(f"  {i+1}. '{error}' -> Model not found: {is_model_error}")

    print("-" * 30)
    print("Testing complete!")

if __name__ == "__main__":
    test_error_sanitization()
