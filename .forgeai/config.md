# ForgeAI Configuration

This repository uses **ForgeAI v2.1** governance.

## Primary Instruction File
- Root: `AGENTS.md`

## Tool-Specific Overrides
- Cursor: `.cursor/rules/forgeai.mdc`
- GitHub Agents / Copilot: `.github/AGENTS.md`

## Key Behaviors Enforced
- 8-phase professional process
- Explicit approval required before code changes (Phase 2)
- Full quality gates before every commit
- `list_keyboard_shortcuts()` must be used when working with browser automation

## Browser Connector Specifics
- The glowing panda indicator should be respected during browser actions.
- Auto-indicator mode is preferred for navigation-heavy tasks.
- Keyboard shortcuts are the preferred method for efficient browser control.

See root `AGENTS.md` for the complete system instructions.