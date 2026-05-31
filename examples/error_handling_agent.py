#!/usr/bin/env python3
"""
Error Handling Agent for Automation Builder

Demonstrates robust error recovery when an LLM-driven browser agent
encounters failures (element not found, navigation issues, rate limits, etc.).

Key patterns shown:
- Automatic retries with backoff
- LLM-guided recovery (feed error + screenshot to the model)
- Fallback strategies (try keyboard if click fails, alternative selectors)
- Graceful degradation

This is essential for real-world "LLM chat \u2192 web actions" systems.

Usage:
    python examples/error_handling_agent.py --model llama3.1
"""

import time
from typing import Any, Dict

from llm_chat import LLMBrowserAgent


class RobustLLMBrowserAgent(LLMBrowserAgent):
    """Wrapper that adds error handling and recovery around the base agent."""

    def __init__(self, *args, max_retries: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_retries = max_retries

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with retries and error recovery."""
        act = action.get("action", "")
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                result = super().execute_action(action)
                if "Failed" not in result.get("observation", ""):
                    return result
                last_error = result.get("observation")
            except Exception as e:
                last_error = str(e)

            print(f"   [Attempt {attempt}/{self.max_retries}] {act} failed: {last_error}")

            if attempt < self.max_retries:
                # Take screenshot for the LLM to analyze the failure
                try:
                    screenshot_path = "/tmp/error_recovery_screenshot.png"
                    self.conn.screenshot(screenshot_path)
                    print(f"   Screenshot saved for recovery analysis: {screenshot_path}")
                except Exception:
                    pass

                # Ask the LLM for recovery strategy
                recovery_prompt = (
                    f"The action '{act}' failed with error: {last_error}. "
                    "Suggest an alternative approach or corrected parameters. "
                    "Consider using keyboard_shortcut, a different selector, or waiting first."
                )
                self.conversation.append({"role": "user", "content": recovery_prompt})

                print("   Asking LLM for recovery strategy...")
                recovery_response = self._call_llm(self.conversation)
                print(f"   LLM recovery suggestion:\n{recovery_response}\n")

                self.conversation.append({"role": "assistant", "content": recovery_response})

                # Try to parse new actions from the recovery response
                new_actions = self._parse_actions(recovery_response)
                if new_actions:
                    # Execute the first suggested recovery action instead
                    return self.execute_action(new_actions[0])

                time.sleep(1.5 * attempt)  # exponential backoff

        return {
            "action": act,
            "observation": f"Action failed after {self.max_retries} attempts. Last error: {last_error}"
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Error-handling LLM browser agent demo")
    parser.add_argument("--model", default="llama3.1")
    parser.add_argument("--backend", default="ollama")
    args = parser.parse_args()

    print("=== Error Handling Agent Demo ===")
    print("This agent demonstrates automatic retries and LLM-guided error recovery.\n")

    agent = RobustLLMBrowserAgent(
        model=args.model,
        backend=args.backend,
        max_retries=3,
    )
    agent.run()


if __name__ == "__main__":
    main()
