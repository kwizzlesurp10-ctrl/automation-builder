#!/usr/bin/env python3
"""
Playwright Web Browser Connector
Minimal sync browser automation for agents / Grok.
Supports launching Chromium or connecting to an existing Chrome session via CDP
(for full control of a visible browser with your cookies/logins).

Key features:
- goto, click, fill, type, extract, evaluate, execute_script, screenshot, cookies
- **select_option** — robust "click to select" for dropdowns/menus (the real-world pattern)
- Full tab management (get_tabs, switch_to_tab, new_tab, close_tab, etc.)
- Rich keyboard navigation support + `list_keyboard_shortcuts()` for agent discovery
- Waiting helpers: wait_for_selector, wait_for_navigation
- Works great in both headless and live CDP mode
- Sync API, easy to expose as tools
- CLI support for "select" (click-based option selection) and "click"

Install:
  pip install playwright
  playwright install chromium

Basic usage:
  from browser_connector import WebBrowserConnector
  conn = WebBrowserConnector(headless=True)
  conn.goto("https://example.com")
  print(conn.get_title())
  conn.close()

Real logged-in browser (strongly recommended for agents):

Grok can discover all available keyboard navigation options:
```python
conn = WebBrowserConnector(cdp_url="http://localhost:9222")
shortcuts = conn.list_keyboard_shortcuts()   # Ask this first!
conn.keyboard_shortcut("Control+L")          # Then use them naturally
```

Example with automatic searching indicator during web navigation:

```python
from browser_connector import WebBrowserConnector
import time

# Connect to your real logged-in Chrome (started with launch-browser)
conn = WebBrowserConnector(
    cdp_url="http://localhost:9222",
    auto_indicator=True,                    # Enable auto panda
    indicator_label="\ud83d\udc3c Grok",
    indicator_actions={"goto", "new_tab", "wait_for_navigation"}  # Configurable
)

# The glowing "searching" panda will automatically appear during these actions
print("Navigating to Google...")
conn.goto("https://www.google.com")

print("Searching for something...")
conn.fill("textarea[name=q]", "xAI Grok")
conn.execute_script("document.querySelector('form').submit()")
conn.wait_for_navigation("**/search**")

print("Current page:", conn.get_title())
print("Links found:", len(conn.get_links()))

# You can also manually control it
conn.show_glowing_panda("\ud83d\udc3c Analyzing results", mode="searching")
time.sleep(2)
conn.hide_glowing_panda()

conn.close()  # Only closes the page in CDP mode, not your browser
```

CLI equivalent with auto indicator:
```bash
python browser_connector.py --auto-indicator goto https://www.google.com
python browser_connector.py --auto-indicator --indicator-actions "goto,wait_for_navigation" \
    wait-for-navigation "**/search**"
```
"""

from playwright.sync_api import sync_playwright
from typing import Optional, Any, Iterable, Set
import json
import time

