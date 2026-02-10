"""
Claude API Client Module
Replaces Ollama LLaMA3 with Anthropic's Claude API for faster, more reliable AI responses.
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Claude client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Model configuration
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"  # Latest and fastest Claude model
MAX_TOKENS = 4096

def call_claude(prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = MAX_TOKENS) -> str:
    """
    Call Claude API with a prompt and return the response.

    Args:
        prompt: The user prompt/query
        system_prompt: Optional system prompt to set context
        temperature: Randomness in responses (0.0 to 1.0)
        max_tokens: Maximum tokens in response

    Returns:
        The text response from Claude
    """
    try:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        # Add system prompt if provided
        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)

        # Extract text from response
        return response.content[0].text

    except Exception as e:
        print(f"[ERROR] Claude API call failed: {str(e)}")
        return f"Error calling Claude API: {str(e)}"


def call_claude_with_tools(prompt: str, tools: list = None, system_prompt: str = None) -> dict:
    """
    Call Claude with tool/function calling support.

    Args:
        prompt: The user prompt/query
        tools: List of tool definitions in Claude format
        system_prompt: Optional system prompt

    Returns:
        dict with 'type' (text or tool_use) and 'content' or 'tool_calls'
    """
    try:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        if tools:
            kwargs["tools"] = tools

        response = client.messages.create(**kwargs)

        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            tool_uses = [block for block in response.content if block.type == "tool_use"]
            return {
                "type": "tool_use",
                "tool_calls": tool_uses
            }
        else:
            # Regular text response
            text_content = "".join([block.text for block in response.content if hasattr(block, 'text')])
            return {
                "type": "text",
                "content": text_content
            }

    except Exception as e:
        print(f"[ERROR] Claude API call with tools failed: {str(e)}")
        return {
            "type": "error",
            "content": f"Error: {str(e)}"
        }


def call_claude_streaming(prompt: str, system_prompt: str = None):
    """
    Call Claude API with streaming enabled.

    Args:
        prompt: The user prompt/query
        system_prompt: Optional system prompt

    Yields:
        Text chunks as they arrive
    """
    try:
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    except Exception as e:
        yield f"Error: {str(e)}"


# Backward compatibility - alias to match existing call_llama3 function
def call_llama3(prompt: str) -> str:
    """
    Backward compatibility wrapper.
    Replaces the old Ollama call_llama3 with Claude API.
    """
    return call_claude(prompt)
