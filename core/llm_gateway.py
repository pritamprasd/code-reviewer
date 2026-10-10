"""
LLM Gateway Module
Unified client bridging local & cloud LLMs via LiteLLM.
Supports OpenRouter, GitHub Copilot (via Copilot tokens or LiteLLM Copilot proxy),
Ollama, Azure, OpenAI, and custom OpenAI-compatible proxy endpoints.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import litellm


class LLMGateway:
    """Manages connections to LLM providers and executes completions."""

    DEFAULT_PRESETS = {
        "OpenRouter": {
            "model": "openrouter/anthropic/claude-3.5-sonnet",
            "api_base": "https://openrouter.ai/api/v1",
            "description": "OpenRouter API (supports Claude 3.5, GPT-4o, DeepSeek, Llama 3.3)",
        },
        "GitHub Copilot (via Proxy / LiteLLM)": {
            "model": "github_copilot/gpt-4o",
            "api_base": "http://localhost:4000/v1",
            "description": "LiteLLM or Copilot Proxy bridging GitHub Copilot subscription",
        },
        "GitHub Models (Marketplace)": {
            "model": "github/gpt-4o",
            "api_base": "https://models.inference.ai.azure.com",
            "description": "GitHub Models API using GitHub Personal Access Token (PAT)",
        },
        "Local Ollama": {
            "model": "ollama/qwen2.5-coder:14b",
            "api_base": "http://localhost:11434",
            "description": "Local Ollama server (Qwen 2.5 Coder, DeepSeek Coder, etc.)",
        },
        "Custom OpenAI-Compatible Gateway": {
            "model": "custom-model",
            "api_base": "http://localhost:4000/v1",
            "description": "Any self-hosted LiteLLM Proxy, vLLM, or Portkey gateway",
        },
    }

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GITHUB_TOKEN")
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Configure litellm suppress noisy telemetry
        litellm.telemetry = False
        litellm.drop_params = True

    def test_connection(self) -> Tuple[bool, str]:
        """Verify connection to the configured LLM gateway."""
        try:
            messages = [
                {"role": "system", "content": "You are a test ping agent."},
                {"role": "user", "content": "Respond with exactly 'PONG'."},
            ]
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 10,
                "temperature": 0.0,
            }
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.api_base:
                kwargs["api_base"] = self.api_base

            resp = litellm.completion(**kwargs)
            content = resp.choices[0].message.content.strip()
            return True, f"Connection successful! Response: {content}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def generate_review(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send code review prompt to the configured LLM through the gateway.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        resp = litellm.completion(**kwargs)
        return resp.choices[0].message.content