class WebBrowserConnector:
    def __init__(self, headless: bool = True, cdp_url: Optional[str] = None, reuse_page: bool = True,
                 auto_indicator: bool = False, indicator_label: str = "\ud83d\udc3c Grok",
                 indicator_actions: Optional[Iterable[str]] = None):
        """
        Args:
            headless: Used only when launching a new browser (not CDP).
            cdp_url: If provided, connect to an existing Chrome via CDP.
            reuse_page: 
                - True (default): In CDP mode, try to reuse an existing page/tab instead of always opening a new blank one.
                  This prevents the "new blank tabs keep opening" problem.
                - False: Always create a fresh new tab (old behavior).
            auto_indicator: If True, automatically show the glowing panda "searching" indicator 
                           during the actions listed in `indicator_actions`.
            indicator_label: Text shown next to the panda when using auto_indicator.
            indicator_actions: Set of method names that should trigger the searching indicator automatically.
                               Defaults to {"goto", "new_tab", "reload", "wait_for_navigation"}.
                               You can customize this, e.g. {"goto", "click"} or pass an empty set to disable.
        """
        self.pw = sync_playwright().start()
        self._auto_indicator = auto_indicator
        self._indicator_label = indicator_label

        default_actions = {"goto", "new_tab", "reload", "wait_for_navigation"}
        if indicator_actions is None:
            self._indicator_actions = default_actions
        else:
            self._indicator_actions = set(indicator_actions)

        if cdp_url:
            self.browser = self.pw.chromium.connect_over_cdp(cdp_url)
            self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()

            if reuse_page and self.context.pages:
                # Reuse the last active page instead of spamming new blank tabs
                self.page = self.context.pages[-1]
            else:
                self.page = self.context.new_page()
        else:
            self.browser = self.pw.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()

    def goto(self, url: str) -> str:
        self._show_searching_indicator("goto")
        try:
            self.page.goto(url, wait_until="domcontentloaded")
            return self.page.url
        finally:
            self._hide_indicator("goto")

    def click(self, selector: str) -> None:
        """Click an element using Playwright selector syntax (CSS, text=, role=, etc.)."""
        self._show_searching_indicator("click")
        try:
            self.page.click(selector)
        finally:
            self._hide_indicator("click")

    def select_option(self, option: str, container: Optional[str] = None, timeout: int = 8000) -> None:
        """
        Robust "click to select" for dropdowns, menus, radio groups, and custom lists.

        This is the dedicated helper for selecting options via clicking (the primary
        real-world pattern for modern UIs that don't use native <select>).

        Args:
            option: Visible text of the option to click (e.g. "MIT License", "Python").
            container: Optional selector or visible label of the dropdown/menu trigger
                       (e.g. "Add license", ".gitignore template", "Choose visibility").
            timeout: Max wait per click attempt.

        Examples (CLI or code):
            conn.select_option("MIT License", container="Add license")
            conn.select_option("Python", container="Add .gitignore")

            # CLI:
            # python browser_connector.py select "MIT License" --container "Add license"
        """
        self._show_searching_indicator("select")
        try:
            if container:
                # Open the dropdown / menu / popover first
                try:
                    # Try direct container click
                    c = self.page.locator(container).first
                    if c.count() > 0:
                        c.click()
                    else:
                        self.page.get_by_text(container, exact=False).first.click()
                except Exception:
                    # Very last attempt - raw text click on container label
                    self.page.click(f"text={container}")
                time.sleep(0.35)  # allow animation / popover to appear

            # Multiple robust strategies for finding the clickable option (in priority order)
            strategies = [
                lambda: self.page.get_by_role("menuitem", name=option),
                lambda: self.page.get_by_role("option", name=option),
                lambda: self.page.get_by_text(option, exact=False),
                lambda: self.page.locator(f"button:has-text('{option}')"),
                lambda: self.page.locator(f"[role*='menuitem']:has-text('{option}'), [role*='option']:has-text('{option}')"),
                lambda: self.page.locator(f"li:has-text('{option}'), div[role='option']:has-text('{option}')"),
            ]

            clicked = False
            for get_loc in strategies:
                try:
                    loc = get_loc()
                    if loc.count() > 0:
                        loc.first.click(timeout=timeout)
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                # Final fallback - Playwright text selector
                self.page.click(f"text={option}")
        finally:
            self._hide_indicator("select")

    def fill(self, selector: str, value: str) -> None:
        self.page.fill(selector, value)

    def type(self, selector: str, text: str, delay: int = 0) -> None:
        self.page.type(selector, text, delay=delay)

    def extract_text(self, selector: str) -> str:
        """Extract text from the first matching element (uses .first to avoid strict mode errors on real pages)."""
        return self.page.locator(selector).first.inner_text()

    def extract_html(self, selector: str) -> str:
        """Extract HTML from the first matching element."""
        return self.page.locator(selector).first.inner_html()

    def screenshot(self, path: str = "screenshot.png") -> str:
        self.page.screenshot(path=path)
        return path

    def evaluate(self, expression: str) -> Any:
        """Execute JavaScript expression and return the result (low-level)."""
        return self.page.evaluate(expression)

    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the current page context.
        Designed to feel similar to Selenium's execute_script.

        Supports common patterns:
            conn.execute_script("return document.title")
            conn.execute_script("document.title")
            conn.execute_script("() => document.title")
            conn.execute_script("return arguments[0].innerText", element)

        Automatically handles "return ..." prefix for convenience.
        """
        script = script.strip()

        # Handle the very common Selenium-style "return foo" pattern
        if script.startswith("return "):
            script = script[7:].strip()

        try:
            if args:
                return self.page.evaluate(script, *args)
            return self.page.evaluate(script)
        except Exception as e:
            # Fallback: wrap as an IIFE if we hit "Illegal return statement"
            if "Illegal return statement" in str(e):
                # Wrap the original (or stripped) script
                wrapped = f"(() => {{ {script} }})()"
                if args:
                    return self.page.evaluate(wrapped, *args)
                return self.page.evaluate(wrapped)
            raise

    def get_cookies(self) -> list:
        return self.context.cookies()

    def set_cookies(self, cookies: list) -> None:
        self.context.add_cookies(cookies)

    # =====================
    # Tab Management (especially powerful when connected via CDP to a live browser)
    # =====================

    def get_tabs(self) -> list[dict]:
        """Return information about all open tabs/pages in the current browser context."""
        tabs = []
        for i, p in enumerate(self.context.pages):
            try:
                tabs.append({
                    "index": i,
                    "url": p.url,
                    "title": p.title(),
                    "is_current": p == self.page
                })
            except Exception:
                tabs.append({
                    "index": i,
                    "url": "about:blank",
                    "title": "<error reading tab>",
                    "is_current": False
                })
        return tabs

    def get_current_tab(self) -> dict:
        """Return info about the currently active tab."""
        try:
            return {
                "url": self.page.url,
                "title": self.page.title()
            }
        except Exception:
            return {"url": self.page.url, "title": "<error>"}

    def switch_to_tab(self, index: int) -> str:
        """Switch the active page to the tab at the given index. Returns the new URL."""
        pages = self.context.pages
        if 0 <= index < len(pages):
            self.page = pages[index]
            return self.page.url
        raise IndexError(f"Tab index {index} out of range (0-{len(pages)-1}). Use get_tabs() first.")

    def switch_to_tab_by_url(self, url_contains: str) -> str:
        """Switch to the first tab whose URL contains the given string. Returns the URL or raises if not found."""
        for i, p in enumerate(self.context.pages):
            if url_contains.lower() in p.url.lower():
                self.page = p
                return p.url
        raise ValueError(f"No tab found containing '{url_contains}' in URL. Use get_tabs().")

    def new_tab(self, url: Optional[str] = None) -> str:
        """Open a new tab (and optionally navigate to a URL). Switches active page to the new tab."""
        self._show_searching_indicator("new_tab")
        try:
            new_page = self.context.new_page()
            self.page = new_page
            if url:
                return self.goto(url)
            return self.page.url
        finally:
            self._hide_indicator("new_tab")

    # --- Keyboard Shortcuts for Browser Navigation ---

    def keyboard_shortcut(self, keys: str) -> None:
        """
        Send a keyboard shortcut or key combination.
        Examples:
            conn.keyboard_shortcut("Control+L")        # Focus address bar (Linux/Windows)
            conn.keyboard_shortcut("Meta+L")           # Focus address bar (macOS)
            conn.keyboard_shortcut("Control+T")        # New tab
            conn.keyboard_shortcut("Control+Shift+T")  # Reopen closed tab
            conn.keyboard_shortcut("Control+W")        # Close tab
            conn.keyboard_shortcut("Control+R")        # Reload
            conn.keyboard_shortcut("Control+Shift+R")  # Hard reload (no cache)
            conn.keyboard_shortcut("Alt+ArrowLeft")  # Go back
            conn.keyboard_shortcut("Alt+ArrowRight")   # Go forward
            conn.keyboard_shortcut("Control+Tab")      # Next tab
            conn.keyboard_shortcut("Control+Shift+Tab")# Previous tab
            conn.keyboard_shortcut("F5")               # Reload
        """
        self.page.keyboard.press(keys)

    def focus_address_bar(self) -> None:
        """Focus the address bar (Ctrl+L / Cmd+L)."""
        # Try both common modifiers for maximum compatibility
        try:
            self.keyboard_shortcut("Control+L")
        except Exception:
            self.keyboard_shortcut("Meta+L")

    def new_tab_shortcut(self) -> None:
        """Open a new tab using the standard keyboard shortcut."""
        try:
            self.keyboard_shortcut("Control+T")
        except Exception:
            self.keyboard_shortcut("Meta+T")

    def close_current_tab_shortcut(self) -> None:
        """Close the current tab using the standard keyboard shortcut."""
        try:
            self.keyboard_shortcut("Control+W")
        except Exception:
            self.keyboard_shortcut("Meta+W")

    def reopen_closed_tab_shortcut(self) -> None:
        """Reopen the last closed tab."""
        try:
            self.keyboard_shortcut("Control+Shift+T")
        except Exception:
            self.keyboard_shortcut("Meta+Shift+T")

    def reload_shortcut(self, hard: bool = False) -> None:
        """Reload the current page using keyboard shortcut."""
        if hard:
            try:
                self.keyboard_shortcut("Control+Shift+R")
            except Exception:
                self.keyboard_shortcut("Meta+Shift+R")
        else:
            try:
                self.keyboard_shortcut("Control+R")
            except Exception:
                self.keyboard_shortcut("Meta+R")

    def go_back_shortcut(self) -> None:
        """Navigate back in history using keyboard shortcut."""
        try:
            self.keyboard_shortcut("Alt+ArrowLeft")
        except Exception:
            self.keyboard_shortcut("Meta+ArrowLeft")

    def go_forward_shortcut(self) -> None:
        """Navigate forward in history using keyboard shortcut."""
        try:
            self.keyboard_shortcut("Alt+ArrowRight")
        except Exception:
            self.keyboard_shortcut("Meta+ArrowRight")

    def next_tab_shortcut(self) -> None:
        """Switch to the next tab."""
        try:
            self.keyboard_shortcut("Control+Tab")
        except Exception:
            self.keyboard_shortcut("Meta+Tab")

    def previous_tab_shortcut(self) -> None:
        """Switch to the previous tab."""
        try:
            self.keyboard_shortcut("Control+Shift+Tab")
        except Exception:
            self.keyboard_shortcut("Meta+Shift+Tab")

    def find_in_page_shortcut(self) -> None:
        """Open the in-page find/search bar."""
        try:
            self.keyboard_shortcut("Control+F")
        except Exception:
            self.keyboard_shortcut("Meta+F")

    # --- Additional Common Browser Keyboard Shortcuts ---

    def open_devtools_shortcut(self) -> None:
        """Open Chrome DevTools (F12 / Ctrl+Shift+I)."""
        try:
            self.keyboard_shortcut("F12")
        except Exception:
            try:
                self.keyboard_shortcut("Control+Shift+I")
            except Exception:
                self.keyboard_shortcut("Meta+Alt+I")

    def open_console_shortcut(self) -> None:
        """Open the JavaScript console (Ctrl+Shift+J)."""
        try:
            self.keyboard_shortcut("Control+Shift+J")
        except Exception:
            self.keyboard_shortcut("Meta+Alt+J")

    def open_bookmarks_shortcut(self) -> None:
        """Open bookmarks manager (Ctrl+Shift+O)."""
        try:
            self.keyboard_shortcut("Control+Shift+O")
        except Exception:
            self.keyboard_shortcut("Meta+Shift+O")

    def bookmark_page_shortcut(self) -> None:
        """Bookmark the current page (Ctrl+D)."""
        try:
            self.keyboard_shortcut("Control+D")
        except Exception:
            self.keyboard_shortcut("Meta+D")

    def open_history_shortcut(self) -> None:
        """Open browsing history (Ctrl+H)."""
        try:
            self.keyboard_shortcut("Control+H")
        except Exception:
            self.keyboard_shortcut("Meta+Y")  # macOS sometimes uses this

    def open_downloads_shortcut(self) -> None:
        """Open downloads page (Ctrl+J)."""
        try:
            self.keyboard_shortcut("Control+J")
        except Exception:
            self.keyboard_shortcut("Meta+Shift+J")

    def view_page_source_shortcut(self) -> None:
        """View page source (Ctrl+U)."""
        try:
            self.keyboard_shortcut("Control+U")
        except Exception:
            self.keyboard_shortcut("Meta+U")

    def toggle_fullscreen_shortcut(self) -> None:
        """Toggle fullscreen mode (F11)."""
        self.keyboard_shortcut("F11")

    def zoom_in_shortcut(self) -> None:
        """Zoom in (Ctrl++)."""
        try:
            self.keyboard_shortcut("Control+Plus")
        except Exception:
            self.keyboard_shortcut("Meta+Plus")

    def zoom_out_shortcut(self) -> None:
        """Zoom out (Ctrl+-)."""
        try:
            self.keyboard_shortcut("Control+Minus")
        except Exception:
            self.keyboard_shortcut("Meta+Minus")

    def zoom_reset_shortcut(self) -> None:
        """Reset zoom to 100% (Ctrl+0)."""
        try:
            self.keyboard_shortcut("Control+0")
        except Exception:
            self.keyboard_shortcut("Meta+0")

    def list_keyboard_shortcuts(self) -> dict:
        """
        Return a structured dictionary of all supported keyboard shortcuts.
        Extremely useful for agents/Grok to discover what navigation actions are available.
        """
        return {
            "address_bar": "Control+L or Meta+L",
            "new_tab": "Control+T or Meta+T",
            "close_tab": "Control+W or Meta+W",
            "reopen_closed_tab": "Control+Shift+T or Meta+Shift+T",
            "reload": "Control+R or Meta+R or F5",
            "hard_reload": "Control+Shift+R or Meta+Shift+R",
            "go_back": "Alt+ArrowLeft or Meta+ArrowLeft",
            "go_forward": "Alt+ArrowRight or Meta+ArrowRight",
            "next_tab": "Control+Tab or Meta+Tab",
            "previous_tab": "Control+Shift+Tab or Meta+Shift+Tab",
            "find_in_page": "Control+F or Meta+F",
            "devtools": "F12 or Control+Shift+I or Meta+Alt+I",
            "console": "Control+Shift+J or Meta+Alt+J",
            "bookmarks_manager": "Control+Shift+O or Meta+Shift+O",
            "bookmark_page": "Control+D or Meta+D",
            "history": "Control+H or Meta+Y",
            "downloads": "Control+J or Meta+Shift+J",
            "view_source": "Control+U or Meta+U",
            "fullscreen": "F11",
            "zoom_in": "Control+Plus or Meta+Plus",
            "zoom_out": "Control+Minus or Meta+Minus",
            "zoom_reset": "Control+0 or Meta+0",
        }

    def close_tab(self, index: Optional[int] = None) -> None:
        """Close a tab. If index is None, closes the current tab and tries to switch to another open tab."""
        pages = self.context.pages
        if index is None:
            page_to_close = self.page
            # Switch to another tab if possible before closing
            if len(pages) > 1:
                for p in pages:
                    if p != self.page:
                        self.page = p
                        break
            page_to_close.close()
        else:
            if 0 <= index < len(pages):
                pages[index].close()
            else:
                raise IndexError(f"Invalid tab index {index}")

    # =====================
    # Convenience & Robust Utility Methods
    # =====================

    def get_title(self) -> str:
        """Get the title of the current page (recommended over extract_text('title'))."""
        return self.page.title()

    def get_url(self) -> str:
        """Get the current URL."""
        return self.page.url

    def reload(self) -> str:
        """Reload the current page."""
        self._show_searching_indicator("reload")
        try:
            self.page.reload(wait_until="domcontentloaded")
            return self.page.url
        finally:
            self._hide_indicator("reload")

    def bring_to_front(self) -> None:
        """Bring the current page/tab to the front (useful in visible/CDP mode)."""
        self.page.bring_to_front()

    def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for a selector to appear. Returns True if found, False on timeout."""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    def wait_for_navigation(self, url_pattern: str = "**/*", timeout: int = 30000, wait_until: str = "domcontentloaded") -> str:
        """
        Wait for a navigation to complete (or until the URL matches the pattern).
        Very useful after clicking buttons/links that cause page changes.

        Args:
            url_pattern: Playwright URL pattern (e.g. "**/*", "**/dashboard", "https://**")
            timeout: Max time to wait in ms
            wait_until: 'domcontentloaded', 'load', 'networkidle', etc.

        Returns:
            The final URL after navigation.
        """
        self._show_searching_indicator("wait_for_navigation")
        try:
            try:
                self.page.wait_for_url(url_pattern, timeout=timeout, wait_until=wait_until)
            except Exception:
                # Fallback: still return current URL even if pattern didn't match in time
                pass
            return self.page.url
        finally:
            self._hide_indicator("wait_for_navigation")

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page."""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    def get_links(self) -> list[str]:
        """Return all href links on the current page."""
        try:
            return self.page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        except Exception:
            return []

    def extract_text_safe(self, selector: str) -> Optional[str]:
        """Safer text extraction that uses .first and never raises on missing elements."""
        try:
            loc = self.page.locator(selector).first
            if loc.count() > 0:
                return loc.inner_text()
        except Exception:
            pass
        return None

    # --- Auth / Storage State (very useful with real logged-in CDP profiles) ---

    def save_storage_state(self, path: str = "auth_state.json") -> str:
        """
        Export cookies + localStorage + sessionStorage to a JSON file.
        Useful for persisting logins across sessions or sharing auth with agents.
        """
        state = self.context.storage_state(path=path)
        return path

    def load_storage_state(self, path: str = "auth_state.json") -> None:
        """
        Load previously saved cookies/storage state into the current context.
        Note: Works best when creating a fresh context. In CDP mode this may have limited effect.
        """
        self.context.add_cookies([])  # no-op placeholder; real load usually happens at context creation
        # For CDP connected contexts, we recommend the user logs in manually once
        # and then uses save_storage_state for backup.

    def get_cookies_for_domain(self, domain: str) -> list:
        """Return cookies for a specific domain (helpful for debugging logged-in state)."""
        all_cookies = self.context.cookies()
        return [c for c in all_cookies if domain in c.get("domain", "")]

    # --- Visual Activity Indicator (Glowing Panda for when Grok is using the browser) ---

    def show_glowing_panda(self, label: str = "\ud83d\udc3c Grok", mode: str = "active") -> None:
        """
        Injects a glowing panda indicator in the bottom-right corner of the current page.
        Uses safe DOM creation to work on sites with strict CSP (like GitHub).
        """
        is_searching = mode.lower() == "searching"
        glow_color = "0, 200, 255" if is_searching else "0, 255, 140"
        animation_speed = "1.1s" if is_searching else "2s"
        extra_class = "searching" if is_searching else ""

        # Escape for JS
        safe_label = label.replace("'", "\\'").replace("\n", " ")

        js = f"""
        (function() {{
            const ID = 'grok-active-indicator';
            let el = document.getElementById(ID);
            if (!el) {{
                el = document.createElement('div');
                el.id = ID;
                el.style.position = 'fixed';
                el.style.bottom = '16px';
                el.style.right = '16px';
                el.style.zIndex = '2147483647';
                el.style.pointerEvents = 'none';
                el.style.display = 'flex';
                el.style.alignItems = 'center';
                el.style.gap = '6px';
                el.style.padding = '6px 12px';
                el.style.borderRadius = '9999px';
                el.style.fontFamily = 'system-ui, -apple-system, sans-serif';
                el.style.fontSize = '13px';
                el.style.fontWeight = '600';
                el.style.color = '#ffffff';
                el.style.background = 'rgba(0, 0, 0, 0.78)';
                el.style.border = '1px solid rgba(255,255,255,0.15)';
                el.style.transition = 'all 0.2s ease';
                document.body.appendChild(el);
            }}

            el.innerHTML = '';
            const panda = document.createElement('span');
            panda.style.fontSize = '15px';
            panda.style.lineHeight = '1';
            panda.textContent = '\ud83d\udc3c';
            el.appendChild(panda);

            const labelSpan = document.createElement('span');
            labelSpan.style.letterSpacing = '0.3px';
            labelSpan.textContent = '{safe_label}';
            el.appendChild(labelSpan);

            el.className = '{extra_class}';

            if (!document.getElementById('grok-indicator-style')) {{
                const style = document.createElement('style');
                style.id = 'grok-indicator-style';
                style.textContent = `
                    @keyframes grok-glow {{
                        0%, 100% {{ box-shadow: 0 0 0 1px rgba({glow_color}, 0.3), 0 0 12px rgba({glow_color}, 0.6), 0 0 24px rgba({glow_color}, 0.4); }}
                        50% {{ box-shadow: 0 0 0 1px rgba({glow_color}, 0.55), 0 0 20px rgba({glow_color}, 0.95), 0 0 40px rgba({glow_color}, 0.65); }}
                    }}
                    #grok-active-indicator {{
                        animation: grok-glow {animation_speed} ease-in-out infinite;
                    }}
                    #grok-active-indicator.searching {{
                        animation: grok-glow 1.1s ease-in-out infinite;
                        background: rgba(0, 0, 0, 0.82);
                    }}
                `;
                document.head.appendChild(style);
            }}
        }})();
        """
        self.page.evaluate(js)

    def hide_glowing_panda(self) -> None:
        """Removes the glowing panda indicator from the current page."""
        js = """
        (function() {
            const el = document.getElementById('grok-active-indicator');
            if (el) el.remove();
            const style = document.getElementById('grok-indicator-style');
            if (style) style.remove();
        })();
        """
        self.page.evaluate(js)

    def set_grok_active(self, active: bool, label: str = "\ud83d\udc3c Grok") -> None:
        """Convenience method to show or hide the indicator."""
        if active:
            self.show_glowing_panda(label)
        else:
            self.hide_glowing_panda()

    def enable_auto_indicator(self, label: Optional[str] = None, actions: Optional[Iterable[str]] = None):
        """Enable automatic searching panda during configured actions."""
        self._auto_indicator = True
        if label:
            self._indicator_label = label
        if actions is not None:
            self._indicator_actions = set(actions)

    def disable_auto_indicator(self):
        """Disable automatic indicator and hide current one if visible."""
        self._auto_indicator = False
        self.hide_glowing_panda()

    # --- Auto Indicator Helpers ---

    def _show_searching_indicator(self, action: str = None):
        """Internal: Show the searching variant if auto_indicator is enabled for this action."""
        if getattr(self, '_auto_indicator', False):
            actions = getattr(self, '_indicator_actions', {"goto", "new_tab", "reload", "wait_for_navigation"})
            if action is None or action in actions:
                label = getattr(self, '_indicator_label', "\ud83d\udc3c Grok")
                self.show_glowing_panda(label, mode="searching")

    def _hide_indicator(self, action: str = None):
        """Internal: Hide indicator if auto_indicator is enabled for this action."""
        if getattr(self, '_auto_indicator', False):
            actions = getattr(self, '_indicator_actions', {"goto", "new_tab", "reload", "wait_for_navigation"})
            if action is None or action in actions:
                self.hide_glowing_panda()

    def close(self) -> None:
        self.context.close()
        self.browser.close()
        self.pw.stop()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

# =============================================================================
# CLI for Commanding Web Navigation (designed for agents / Grok tool use)
# =============================================================================

def _get_connector(args) -> 'WebBrowserConnector':
    """
    Smart connector factory.

    - If --cdp / --live is passed → force CDP mode (real logged-in browser).
    - If no flag is passed, auto-detect if a Chrome debug session is running on the port.
      This makes "control a real, logged-in browser" the path of least resistance.
    - reuse_page=True by default in CDP mode to avoid spawning tons of blank tabs.
    """
    import socket

    cdp_url = getattr(args, 'cdp_url', None) or "http://localhost:9222"
    force_cdp = getattr(args, 'cdp', False) or getattr(args, 'live', False)

    def _is_port_open(host: str, port: int, timeout: float = 0.8) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ConnectionRefusedError):
            return False

    try:
        port = int(cdp_url.rsplit(":", 1)[-1].split("/")[0])
    except Exception:
        port = 9222

    reuse = not getattr(args, 'new_tab', False)
    auto_ind = getattr(args, 'auto_indicator', False)
    ind_label = getattr(args, 'indicator_label', "\ud83d\udc3c Grok")
    ind_actions_str = getattr(args, 'indicator_actions', "")
    ind_actions = None
    if ind_actions_str:
        ind_actions = {a.strip() for a in ind_actions_str.split(",") if a.strip()}

    if force_cdp or _is_port_open("127.0.0.1", port):
        return WebBrowserConnector(cdp_url=cdp_url, reuse_page=reuse,
                                   auto_indicator=auto_ind, indicator_label=ind_label,
                                   indicator_actions=ind_actions)

    # Fallback to new headless browser
    headless = not getattr(args, 'visible', False)
    return WebBrowserConnector(headless=headless, reuse_page=False)


def _print_result(data, use_json: bool):
    """Print result in human or JSON format."""
    if use_json:
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"{k}: {v}")
        elif isinstance(data, list):
            for item in data:
                print(item)
        else:
            print(data)


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Web Browser Connector CLI - Command web navigation from the terminal / agents.",
        epilog="""
