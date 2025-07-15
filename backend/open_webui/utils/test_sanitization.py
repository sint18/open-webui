#!/usr/bin/env python3
"""
Test script to verify error sanitization is working correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.error_handler import sanitize_error, sanitize_pricing_error, remove_sensitive_info

def test_pricing_error_sanitization():
    """Test that pricing errors are properly sanitized"""
    print("Testing pricing error sanitization...")

    test_cases = [
        "model 'gpt-4' not found in LiteLLM price map @ https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json",
        "model 'claude-3-sonnet-20240229' not found in LiteLLM price map @ https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json",
        "Pricing information not available for model 'llama-3.1-70b-versatile'",
        "Unable to load pricing information for gpt-4o-mini",
        "Service is temporarily unavailable. Please try again later.",
        "The requested service is currently unavailable. Please try again later.",
        "Service configuration is incomplete. Please try again later."
    ]

    for i, error_msg in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Original: {error_msg}")

        error = Exception(error_msg)
        sanitized = sanitize_error(error)

        print(f"Sanitized: {sanitized.message}")
        print(f"Category: {sanitized.category.value}")

        # Check that no sensitive information is exposed
        assert "gpt-4" not in sanitized.message.lower()
        assert "claude" not in sanitized.message.lower()
        assert "llama" not in sanitized.message.lower()
        assert "litellm" not in sanitized.message.lower()
        assert "openai" not in sanitized.message.lower()
        assert "github" not in sanitized.message.lower()
        assert "price map" not in sanitized.message.lower()

        print("✓ No sensitive information exposed")

def test_remove_sensitive_info():
    """Test the remove_sensitive_info function"""
    print("\n\nTesting remove_sensitive_info function...")

    test_cases = [
        "Error with gpt-4 model in OpenAI API",
        "LiteLLM service failed for claude-3-sonnet",
        "Model 'llama-3.1-70b' not found in price map",
        "Connection to http://localhost:11434 failed",
        "Authentication failed for API key abc123",
        "Rate limit exceeded for mistral-7b-instruct"
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Original: {text}")

        cleaned = remove_sensitive_info(text)
        print(f"Cleaned: {cleaned}")

        # Verify sensitive info is removed
        assert "gpt-4" not in cleaned.lower()
        assert "claude-3-sonnet" not in cleaned.lower()
        assert "llama-3.1-70b" not in cleaned.lower()
        assert "litellm" not in cleaned.lower()
        assert "openai" not in cleaned.lower()
        assert "localhost:11434" not in cleaned.lower()
        assert "abc123" not in cleaned.lower()
        assert "mistral-7b-instruct" not in cleaned.lower()

        print("✓ Sensitive information removed")

def test_service_error_sanitization():
    """Test that service errors are properly sanitized"""
    print("\n\nTesting service error sanitization...")

    test_cases = [
        "OpenAI API authentication failed",
        "Ollama service connection timeout",
        "LiteLLM rate limit exceeded",
        "Model gpt-4 not available",
        "Claude-3 API quota exceeded"
    ]

    for i, error_msg in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"Original: {error_msg}")

        error = Exception(error_msg)
        sanitized = sanitize_error(error)

        print(f"Sanitized: {sanitized.message}")
        print(f"Category: {sanitized.category.value}")

        # Check that no service names or model names are exposed
        assert "openai" not in sanitized.message.lower()
        assert "ollama" not in sanitized.message.lower()
        assert "litellm" not in sanitized.message.lower()
        assert "gpt-4" not in sanitized.message.lower()
        assert "claude-3" not in sanitized.message.lower()

        print("✓ No service or model names exposed")

if __name__ == "__main__":
    print("Running error sanitization tests...")
    print("=" * 50)

    test_pricing_error_sanitization()
    test_remove_sensitive_info()
    test_service_error_sanitization()

    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    print("Error sanitization is working correctly.")
