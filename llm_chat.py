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
- Screenshot + vision feedback support
- Self-discovery via list_keyboard_shortcuts()

Run:
    python llm_chat.py --model llama3.1
    python llm_chat.py --backend openai --base-url http://localhost:8000/v1 --model Qwen2.5-32B

Requirements:
- Chrome running with remote debugging (see launch-browser command)
- Ollama or an OpenAI-compatible server
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
        vision: bool = False,
    ):
        print("Connecting to live Chrome session (CDP)...")
        self.conn = WebBrowserConnector(
            cdp_url=cdp_url,
            auto_indicator=True,
            indicator_label="\ud83e\udd16 LLM Agent",
            indicator_actions={
                "goto", "click", "select_option", "fill", "type",
                "keyboard_shortcut", "wait_for_navigation", "execute_script",
                "new_tab", "switch_to_tab", "reload", "screenshot"
            },
        )
        print("Connected. Glowing panda will appear during actions.\n")

        self.model = model
        self.backend = backend.lower()
        self.base_url = base_url or ("http://localhost:11434" if backend == "ollama" else "http://localhost:8000/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "ollama")
        self.vision = vision
        self.conversation: List[Dict[str, Any]] = []

        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return f"""You are an expert browser automation agent controlling a real logged-in Chrome browser using the Automation Builder toolkit.

Available tools (call them by outputting clean JSON):
{{
  "action": "goto",
  "url": "https://..."
}}
{{
  "action": "click",
  "selector": "text=Submit"   # or role=button, CSS, etc.
}}
{{
  "action": "select_option",
  "option": "MIT License",
  "container": "Add license"   # optional
}}
{{
  "action": "keyboard_shortcut",
  "keys": "Control+L"
}}
{{
  "action": "screenshot",
  "describe": true   # if you want a text description
}}

You also have:
- fill, type, execute_script, wait_for_navigation, new_tab, switch_to_tab, reload
- get_title, get_url, get_tabs, list_keyboard_shortcuts (very useful for discovery)

CRITICAL INSTRUCTIONS:
1. Always call list_keyboard_shortcuts() early if you are unsure of available shortcuts.
2. Prefer keyboard_shortcut and select_option — they are the most reliable.
3. After every action, you will receive an observation (page title, URL, result).
4. If vision is enabled, you can request screenshots and receive descriptions.
5. Be precise. Use the most reliable selector strategy.
6. You can call multiple actions in parallel by outputting multiple JSON objects.

Output ONLY valid JSON action objects (one per line if multiple). Do not add extra text unless you are responding to the user.

Current capabilities include full keyboard control and excellent dropdown/menu selection.
"""

    def _call_llm(self, messages: List[Dict[str, Any]]) -> str:
        """Call the configured LLM backend."""
        if self.backend == "ollama":
            url = f"{self.base_url}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.1},
            }
            resp = requests.post(url, json=payload, timeout=180)
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
        """Parse JSON action objects from LLM output."""
        actions = []
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                action = json.loads(line)
                if isinstance(action, dict) and "action" in action:
                    actions.append(action)
            except json.JSONDecodeError:
                continue
        return actions

    def _take_screenshot_and_describe(self) -> str:
        """Take a screenshot and return a description (text for now)."""
        path = "/tmp/llm_agent_screenshot.png"
        self.conn.screenshot(path)
        # For now we just note that a screenshot was taken.
        # Future: feed base64 to vision models.
        return f"Screenshot saved to {path} (vision feedback not yet wired for this model)."

    def execute_action(self, action: Dict[str, Any]) -> str:
        """Execute one action and return a concise observation."""
        act = action.get("action", "").lower()

        try:
            if act == "goto":
                self.conn.goto(action["url"])
                return f"Navigated to {self.conn.get_url()}. Title: {self.conn.get_title()}"

            elif act == "click":
                self.conn.click(action["selector"])
                return f"Clicked. Current title: {self.conn.get_title()}"

            elif act == "select_option":
                self.conn.select_option(
                    action["option"], container=action.get("container")
                )
                return f"Selected '{action['option']}'. Title: {self.conn.get_title()}"

            elif act == "keyboard_shortcut":
                self.conn.keyboard_shortcut(action["keys"])
                time.sleep(0.5)
                return f"Sent keys '{action['keys']}'. URL: {self.conn.get_url()}"

            elif act == "fill":
                self.conn.fill(action["selector"], action["value"])
                return f"Filled field. Title: {self.conn.get_title()}"

            elif act == "type":
                self.conn.type(action["selector"], action["text"])
                return f"Typed text."

            elif act == "execute_script":
                result = self.conn.execute_script(action["script"])
                return f"Script result: {str(result)[:300]}"

            elif act == "wait_for_navigation":
                url = self.conn.wait_for_navigation(action.get("pattern", "**/*"))
                return f"Navigation complete. URL: {url}"

            elif act == "screenshot":
                return self._take_screenshot_and_describe()

            elif act == "new_tab":
                url = self.conn.new_tab(action.get("url"))
                return f"New tab opened: {url}"

            elif act == "switch_to_tab":
                url = self.conn.switch_to_tab(int(action["index"]))
                return f"Switched to tab. URL: {url}"

            elif act == "reload":
                self.conn.reload()
                return f"Reloaded. Title: {self.conn.get_title()}"

            elif act == "list_keyboard_shortcuts":
                shortcuts = self.conn.list_keyboard_shortcuts()
                return f"Available shortcuts: {json.dumps(shortcuts, indent=2)}"

            else:
                return f"Unknown action: {act}"

        except Exception as e:
            return f"Action '{act}' failed: {str(e)}"

    def run(self):
        print("=" * 70)
        print("Automation Builder \u2014 LLM Chat (v2)")
        print(f"Backend: {self.backend} | Model: {self.model}")
        print("Talk to the agent. It will control your real browser.")
        print("Type 'quit' to exit.")
        print("=" * 70)
        print()

        self.conversation = [{"role": "system", "content": self.system_prompt}]

        # Seed with current state
        state = f"Current URL: {self.conn.get_url()}\nTitle: {self.conn.get_title()}"
        self.conversation.append({
            "role": "user",
            "content": f"Browser state:\n{state}\n\nWhat would you like to automate?"
        })

        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in {"quit", "exit", "q"}:
                    break
                if not user_input:
                    continue

                self.conversation.append({"role": "user", "content": user_input})

                print("\ud83e\udd16 Agent thinking...")
                response = self._call_llm(self.conversation)
                print(f"\nAgent:\n{response}\n")

                self.conversation.append({"role": "assistant", "content": response})

                actions = self._parse_actions(response)
                if actions:
                    print("▶ Executing actions...")
                    for action in actions:
                        observation = self.execute_action(action)
                        print(f"   {observation}")
                        self.conversation.append({
                            "role": "user",
                            "content": f"Observation: {observation}"
                        })

                    # Let the model react to the observations
                    follow_up = self._call_llm(self.conversation)
                    print(f"\nAgent follow-up:\n{follow_up}\n")
                    self.conversation.append({"role": "assistant", "content": follow_up})

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="LLM-powered browser automation chat")
    parser.add_argument("--model", default="llama3.1", help="Model name")
    parser.add_argument("--backend", default="ollama", choices=["ollama", "openai"], help="LLM backend")
    parser.add_argument("--base-url", help="Base URL for the LLM server")
    parser.add_argument("--api-key", help="API key (for OpenAI-compatible backends)")
    parser.add_argument("--cdp-url", default="http://localhost:9222")
    parser.add_argument("--vision", action="store_true", help="Enable vision/screenshot feedback (future)")

    args = parser.parse_args()

    agent = LLMBrowserAgent(
        model=args.model,
        backend=args.backend,
        base_url=args.base_url,
        api_key=args.api_key,
        cdp_url=args.cdp_url,
        vision=args.vision,
    )
    agent.run()


if __name__ == "__main__":
    main()