=== Recommended: Control a REAL logged-in browser ===

1. One-time setup (run this once):
   python browser_connector.py launch-browser

2. Log into sites in that Chrome window. Keep it running.

3. Normal commands now reuse your current tab by default (no more blank tab spam).

   With --auto-indicator, the glowing searching panda will automatically appear during navigation.

   Even better — use the built-in demo:
   python browser_connector.py demo
   python browser_connector.py demo --label "\ud83d\udc3c Grok" --actions "goto,wait_for_navigation"

   Use --new-tab if you explicitly want a fresh tab.

Other useful commands:
  python browser_connector.py status
  python browser_connector.py launch-browser
  python browser_connector.py show-indicator --label "\ud83d\udc3c Searching..."
  python browser_connector.py hide-indicator
  python browser_connector.py demo
  python browser_connector.py demo --auto-indicator --label "\ud83d\udc3c Grok" --actions "goto,wait_for_navigation"

Keyboard navigation shortcuts (Grok-friendly):
  python browser_connector.py shortcut "Control+L"
  python browser_connector.py back
  python browser_connector.py forward
  python browser_connector.py reload-shortcut --hard
  python browser_connector.py devtools
  python browser_connector.py list-shortcuts          # ← Very useful for agents

Examples:
  python browser_connector.py goto https://supabase.com
  python browser_connector.py --json tabs
  python browser_connector.py click "text=Sign in"
  python browser_connector.py execute-script "return document.title" --json
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Global options
    parser.add_argument("--cdp", "--live", action="store_true",
                        help="Force connection to a running Chrome debug session (real logged-in browser). Usually not needed — auto-detection is enabled.")
    parser.add_argument("--cdp-url", default="http://localhost:9222",
                        help="Custom CDP URL (default: http://localhost:9222)")
    parser.add_argument("--visible", action="store_true",
                        help="Run with visible browser (only for new instances)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON (ideal for agents)")
    parser.add_argument("--timeout", type=int, default=30000,
                        help="Default timeout for actions in ms")
    parser.add_argument("--new-tab", action="store_true",
                        help="Force creation of a new tab (default behavior in CDP mode is to reuse the current tab to avoid spam)")
    parser.add_argument("--auto-indicator", action="store_true",
                        help="Automatically show the glowing \ud83d\udc3c searching indicator during navigation actions")
    parser.add_argument("--indicator-label", default="\ud83d\udc3c Grok",
                        help="Label to use with --auto-indicator (default: '\ud83d\udc3c Grok')")
    parser.add_argument("--indicator-actions", default="",
                        help="Comma-separated list of actions that should trigger the auto-indicator "
                             "(e.g. 'goto,new_tab,reload'). Defaults to navigation actions.")

    subparsers = parser.add_subparsers(dest="command", help="Action to perform")

    # === Subcommands ===

    # goto
    p = subparsers.add_parser("goto", help="Navigate to a URL")
    p.add_argument("url", help="Target URL")

    # click
    p = subparsers.add_parser("click", help="Click an element")
    p.add_argument("selector", help="CSS selector, text=, role=, etc.")

    # select - dedicated "click to select" for dropdowns, menus, lists (GitHub-style forms etc.)
    p = subparsers.add_parser("select", help="Select an option by clicking it (robust for custom dropdowns/menus)")
    p.add_argument("option", help="Visible text of the option to select (e.g. 'MIT License', 'Python')")
    p.add_argument("--container", "--in", dest="container",
                   help="Optional dropdown/menu trigger (text or selector) to click first to open it")

    # fill
    p = subparsers.add_parser("fill", help="Fill an input/textarea")
    p.add_argument("selector", help="Selector for the field")
    p.add_argument("value", help="Text to fill")

    # type
    p = subparsers.add_parser("type", help="Type text with optional delay")
    p.add_argument("selector")
    p.add_argument("text")
    p.add_argument("--delay", type=int, default=0)

    # screenshot
    p = subparsers.add_parser("screenshot", help="Take a screenshot")
    p.add_argument("path", nargs="?", default="screenshot.png")

    # extract-text
    p = subparsers.add_parser("extract-text", help="Extract text from selector")
    p.add_argument("selector")

    # execute-script (or eval)
    p = subparsers.add_parser("execute-script", aliases=["eval", "js"], help="Execute JavaScript")
    p.add_argument("script", help="JavaScript code to run")

    # wait-for-navigation
    p = subparsers.add_parser("wait-for-navigation", help="Wait for navigation to complete")
    p.add_argument("pattern", nargs="?", default="**/*")

    # tabs / get-tabs
    p = subparsers.add_parser("tabs", aliases=["get-tabs"], help="List all open tabs")

    # switch-tab
    p = subparsers.add_parser("switch-tab", help="Switch to a tab by index")
    p.add_argument("index", type=int)

    # new-tab
    p = subparsers.add_parser("new-tab", help="Open a new tab (optionally navigate)")
    p.add_argument("url", nargs="?")

    # Keyboard shortcuts for browser navigation
    p = subparsers.add_parser("shortcut", help="Send a keyboard shortcut (e.g. 'Control+L', 'Control+T', 'Alt+Left')")
    p.add_argument("keys", help="Key combination to press (e.g. Control+T, Meta+Shift+T, Alt+Left, F5)")

    # Common convenience shortcut commands
    p = subparsers.add_parser("focus-address", aliases=["address-bar"], help="Focus the address bar (Ctrl/Cmd + L)")
    p = subparsers.add_parser("reload-shortcut", aliases=["hard-reload"], help="Reload page (Ctrl+R). Use --hard for Ctrl+Shift+R")
    p.add_argument("--hard", action="store_true", help="Perform hard reload (bypass cache)")
    p = subparsers.add_parser("back", help="Go back in history (Alt+Left)")
    p = subparsers.add_parser("forward", help="Go forward in history (Alt+Right)")

    # More power-user keyboard shortcuts
    p = subparsers.add_parser("devtools", help="Open DevTools (F12 / Ctrl+Shift+I)")
    p = subparsers.add_parser("console", help="Open JavaScript Console (Ctrl+Shift+J)")
    p = subparsers.add_parser("history", help="Open History (Ctrl+H)")
    p = subparsers.add_parser("bookmarks", help="Open Bookmarks Manager (Ctrl+Shift+O)")
    p = subparsers.add_parser("downloads", help="Open Downloads (Ctrl+J)")
    p = subparsers.add_parser("view-source", help="View Page Source (Ctrl+U)")
    p = subparsers.add_parser("fullscreen", help="Toggle Fullscreen (F11)")
    p = subparsers.add_parser("zoom-in", help="Zoom In (Ctrl++)")
    p = subparsers.add_parser("zoom-out", help="Zoom Out (Ctrl+-)")
    p = subparsers.add_parser("zoom-reset", help="Reset Zoom (Ctrl+0)")

    # Discovery command for agents
    p = subparsers.add_parser("list-shortcuts", aliases=["shortcuts", "keyboard-help"],
                              help="List all supported keyboard shortcuts (great for agents)")

    # close-tab
    p = subparsers.add_parser("close-tab", help="Close a tab (current if no index)")
    p.add_argument("index", type=int, nargs="?")

    # title
    p = subparsers.add_parser("title", help="Get current page title")

    # url
    p = subparsers.add_parser("url", help="Get current page URL")

    # links
    p = subparsers.add_parser("links", help="Get all links on the page")

    # reload
    p = subparsers.add_parser("reload", help="Reload current page")

    # scroll-bottom
    p = subparsers.add_parser("scroll-bottom", help="Scroll to bottom of page")

    # launch-browser - helper to start the real logged-in Chrome debug session
    p = subparsers.add_parser("launch-browser", aliases=["start-chrome", "launch-chrome"],
                              help="Launch a Chrome debug session with a persistent profile (best for real logged-in browser control)")

    # status / info
    p = subparsers.add_parser("status", aliases=["info"], help="Show current connection status and whether a real browser is attached")

    # save-auth
    p = subparsers.add_parser("save-auth", help="Save cookies + storage state to a file (backup your logged-in session)")
    p.add_argument("path", nargs="?", default="auth_state.json")

    # cookies
    p = subparsers.add_parser("cookies", help="Show cookies for a domain (debug logged-in state)")
    p.add_argument("domain", nargs="?", default="")

    # Indicator commands for when Grok is actively using the browser
    p = subparsers.add_parser("show-indicator", help="Show glowing \ud83d\udc3c indicator in corner (signals Grok is active)")
    p.add_argument("--label", default="\ud83d\udc3c Grok", help="Custom text next to the panda")

    p = subparsers.add_parser("hide-indicator", help="Remove the glowing panda indicator")

    # Demo command - runs a realistic web navigation example with the configurable searching indicator
    p = subparsers.add_parser("demo", help="Run a realistic web navigation demo with automatic glowing searching panda")
    p.add_argument("--label", default="\ud83d\udc3c Grok", help="Label for the auto indicator")
    p.add_argument("--actions", default="goto,new_tab,wait_for_navigation",
                   help="Comma-separated list of actions that should trigger the searching indicator")

    # Support simple mode: python browser_connector.py https://example.com
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-') and sys.argv[1] not in ['goto','click','select','fill','type','screenshot','extract-text','execute-script','eval','js','wait-for-navigation','tabs','get-tabs','switch-tab','new-tab','close-tab','title','url','links','reload','scroll-bottom','show-indicator','hide-indicator','launch-browser','status','demo','shortcut','focus-address','address-bar','reload-shortcut','hard-reload','back','forward','devtools','console','history','bookmarks','downloads','view-source','fullscreen','zoom-in','zoom-out','zoom-reset','list-shortcuts','shortcuts','keyboard-help']:
        # Looks like a bare URL - inject 'goto' command
        sys.argv.insert(1, 'goto')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    conn = None
    try:
        conn = _get_connector(args)
        use_json = args.json

        result = None

        if args.command == "goto":
            url = args.url
            result = {"url": conn.goto(url)}
            if not use_json:
                print(f"Navigated to: {result['url']}")

        elif args.command == "click":
            conn.click(args.selector)
            result = {"status": "clicked", "selector": args.selector}

        elif args.command == "select":
            conn.select_option(args.option, container=getattr(args, "container", None))
            result = {
                "status": "selected",
                "option": args.option,
                "container": getattr(args, "container", None)
            }
            if not use_json:
                c = f" (in {args.container})" if getattr(args, "container", None) else ""
                print(f"Selected option: {args.option}{c}")

        elif args.command == "fill":
            conn.fill(args.selector, args.value)
            result = {"status": "filled", "selector": args.selector}

        elif args.command == "type":
            conn.type(args.selector, args.text, delay=args.delay)
            result = {"status": "typed", "selector": args.selector}

        elif args.command == "screenshot":
            path = conn.screenshot(args.path)
            result = {"screenshot": path}
            if not use_json:
                print(f"Screenshot saved to: {path}")

        elif args.command == "extract-text":
            text = conn.extract_text_safe(args.selector) or conn.extract_text(args.selector)
            result = {"selector": args.selector, "text": text}

        elif args.command in ("execute-script", "eval", "js"):
            script_result = conn.execute_script(args.script)
            result = {"result": script_result, "script": args.script[:100] + "..." if len(args.script) > 100 else args.script}

        elif args.command == "wait-for-navigation":
            final_url = conn.wait_for_navigation(args.pattern, timeout=args.timeout)
            result = {"url": final_url}

        elif args.command in ("tabs", "get-tabs"):
            tabs = conn.get_tabs()
            result = {"tabs": tabs, "count": len(tabs)}

        elif args.command == "switch-tab":
            url = conn.switch_to_tab(args.index)
            result = {"switched_to": args.index, "url": url}

        elif args.command == "new-tab":
            # Force a new page regardless of reuse settings
            new_page = conn.context.new_page()
            conn.page = new_page
            if args.url:
                url = conn.goto(args.url)
            else:
                url = conn.page.url
            result = {"new_tab_url": url}

        elif args.command == "shortcut":
            conn.keyboard_shortcut(args.keys)
            result = {"shortcut_sent": args.keys}

        elif args.command in ("focus-address", "address-bar"):
            conn.focus_address_bar()
            result = {"action": "focus_address_bar"}

        elif args.command in ("reload-shortcut", "hard-reload"):
            conn.reload_shortcut(hard=args.hard)
            result = {"action": "hard_reload" if args.hard else "reload"}

        elif args.command == "back":
            conn.go_back_shortcut()
            result = {"action": "go_back"}

        elif args.command == "forward":
            conn.go_forward_shortcut()
            result = {"action": "go_forward"}

        elif args.command == "devtools":
            conn.open_devtools_shortcut()
            result = {"action": "open_devtools"}

        elif args.command == "console":
            conn.open_console_shortcut()
            result = {"action": "open_console"}

        elif args.command == "history":
            conn.open_history_shortcut()
            result = {"action": "open_history"}

        elif args.command == "bookmarks":
            conn.open_bookmarks_shortcut()
            result = {"action": "open_bookmarks"}

        elif args.command == "downloads":
            conn.open_downloads_shortcut()
            result = {"action": "open_downloads"}

        elif args.command == "view-source":
            conn.view_page_source_shortcut()
            result = {"action": "view_source"}

        elif args.command == "fullscreen":
            conn.toggle_fullscreen_shortcut()
            result = {"action": "toggle_fullscreen"}

        elif args.command == "zoom-in":
            conn.zoom_in_shortcut()
            result = {"action": "zoom_in"}

        elif args.command == "zoom-out":
            conn.zoom_out_shortcut()
            result = {"action": "zoom_out"}

        elif args.command == "zoom-reset":
            conn.zoom_reset_shortcut()
            result = {"action": "zoom_reset"}

        elif args.command in ("list-shortcuts", "shortcuts", "keyboard-help"):
            shortcuts = conn.list_keyboard_shortcuts()
            result = {"available_shortcuts": shortcuts}

        elif args.command == "close-tab":
            conn.close_tab(args.index)
            result = {"status": "tab_closed", "index": args.index}

        elif args.command == "title":
            result = {"title": conn.get_title()}

        elif args.command == "url":
            result = {"url": conn.get_url()}

        elif args.command == "links":
            links = conn.get_links()
            result = {"links": links, "count": len(links)}

        elif args.command == "reload":
            url = conn.reload()
            result = {"url": url}

        elif args.command == "scroll-bottom":
            conn.scroll_to_bottom()
            result = {"status": "scrolled_to_bottom"}

        elif args.command in ("launch-browser", "start-chrome", "launch-chrome"):
            # This command launches Chrome outside of Python (best effort)
            import subprocess
            import os
            profile_dir = os.path.expanduser("~/.grok-browser-profile")
            os.makedirs(profile_dir, exist_ok=True)

            cmd = [
                "google-chrome-stable",
                f"--remote-debugging-port=9222",
                f"--user-data-dir={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                # Good flags for agent-controlled browser
                "--disable-extensions-except=",
                "--disable-sync",
            ]
            print(f"Launching Chrome debug session with persistent profile at: {profile_dir}")
            print("Command:", " ".join(cmd))
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                result = {
                    "status": "launched",
                    "profile": profile_dir,
                    "remote_debugging": "http://localhost:9222",
                    "note": "Log into your accounts in this Chrome window. Then use --cdp (or no flag) to let agents control it."
                }
            except FileNotFoundError:
                result = {"error": "google-chrome-stable not found in PATH"}
            except Exception as e:
                result = {"error": str(e)}

        elif args.command in ("status", "info"):
            import socket
            cdp_url = getattr(args, 'cdp_url', None) or "http://localhost:9222"
            try:
                port = int(cdp_url.rsplit(":", 1)[-1].split("/")[0])
            except Exception:
                port = 9222

            is_connected = False
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                    is_connected = True
            except Exception:
                pass

            result = {
                "cdp_url": cdp_url,
                "debug_port_listening": is_connected,
                "mode": "CDP (real logged-in browser)" if is_connected else "Headless (new instance)",
                "recommendation": "Use --cdp (or just run commands) when you want the agent to control your already-logged-in browser."
            }

            if is_connected:
                try:
                    tabs = conn.get_tabs()
                    result["open_tabs"] = len(tabs)
                    result["current_url"] = conn.get_url()
                except Exception:
                    pass

        elif args.command == "save-auth":
            path = conn.save_storage_state(args.path)
            result = {"saved_to": path, "note": "This file contains cookies and storage. Keep it secure."}

        elif args.command == "cookies":
            cookies = conn.get_cookies_for_domain(args.domain) if args.domain else conn.get_cookies()[:20]
            result = {"cookies": cookies, "count": len(cookies)}

        elif args.command == "show-indicator":
            conn.show_glowing_panda(args.label)
            result = {"status": "indicator shown", "label": args.label}

        elif args.command == "hide-indicator":
            conn.hide_glowing_panda()
            result = {"status": "indicator hidden"}

        elif args.command == "demo":
            # Self-contained realistic demo (works reliably from CLI)
            actions = [a.strip() for a in args.actions.split(",") if a.strip()]
            print("=== Web Navigation Demo with Searching Panda ===")
            cdp = getattr(args, 'cdp_url', None) or "http://localhost:9222"
            conn = WebBrowserConnector(
                cdp_url=cdp,
                auto_indicator=True,
                indicator_label=args.label,
                indicator_actions=set(actions)
            )
            try:
                print("\n[1] Navigating to Google (searching indicator should appear)...")
                conn.goto("https://www.google.com")
                print(f"     Title: {conn.get_title()}")

                print("\n[2] Searching + waiting for results...")
                conn.fill("textarea[name=q], input[name=q]", "Grok browser control")
                conn.execute_script("document.querySelector('form').submit()")
                conn.wait_for_navigation("**/search**")
                print(f"     Results: {conn.get_title()}")

                print("\n[3] Opening another tab (indicator will show if configured)...")
                conn.new_tab("https://x.ai")
                print(f"     New tab: {conn.get_title()}")

                print("\n\u2705 Demo complete. The searching variant appeared automatically on the configured actions.")
            finally:
                pass  # Never close the user's real browser in CDP mode
            result = {"status": "demo completed"}

        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)

        if result is not None:
            _print_result(result, use_json)

    except Exception as e:
        error_data = {"error": str(e), "type": type(e).__name__}
        if use_json:
            _print_result(error_data, True)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            # In CDP mode we usually don't want to close the whole browser
            if not (getattr(args, 'cdp', False) or getattr(args, 'live', False)):
                try:
                    conn.close()
                except Exception:
                    pass


