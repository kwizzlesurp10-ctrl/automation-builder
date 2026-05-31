#!/usr/bin/env python3
"""
Example: Robust "click to select" for dropdowns, menus, and custom lists.

This is one of the most useful patterns when driving real logged-in browsers
(GitHub forms, HF Hub settings, admin panels, etc.).

The `select_option` method (and CLI `select` command) uses multiple
fallback strategies so it works on native <select>, ARIA menus,
button-triggered popovers, and other modern UI patterns.

Usage:
    # Code
    from browser_connector import WebBrowserConnector
    conn = WebBrowserConnector(cdp_url="http://localhost:9222")
    conn.select_option("MIT License", container="Add license")

    # CLI (recommended for quick testing)
    python browser_connector.py select "Python" --container "Add .gitignore"
"""

from browser_connector import WebBrowserConnector


def main():
    print("=== Select Dropdowns Example ===")
    print("This example shows the new robust selection helper.")
    print()

    # Connect to your live browser (recommended)
    conn = WebBrowserConnector(
        cdp_url="http://localhost:9222",
        auto_indicator=True,           # Show the panda while acting
        indicator_label="🐼 Selecting",
    )

    print("Connected to browser.")
    print("Uncomment the lines below to run against a real form (e.g. GitHub /new).")
    print()

    # === Real-world example (GitHub new repository form) ===
    # conn.goto("https://github.com/new")
    #
    # # These were the exact dropdowns that were difficult to automate
    # conn.select_option("MIT License", container="Add license")
    # conn.select_option("Python", container="Add .gitignore")
    # conn.select_option("Public", container="Choose visibility")
    #
    # print("Selections made!")

    print("Example complete. See source for more patterns and CLI usage.")
    print()
    print("CLI equivalent:")
    print("  python browser_connector.py select \"MIT License\" --container \"Add license\"")


if __name__ == "__main__":
    main()
