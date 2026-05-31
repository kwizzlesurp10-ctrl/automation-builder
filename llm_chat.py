#!/usr/bin/env python3
"""
LLM Chat — Automation Builder

The flagship experience: Talk naturally to an LLM and have it execute
real web navigation and automation actions in your logged-in browser.

Features:
- Multi-backend LLM support (Ollama + any OpenAI-compatible endpoint)
- Clean JSON action format (reliable for modern LLMs)
- Full access to the Automation Builder toolkit
- Automatic glowing panda during actions
- **Real vision support** — screenshots are sent as images to vision-capable models
- Self-discovery via list_keyboard_shortcuts()

Run:
    python llm_chat.py --model llama3.1
    python llm_chat.py --backend openai --base-url http://localhost:8000/v1 --model gpt-4o-mini

Requirements:
- Chrome running with remote debugging
- Ollama or an OpenAI-compatible server (vision models work best with gpt-4o, llava, etc.)
"""

import argparse
import base64
import json
import os
import time
from typing import Any, Dict, List, Optional

import requests

from browser_connector import WebBrowserConnector


class LLMBrowserAgent:
    def __init__(
        self,
        model: str = "llama3.1",
        backend: str = "ollama",
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        cdp_url: str = "http://localhost:9222",
    ):
        print("Connecting to live Chrome session (CDP)...")
        self.conn = WebBrowserConnector(
            cdp_url=cdp_url,
            auto_indicator=True,
            indicator_label="🤖 LLM Agent",
            indicator_actions={
                "goto",
                "click",
                "select_option",
                "fill",
                "type",
                "keyboard_shortcut",
                "wait_for_navigation",
                "execute_script",
                "new_tab",
                "switch_to_tab",
                "reload",
                "screenshot",
            },
        )
        print("Connected. Glowing panda will appear during actions.\n")

        self.model = model
        self.backend = backend.lower()
        self.base_url = base_url or (
            "http://localhost:11434"
            if backend == "ollama"
            else "http://localhost:8000/v1"
        )
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "ollama")
        self.conversation: List[Dict[str, Any]] = []

        self.is_vision_model = self._detect_vision_model(model)

        self.system_prompt = self._build_system_prompt()

    def _detect_vision_model(self, model: str) -> bool:
        """Heuristic to detect if the model supports vision."""
        vision_keywords = [
            "vision",
            "llava",
            "gpt-4o",
            "claude-3",
            "qwen2-vl",
            "bakllava",
        ]
        model_lower = model.lower()
        return any(kw in model_lower for kw in vision_keywords)

    def _build_system_prompt(self) -> str:
        vision_rule = ""
        if self.is_vision_model:
            vision_rule = "\n5. VISION CAPABILITY: You receive actual images when you call `screenshot`. CRITICAL: Cross-reference the output of `list_keyboard_shortcuts` with your visual understanding of the UI to map visual buttons/icons directly to robust keyboard commands."

        return f"""You are an expert browser automation agent controlling a real logged-in Chrome browser using the Automation Builder toolkit.

Available tools (call them by outputting clean JSON, one object per line):
{{
  "action": "goto",
  "url": "https://..."
}}
{{
  "action": "click",
  "selector": "text=Submit"
}}
{{
  "action": "select_option",
  "option": "MIT License",
  "container": "Add license"
}}
{{
  "action": "keyboard_shortcut",
  "keys": "Control+L"
}}
{{
  "action": "screenshot"
}}
{{
  "action": "list_keyboard_shortcuts"
}}

You also have: fill, type, execute_script, wait_for_navigation, new_tab, switch_to_tab, reload.

CRITICAL RULES:
1. SELF-DISCOVERY: When exploring a new site or UI (like Drive or GitHub), ALWAYS call `list_keyboard_shortcuts` first. Modern SPAs have rich keyboard shortcuts (e.g. 'c' to compose, '/' to search) that are significantly more reliable than clicking fragile CSS selectors.
2. Prefer `keyboard_shortcut` and `select_option` over DOM clicks whenever possible.
3. After actions you will receive observations. Use them to decide next steps.
4. Output ONLY JSON action objects (one per line). No extra commentary unless answering the user directly.{vision_rule}
"""

    def _get_screenshot_base64(self) -> str:
        """Take a screenshot and return it as base64 string."""
        path = "/tmp/llm_vision_screenshot.png"
        self.conn.screenshot(path)
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _call_llm(self, messages: List[Dict[str, Any]]) -> str:
        """Call LLM, with special handling for vision when needed."""
        if self.backend == "ollama":
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.1},
            }
            resp = requests.post(url, json=payload, timeout=180)
            if resp.status_code == 404:
                try:
                    err_msg = resp.json().get("error", "")
                    if "not found" in err_msg:
                        raise ValueError(
                            f"Ollama error: {err_msg}. Please run 'ollama pull {self.model}' or restart with an installed model (e.g., --model llama3.2)."
                        )
                except (ValueError, json.JSONDecodeError):
                    pass
            resp.raise_for_status()
            return resp.json()["message"]["content"]

        else:  # OpenAI-compatible
            url = f"{self.base_url}/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=180)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    def _parse_actions(self, text: str) -> List[Dict[str, Any]]:
        actions = []
        for line in text.strip().splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    action = json.loads(line)
                    if isinstance(action, dict) and "action" in action:
                        actions.append(action)
                except Exception:
                    pass
        return actions

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action and return observation dict (can include image for vision)."""
        act = action.get("action", "").lower()
        result: Dict[str, Any] = {"action": act}

        try:
            if act == "goto":
                self.conn.goto(action["url"])
                result["observation"] = f"Navigated. Title: {self.conn.get_title()}"

            elif act == "click":
                self.conn.click(action["selector"])
                result["observation"] = (
                    f"Clicked '{action['selector']}'. Title: {self.conn.get_title()}"
                )

            elif act == "select_option":
                self.conn.select_option(
                    action["option"], container=action.get("container")
                )
                result["observation"] = (
                    f"Selected option. Title: {self.conn.get_title()}"
                )

            elif act == "keyboard_shortcut":
                self.conn.keyboard_shortcut(action["keys"])
                time.sleep(0.5)
                result["observation"] = f"Sent keys. URL: {self.conn.get_url()}"

            elif act == "screenshot":
                if self.is_vision_model:
                    b64 = self._get_screenshot_base64()
                    result["image_base64"] = b64
                    result["observation"] = (
                        "Screenshot captured and provided as image to the model."
                    )
                else:
                    path = "/tmp/llm_screenshot.png"
                    self.conn.screenshot(path)
                    result["observation"] = (
                        f"Screenshot saved to {path} (model does not support vision)."
                    )

            elif act == "list_keyboard_shortcuts":
                shortcuts = self.conn.list_keyboard_shortcuts()
                result["observation"] = json.dumps(shortcuts, indent=2)

            else:
                if hasattr(self.conn, act):
                    method = getattr(self.conn, act)
                    if callable(method):
                        args = {k: v for k, v in action.items() if k != "action"}
                        method(**args)
                result["observation"] = f"Executed '{act}'."

            return result

        except Exception as e:
            return {"action": act, "observation": f"Failed: {str(e)}"}

    def run(self):
        print("=" * 70)
        print("Automation Builder \u2014 LLM Chat (Vision Enabled)")
        print(
            f"Backend: {self.backend} | Model: {self.model} | Vision: {self.is_vision_model}"
        )
        print("Talk to the agent. It will control your real browser.")
        print("Type 'quit' to exit.")
        print("=" * 70)

        self.conversation = [{"role": "system", "content": self.system_prompt}]

        state = f"Current URL: {self.conn.get_url()}\nTitle: {self.conn.get_title()}"
        self.conversation.append(
            {"role": "user", "content": f"Initial browser state:\n{state}"}
        )

        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in {"quit", "exit", "q"}:
                    break
                if not user_input:
                    continue

                self.conversation.append({"role": "user", "content": user_input})

                print("🤖 Agent thinking...")
                response_text = self._call_llm(self.conversation)
                print(f"\nAgent:\n{response_text}\n")

                self.conversation.append(
                    {"role": "assistant", "content": response_text}
                )

                actions = self._parse_actions(response_text)
                for action in actions:
                    obs = self.execute_action(action)

                    if "image_base64" in obs:
                        if self.backend == "ollama":
                            self.conversation.append(
                                {
                                    "role": "user",
                                    "content": f"Observation after {action['action']}: {obs.get('observation', '')}",
                                    "images": [obs["image_base64"]],
                                }
                            )
                        else:
                            self.conversation.append(
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"Observation after {action['action']}: {obs.get('observation', '')}",
                                        },
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/png;base64,{obs['image_base64']}"
                                            },
                                        },
                                    ],
                                }
                            )
                    else:
                        self.conversation.append(
                            {
                                "role": "user",
                                "content": f"Observation after {action.get('action')}: {obs.get('observation', '')}",
                            }
                        )

                    print(f"   \u2192 {obs.get('observation', '')}")

                if actions:
                    follow_up = self._call_llm(self.conversation)
                    print(f"\nAgent follow-up:\n{follow_up}\n")
                    self.conversation.append(
                        {"role": "assistant", "content": follow_up}
                    )

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.1")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai"])
    parser.add_argument("--base-url")
    parser.add_argument("--api-key")
    parser.add_argument("--cdp-url", default="http://localhost:9222")
    args = parser.parse_args()

    agent = LLMBrowserAgent(
        model=args.model,
        backend=args.backend,
        base_url=args.base_url,
        api_key=args.api_key,
        cdp_url=args.cdp_url,
    )
    agent.run()


if __name__ == "__main__":
    main()
