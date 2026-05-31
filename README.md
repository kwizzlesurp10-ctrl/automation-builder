# Automation Builder

**Use an LLM chat to execute web navigation commands and actions** through your real logged-in browser.

> Powered by **CDP-connected Playwright** (your real logged-in Chrome), **visual observability** (glowing panda), **keyboard-level control**, and **swarm-style agent patterns** inspired by [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm).

**Core repo concept**: Chat naturally with an LLM. The model translates your intent into precise browser actions using the full power of Automation Builder.

This is the flagship experience of the project.

## The Vision

Talk to your browser like a human:

- "Go to GitHub, create a new public repo called my-agent-experiments with Python gitignore and MIT license"
- "Open Linear, create a bug report about the panda animation, and assign it to me"
- "Search Hugging Face for the latest Qwen2.5 GGUF models and open the top result"

The LLM uses the rich, discoverable, keyboard-friendly surface (`list_keyboard_shortcuts()`, `select_option`, keyboard shortcuts, etc.) while you watch the glowing panda do the work.

## Flagship Feature: LLM Chat

The main way to use the project is `llm_chat.py` — a conversational interface where an LLM directly controls your real browser.

```bash
# Ollama (recommended)
python llm_chat.py --model llama3.1

# OpenAI-compatible (vLLM, LM Studio, OpenRouter, etc.)
python llm_chat.py --backend openai --base-url http://localhost:8000/v1 --model Qwen2.5-32B
```

**Current capabilities:**
- Clean JSON action format (highly reliable)
- Multi-backend support (Ollama + any OpenAI-compatible server)
- Automatic glowing panda during execution
- Strong self-discovery (`list_keyboard_shortcuts`)
- Screenshot + observation feedback
- Full toolkit access (`select_option`, keyboard control, etc.)

The LLM receives rich observations after every action and can perform complex, multi-step automations.

## Why This Works So Well

- Real logged-in Chrome = all your cookies, 2FA sessions, extensions
- Glowing panda = perfect visual feedback for both you and the LLM
- Strong self-discovery tools (`list_keyboard_shortcuts`, `get_tabs`, etc.)
- Robust `select_option` for the dropdowns and menus that usually break automation
- JSON-friendly + observable results that LLMs can reason over

## Quick Start

```bash
# 1. Launch persistent Chrome (with your real logins)
python browser_connector.py launch-browser

# 2. Make sure Ollama is running with a good model
ollama run llama3.1

# 3. Start chatting
python llm_chat.py
```

Then just describe what you want done on the web. The agent will drive the browser for you.

## Examples

See the `examples/` directory for runnable demonstrations, including `examples/llm_browser_agent.py`.

## Browser Assistant Swarm Connection

This project draws heavily from the [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm) / OpenComet architecture:

- Real browser as a first-class tool for agents
- Strong observability and structured action surface
- Designed for multi-step, long-horizon automation loops
- Excellent backend for local LLM + LangGraph browser agents

## ForgeAI Governance

This repository follows **ForgeAI v2.1** professional engineering governance.

All AI agents working in this repo must follow the process defined in [AGENTS.md](./AGENTS.md).

## Installation

```bash
pip install playwright
playwright install chromium
```

## License

MIT

---

**Built with real logged-in browser automation, the glowing panda, and a lot of debugging against production UIs.**