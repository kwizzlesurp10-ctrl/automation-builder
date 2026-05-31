#!/usr/bin/env python3
"""
Drive Chat - Conversational control of Google Drive via your live browser.

Run with:
    python drive_chat.py

Requirements:
- Chrome must be running with remote debugging:
  google-chrome-stable --remote-debugging-port=9222 --user-data-dir=~/.grok-browser-profile

The glowing panda will appear whenever the tool is actively controlling Drive.
"""

from browser_connector import WebBrowserConnector
import time
import re


class DriveChat:
    def __init__(self):
        print("Connecting to your live Chrome session (port 9222)...")
        self.conn = WebBrowserConnector(
            cdp_url="http://localhost:9222",
            auto_indicator=True,
            indicator_label="\ud83d\udc3c Drive",
            indicator_actions={"goto", "click", "fill", "wait_for_navigation"},
        )
        print("Connected. The glowing panda will show during Drive actions.\n")
        self._go_to_drive_home()

    def _go_to_drive_home(self):
        print("Ensuring we're on Google Drive...")
        self.conn.goto("https://drive.google.com/drive/my-drive")
        # Give Drive time to load its main UI
        try:
            self.conn.wait_for_selector('[role="main"]', timeout=15000)
        except Exception:
            pass
        print("Ready on Google Drive.\n")

    def search(self, query: str):
        print(f"Searching Drive for: {query}")
        # Best reliable way: use the search box at the top
        try:
            # Click the search area (Drive has a prominent search bar)
            self.conn.click('input[aria-label*="Search"]')
            time.sleep(0.5)
            self.conn.page.keyboard.type(query)
            self.conn.page.keyboard.press("Enter")
            self.conn.wait_for_navigation("**/drive/search**", timeout=12000)
            print(f"Search results loaded for '{query}'.")
        except Exception as e:
            print(f"Search via UI had an issue ({e}). Falling back to direct URL...")
            self.conn.goto(f"https://drive.google.com/drive/search?q={query}")

    def create_folder(self, name: str):
        print(f"Creating folder: '{name}'")
        try:
            # Click the big "New" button
            self.conn.click('div[aria-label="New"]')
            self.conn.wait_for_selector('div[aria-label="Folder"]', timeout=6000)
            self.conn.click('div[aria-label="Folder"]')

            # Type the name
            self.conn.wait_for_selector(
                'input[aria-label*="Folder name"]', timeout=5000
            )
            self.conn.fill('input[aria-label*="Folder name"]', name)

            # Confirm
            self.conn.click('button:has-text("Create")')
            print(f"✓ Folder '{name}' created.")
        except Exception as e:
            print(f"Could not create folder through the UI: {e}")
            print("Trying keyboard shortcut (Ctrl+Shift+N)...")
            self.conn.keyboard_shortcut("Control+Shift+N")
            time.sleep(1.5)
            self.conn.page.keyboard.type(name)
            self.conn.page.keyboard.press("Enter")

    def list_visible_items(self, limit: int = 12):
        print("Listing items visible in the current Drive view...")
        try:
            # Drive items usually have data-id or are in grid cells
            items = self.conn.page.locator('[data-id], [role="gridcell"]').all()[:limit]
            names = []
            for item in items:
                try:
                    text = item.inner_text().strip()
                    if text:
                        names.append(text.split("\n")[0])
                except Exception:
                    pass

            if names:
                print("\nVisible items:")
                for name in names:
                    print(f"  • {name}")
            else:
                print("No items detected (folder might be empty or still loading).")
        except Exception as e:
            print(f"Could not list items: {e}")

    def chat_loop(self):
        print("\n" + "=" * 70)
        print("Drive Chat is ready!")
        print("Talk to your Google Drive naturally (type 'quit' to exit).")
        print("\nExamples:")
        print("  list my files")
        print("  create folder Projects")
        print("  search for Q3 report")
        print("  go to my drive")
        print("=" * 70 + "\n")

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                self.handle_message(user_input)

            except KeyboardInterrupt:
                print("\nExiting Drive Chat.")
                break
            except Exception as e:
                print(f"Error: {e}")

    def handle_message(self, message: str):
        msg = message.lower()

        if any(
            kw in msg for kw in ["list", "show files", "what do i have", "my files"]
        ):
            self.list_visible_items()

        elif "create folder" in msg or "make folder" in msg or "new folder" in msg:
            match = re.search(r'folder\s+["\']?([^"\']+)["\']?', message, re.IGNORECASE)
            if match:
                self.create_folder(match.group(1).strip())
            else:
                print("Please tell me the folder name, e.g.: create folder Projects")

        elif "search" in msg:
            query = message.split("search", 1)[-1].strip()
            if query:
                self.search(query)
            else:
                print("What should I search for in Drive?")

        elif "go to drive" in msg or "open drive" in msg or "my drive" in msg:
            self._go_to_drive_home()
            print("Back at the root of My Drive.")

        elif "help" in msg:
            print(
                "Try: 'list files', 'create folder X', 'search for Y', or 'go to my drive'."
            )

        else:
            print(
                "I can help with: listing files, creating folders, searching, and going to Drive."
            )
            print(
                "Try something like: 'create folder Experiments' or 'search for invoices'."
            )


if __name__ == "__main__":
    chat = DriveChat()
    chat.chat_loop()
