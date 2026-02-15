#!/usr/bin/env python3
"""
Test script to verify Claude CLI integration
"""

from claude_cli_client import call_claude, call_llama3, test_claude_cli

def main():
    print("=" * 60)
    print("Testing Claude CLI Integration")
    print("=" * 60)

    # Test 1: Basic CLI connection
    print("\n[Test 1] Testing Claude CLI connection...")
    if test_claude_cli():
        print("✅ Claude CLI is accessible and working")
    else:
        print("❌ Claude CLI test failed")
        return

    # Test 2: Simple math question
    print("\n[Test 2] Testing simple query...")
    response = call_claude("What is 15 + 27? Answer with just the number.")
    print(f"Query: What is 15 + 27?")
    print(f"Response: {response}")

    # Test 3: Backward compatibility with call_llama3
    print("\n[Test 3] Testing backward compatibility (call_llama3)...")
    response = call_llama3("Name one programming language. Just the name.")
    print(f"Query: Name one programming language")
    print(f"Response: {response}")

    # Test 4: System prompt simulation
    print("\n[Test 4] Testing with system prompt...")
    system = "You are a helpful assistant that answers in one short sentence."
    prompt = "Why is the sky blue?"
    full_prompt = f"{system}\n\n{prompt}"
    response = call_claude(full_prompt)
    print(f"Query: Why is the sky blue?")
    print(f"Response: {response}")

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
