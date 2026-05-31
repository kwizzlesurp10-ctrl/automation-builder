#!/usr/bin/env python3
"""
Example: LLM Agent that creates GitHub repositories via natural language.

This demonstrates the power of the LLM + Automation Builder combination
for complex, multi-step authenticated web tasks.
"""

from llm_chat import LLMBrowserAgent

if __name__ == "__main__":
    print("=== GitHub Repo Creator Agent Demo ===\n")
    print("Example prompt you can give the agent:")
    print('"Create a new public GitHub repository called my-automation-tests with Python .gitignore and MIT license"')
    print()

    agent = LLMBrowserAgent(model="llama3.1")
    agent.run()
