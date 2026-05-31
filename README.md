# Automation Builder

**Powerful browser automation and agent control plane** — built for real-world, authenticated web tasks.

> Powered by **CDP-connected Playwright** (your real logged-in Chrome), **visual observability** (glowing panda), **keyboard-level control**, and **swarm-style agent patterns** inspired by [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm).

This project gives AI agents (and humans) reliable, observable, keyboard-and-mouse-level control over a real user's already-logged-in browser — without managing credentials yourself.

## Why Automation Builder?

Most browser automation tools are either:
- Headless and fragile (no real logins, no extensions, no state)
- Or too low-level for agents

Automation Builder solves this by combining:

- **Real logged-in browser** via Chrome DevTools Protocol (CDP)
- **Strong observability** with the glowing panda indicator (active + searching modes)
- **Human-like control** through rich keyboard shortcuts + self-discovery (`list_keyboard_shortcuts()`)
- **Robust interaction** including the powerful `select` command for dropdowns, menus, and custom lists
- **Agent-friendly API + CLI** with JSON output, auto-indicator, and tab management

Perfect for building sophisticated automation agents, research tools, workflow builders, or swarm-style multi-agent systems that need to interact with the real web.

## Core Capabilities

- **CDP Real Browser Control** — Attach to your persistent Chrome profile (with all your logins)
- **Glowing Panda Indicator** — Visual feedback when the agent is actively controlling the browser (configurable auto-trigger on actions like `goto`, `click`, `select`)
- **Advanced Selection** — `select_option()` / CLI `select` command with multi-strategy clicking for modern dropdowns and menus
- **Full Keyboard Surface** — Dozens of shortcuts + `list_keyboard_shortcuts()` for agent discovery
- **Tab & Context Management** — Smart reuse, new tabs, switching, close
- **Scripting Superpowers** — `execute_script`, `wait_for_navigation`, robust locators
- **CLI + Python API** — Works great both from the terminal and as tools for LLMs/agents
- **Examples included** — See `examples/` for ready-to-run patterns

## Quick Start

```bash
# 1. Launch a persistent debug Chrome (one-time)
python browser_connector.py launch-browser

# 2. Log into the sites you need in that window

# 3. Control it from code or CLI
python browser_connector.py --cdp goto https://github.com
python browser_connector.py --cdp select "MIT License" --container "Add license"
python browser_connector.py --cdp list-shortcuts --json
```

See the full CLI with:
```bash
python browser_connector.py --help
```

## Examples

```bash
# Python API
conn = WebBrowserConnector(cdp_url="http://localhost:9222", auto_indicator=True)
conn.goto("https://github.com/new")
conn.select_option("Python", container="Add .gitignore")
conn.select_option("MIT License", container="Add license")

# CLI
python browser_connector.py select "Public" --container "Choose visibility"
```

See the `examples/` directory for more runnable demonstrations.

## Browser Assistant Swarm Inspiration

This project draws heavily from the [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm) / OpenComet architecture:

- Real browser as a first-class tool for agents
- Strong observability and structured action surface
- Local inference friendly (works great with Ollama, llama.cpp, etc.)
- Designed for multi-step, long-horizon automation loops

It serves as an excellent reliable "hands and eyes" backend for swarm-style or LangGraph-based browser agents.

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