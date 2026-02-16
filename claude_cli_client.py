"""
Claude CLI Client Module
Uses the Claude CLI (claude-code) instead of the Claude API for LLM calls.
"""

import subprocess
import json
import tempfile
import os
from typing import Optional, Generator

# Configuration
CLAUDE_CLI_COMMAND = "claude"  # Assumes 'claude' is in PATH
DEFAULT_TIMEOUT = 120  # seconds


def call_claude_cli(
    prompt: str,
    system_prompt: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    model: str = "sonnet"
) -> str:
    """
    Call Claude CLI with a prompt and return the response.

    Args:
        prompt: The user prompt/query
        system_prompt: Optional system prompt to set context
        timeout: Command timeout in seconds
        model: Model to use (sonnet, opus, haiku)

    Returns:
        The text response from Claude CLI
    """
    try:
        # Prepare the full prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Unset CLAUDECODE to avoid nested session errors
        env = os.environ.copy()
        env.pop('CLAUDECODE', None)

        # Build the Claude CLI command
        # Note: Claude CLI doesn't support --model flag in chat mode
        cmd = [CLAUDE_CLI_COMMAND, "chat"]

        # Execute the command with prompt via stdin
        result = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env
        )

        # Check if we got a valid response in stdout
        response = result.stdout.strip()

        # If there's a valid response, return it even if return code is non-zero
        # (Claude CLI sometimes returns non-zero with warnings but still produces output)
        if response:
            if result.stderr:
                print(f"[WARNING] Claude CLI stderr: {result.stderr.strip()}")
            return response

        # Only treat as error if we have no response
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"[ERROR] Claude CLI failed: {error_msg}")
            return f"Error calling Claude CLI: {error_msg}"

        return response

    except subprocess.TimeoutExpired:
        return f"Error: Claude CLI timed out after {timeout} seconds"
    except FileNotFoundError:
        return f"Error: Claude CLI command '{CLAUDE_CLI_COMMAND}' not found. Make sure it's installed and in PATH."
    except Exception as e:
        print(f"[ERROR] Claude CLI call failed: {str(e)}")
        return f"Error calling Claude CLI: {str(e)}"


def call_claude_cli_interactive(prompt: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    Call Claude CLI using stdin for prompt input (alternative method).

    Args:
        prompt: The user prompt/query
        timeout: Command timeout in seconds

    Returns:
        The text response from Claude CLI
    """
    try:
        # Unset CLAUDECODE to avoid nested session errors
        env = os.environ.copy()
        env.pop('CLAUDECODE', None)

        # Build the Claude CLI command
        cmd = [CLAUDE_CLI_COMMAND, "chat"]

        # Execute the command with prompt via stdin
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env
        )

        # Check if we got a valid response in stdout
        response = result.stdout.strip()

        # If there's a valid response, return it even if return code is non-zero
        # (Claude CLI sometimes returns non-zero with warnings but still produces output)
        if response:
            if result.stderr:
                print(f"[WARNING] Claude CLI stderr: {result.stderr.strip()}")
            return response

        # Only treat as error if we have no response
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"[ERROR] Claude CLI failed: {error_msg}")
            return f"Error calling Claude CLI: {error_msg}"

        return response

    except subprocess.TimeoutExpired:
        return f"Error: Claude CLI timed out after {timeout} seconds"
    except FileNotFoundError:
        return f"Error: Claude CLI command '{CLAUDE_CLI_COMMAND}' not found. Make sure it's installed and in PATH."
    except Exception as e:
        print(f"[ERROR] Claude CLI call failed: {str(e)}")
        return f"Error calling Claude CLI: {str(e)}"


def call_claude_cli_simple(prompt: str) -> str:
    """
    Simplified Claude CLI call using stdin.
    This is the most straightforward approach.

    Args:
        prompt: The user prompt/query

    Returns:
        The text response from Claude CLI
    """
    try:
        # Unset CLAUDECODE to avoid nested session errors
        env = os.environ.copy()
        env.pop('CLAUDECODE', None)

        # Execute claude command with prompt via stdin
        result = subprocess.run(
            [CLAUDE_CLI_COMMAND, "chat"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=DEFAULT_TIMEOUT,
            check=False,
            env=env
        )

        # Check if we got a valid response in stdout
        response = result.stdout.strip()

        # If there's a valid response, return it even if return code is non-zero
        # (Claude CLI sometimes returns non-zero with warnings but still produces output)
        if response:
            if result.stderr:
                print(f"[WARNING] Claude CLI stderr: {result.stderr.strip()}")
            return response

        # Only treat as error if we have no response
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"[ERROR] Claude CLI failed: {error_msg}")
            return f"Error calling Claude CLI: {error_msg}"

        return response

    except subprocess.TimeoutExpired:
        return f"Error: Claude CLI timed out after {DEFAULT_TIMEOUT} seconds"
    except FileNotFoundError:
        return f"Error: Claude CLI command '{CLAUDE_CLI_COMMAND}' not found. Make sure it's installed and in PATH."
    except Exception as e:
        print(f"[ERROR] Claude CLI call failed: {str(e)}")
        return f"Error calling Claude CLI: {str(e)}"


# Backward compatibility - alias to match existing call_llama3 function
def call_llama3(prompt: str) -> str:
    """
    Backward compatibility wrapper.
    Replaces the old Ollama call_llama3 with Claude CLI.
    """
    return call_claude_cli_simple(prompt)


def call_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> str:
    """
    Main Claude call function - matches the API signature but uses CLI.

    Args:
        prompt: The user prompt/query
        system_prompt: Optional system prompt to set context (prepended to prompt)
        temperature: Not used with CLI, included for API compatibility
        max_tokens: Not used with CLI, included for API compatibility

    Returns:
        The text response from Claude CLI
    """
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    return call_claude_cli_simple(full_prompt)


def test_claude_cli():
    """
    Test function to verify Claude CLI is working.
    """
    print("Testing Claude CLI connection...")
    response = call_claude_cli_simple("Say 'Hello, I am Claude CLI' and nothing else.")
    print(f"Response: {response}")
    return "Claude CLI" in response or "claude" in response.lower()


if __name__ == "__main__":
    # Test the CLI connection
    if test_claude_cli():
        print("✅ Claude CLI is working correctly!")
    else:
        print("❌ Claude CLI test failed. Please check your installation.")

    # Interactive test
    test_prompt = "What is 2+2? Answer in one sentence."
    print(f"\nTest prompt: {test_prompt}")
    response = call_claude(test_prompt)
    print(f"Response: {response}")
