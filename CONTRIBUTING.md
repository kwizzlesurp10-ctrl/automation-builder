# Contributing to Automation Builder

Thank you for your interest in improving Automation Builder \u2014 the LLM-powered browser automation toolkit.

## Core Philosophy

- The browser is a **first-class tool** for agents.
- Real logged-in Chrome (via CDP) > headless browsers.
- Observability matters: the glowing panda is not just cute \u2014 it's critical feedback.
- LLMs should be able to discover capabilities (`list_keyboard_shortcuts`, etc.).
- Reliability > cleverness (prefer `select_option` and keyboard shortcuts).

## Development Setup

```bash
git clone https://github.com/kwizzlesurp10-ctrl/automation-builder.git
cd automation-builder

# Install
pip install -e ".[dev]"

# Start Chrome debug session
python browser_connector.py launch-browser

# Run the LLM chat
python llm_chat.py --model llama3.1
```

## Adding New Capabilities

When adding new actions to the connector or `llm_chat.py`:

1. Add the method to `WebBrowserConnector` with clear docstrings.
2. Update the system prompt in `llm_chat.py`.
3. Add the action name to `indicator_actions` if it should trigger the panda.
4. Add an example in `examples/`.

## Testing

- Test against real sites (GitHub, Linear, Notion, etc.).
- Always test with the glowing panda enabled.
- Prefer keyboard + `select_option` flows in examples.

## Commit Style

We follow Conventional Commits.

Good examples:
- `feat: add real vision support with base64 screenshots`
- `docs: improve llm_chat system prompt for better tool use`
- `example: add GitHub repository creation agent`

## Questions?

Open an issue or start a discussion. We're particularly interested in:
- Better LLM tool-calling patterns
- Vision model integrations
- New high-value example agents
- Reliability improvements for tricky UIs

Let's build the best browser control plane for LLM agents.
