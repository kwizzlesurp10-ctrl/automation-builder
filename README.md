# Automation Builder

**Powerful browser automation and agent control plane** — built for real-world, authenticated web tasks.

> Powered by **CDP-connected Playwright** (your real logged-in Chrome), **visual observability** (glowing panda), **keyboard-level control**, and **swarm-style agent patterns** inspired by [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm).

This is the source project for Automation Builder — a production-grade toolkit that gives AI agents reliable, observable, keyboard-and-mouse-level control over a real user's already-logged-in browser.

## Why Automation Builder?

Most browser automation is either headless + fragile or too low-level for agents. This project delivers the missing middle:

- Real logged-in browser via Chrome DevTools Protocol (CDP)
- Strong visual observability with the glowing panda (active + searching modes)
- Human-like control via rich keyboard shortcuts + self-discovery
- Robust selection for modern dropdowns/menus (`select` command)
- Agent-friendly Python API + CLI with JSON output and auto-indicator

Perfect for building sophisticated automation agents, research tools, workflow builders, or swarm-style multi-agent systems.

## Core Features

- **CDP Real Browser** — Persistent profile with all your logins, extensions, and cookies
- **Glowing Panda** — Configurable visual indicator (auto-triggers on navigation, clicks, selects, etc.)
- **Powerful Selection** — `select_option()` + CLI `select` for reliable dropdown/menu interaction
- **Full Keyboard Control** — Dozens of shortcuts + `list_keyboard_shortcuts()` for agents
- **Tab Intelligence** — Smart reuse, management, and discovery
- **Rich Scripting** — `execute_script`, `wait_for_navigation`, robust locators
- **CLI + Library** — Works from terminal or as tools for LLMs/agents
- **Examples** — See `examples/` for ready patterns

## Quick Start

```bash
# One-time: launch persistent debug Chrome
python browser_connector.py launch-browser

# Then control it
python browser_connector.py --cdp goto https://github.com
python browser_connector.py --cdp select "MIT License" --container "Add license"
python browser_connector.py --cdp list-shortcuts --json
```

See `python browser_connector.py --help` for the full command set.

## Examples

```python
from browser_connector import WebBrowserConnector

conn = WebBrowserConnector(cdp_url="http://localhost:9222", auto_indicator=True)
conn.goto("https://github.com/new")
conn.select_option("Python", container="Add .gitignore")
conn.select_option("MIT License", container="Add license")
```

See the `examples/` directory for more runnable demonstrations.

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