if __name__ == "__main__":
    main()


# =============================================================================
# Web Navigation Example with Configurable Auto Indicator
# =============================================================================

def web_navigation_example(cdp_url: str = "http://localhost:9222",
                           auto_indicator: bool = True,
                           indicator_label: str = "\ud83d\udc3c Grok",
                           indicator_actions: Optional[Iterable[str]] = None):
    """
    Realistic web navigation example using the connector with the glowing searching indicator.

    This demonstrates:
    - Connecting to a live browser via CDP
    - Configurable automatic "searching" panda during navigation actions
    - Common browser automation patterns (search, navigate, extract)

    Usage:
        from browser_connector import web_navigation_example
        web_navigation_example()

    Or with custom actions:
        web_navigation_example(
            indicator_actions={"goto", "wait_for_navigation"}
        )
    """
    if indicator_actions is None:
        indicator_actions = {"goto", "new_tab", "wait_for_navigation"}

    print("=" * 60)
    print("Web Navigation Example with Auto Searching Indicator")
    print("=" * 60)

    conn = WebBrowserConnector(
        cdp_url=cdp_url,
        auto_indicator=auto_indicator,
        indicator_label=indicator_label,
        indicator_actions=indicator_actions
    )

    try:
        print("\n[1] Navigating to Google (searching panda should appear)...")
        conn.goto("https://www.google.com")
        print(f"     Current page: {conn.get_title()}")

        print("\n[2] Performing a search (indicator active during navigation)...")
        conn.fill("textarea[name=q], input[name=q]", "xAI Grok browser automation")
        conn.execute_script("document.querySelector('form').submit()")
        conn.wait_for_navigation("**/search**")
        print(f"     Search results page: {conn.get_title()}")

        print("\n[3] Extracting some results...")
        links = conn.get_links()[:5]
        print(f"     Found {len(links)} links on page (showing first 5):")
        for link in links:
            print(f"       - {link[:80]}")

        print("\n[4] Opening a new tab (searching indicator will show)...")
        conn.new_tab("https://github.com/xai-org/grok")
        print(f"     New tab title: {conn.get_title()}")

        print("\n\u2705 Example complete!")
        print("   The glowing panda (searching variant) appeared automatically")
        print("   during navigation actions as configured.")

    except Exception as e:
        print(f"\nError during example: {e}")
    finally:
        # In CDP mode we don't want to close the user's browser
        if not cdp_url:
            conn.close()


# Quick demo entrypoint
# python -c "from browser_connector import web_navigation_example; web_navigation_example()"
