# huggingface-local-models

**Tools, scripts, and a powerful real-browser agent control plane for working with Hugging Face models locally.**

> Powered by CDP-connected Playwright (your real logged-in Chrome), visual observability (glowing panda), keyboard-level control, and swarm-style agent patterns inspired by [browser-assistant-swarm](https://github.com/kwizzlesurp10-ctrl/browser-assistant-swarm).

This repository was created by its own tooling (see `scripts/setup_github_hf_repo.py`).

## Why This Exists

Local inference (llama.cpp, Ollama, GGUF, Transformers.js, etc.) is powerful, but many real workflows still require reliable, authenticated, observable interaction with the web (HF Hub, model cards, Spaces, GitHub, Drive, papers, leaderboards).

This project delivers both:

1. **Local HF model tooling** (GGUF discovery, quant selection, server runners, conversion, OpenAI-compatible serving, etc.)
2. **A production-grade browser agent control plane** that any local LLM or LangGraph-style agent can drive against your real browser sessions.

## The Browser Control Plane (Core IP)

Located in the root Python package + CLI:

- `browser_connector.py` — `WebBrowserConnector` with CDP support for persistent real Chrome
- Full tab management, `execute_script`, `wait_for_navigation`
- Rich keyboard shortcuts + `list_keyboard_shortcuts()` self-discovery for agents
- Visual glowing 🐼 panda indicator (active + searching animation) with configurable auto-trigger
- `--cdp` / auto-detect + persistent profile support
- `drive_chat.py` example of natural-language conversational control
- Robust against real production UIs (used to create this repo itself on GitHub)

See the original development in the sibling `Grok-Playwright-Browser-Connector` work for the full evolution and debugging story.

## Browser Assistant Swarm Concept

This repo directly implements and extends ideas from browser-assistant-swarm / OpenComet:

- Real (not headless) browser as first-class tool for agents
- Local inference (Ollama + the HF local models in this repo) driving multi-step browser tasks
- Observable actions (panda + screenshots + structured output)
- Keyboard + DOM + script surface for reliable control
- Potential future: LangGraph loops, extension sidepanel, dashboard, memory, and approval gates

Future agents running on models from this repo can use the connector as their "eyes and hands" on the authenticated web.

## Quick Start (Browser Control)

```bash
# 1. One-time Chrome debug session (persistent profile with your logins)
python browser_connector.py launch-browser
# (or manually: google-chrome-stable --remote-debugging-port=9222 --user-data-dir=~/.grok-browser-profile)

# 2. Use it
python browser_connector.py --cdp status
python browser_connector.py goto https://huggingface.co
python browser_connector.py list-shortcuts --json
```

## ForgeAI Governance

This repository is governed by **ForgeAI v2.1**. All AI agents (Grok, Cursor, Claude, Aider, Copilot, etc.) **must** follow the full 8-phase professional process defined in [AGENTS.md](./AGENTS.md).

Key files:
- `AGENTS.md` (root)
- `.github/AGENTS.md`
- `.cursor/rules/forgeai.mdc`
- `.forgeai/config.md`

## Roadmap Ideas

- GGUF/quant catalog and downloader scripts
- Local server runners + OpenAI-compatible proxy for models in this repo
- LangGraph / local-LLM multi-step agent that drives the browser connector for HF Hub research, paper reading, model testing, etc.
- Chrome extension sidepanel (in the spirit of browser-assistant-swarm)
- Evaluation harness using the browser control plane

## License

MIT (governance and connector code).

---

**Created with Grok + the Playwright CDP connector + live logged-in browser automation.**
The very automation that built this repo lives inside it.