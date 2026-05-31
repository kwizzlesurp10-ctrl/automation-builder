#!/usr/bin/env python3
"""
Example: Using Automation Builder as an LLM-powered browser agent.

This demonstrates the core repo concept:
"Use an LLM chat to execute web navigation commands and actions."

Run:
    python examples/llm_browser_agent.py --model llama3.1

The agent will use natural language to control your real logged-in browser.
"""

import argparse
from llm_chat import LLMBrowserAgent

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama3.1")
    parser.add_argument("--backend", default="ollama")
    args = parser.parse_args()

    print("Starting LLM Browser Agent Demo...")
    agent = LLMBrowserAgent(
        model=args.model,
        backend=args.backend,
    )
    agent.run()
