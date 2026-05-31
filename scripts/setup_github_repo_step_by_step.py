#!/usr/bin/env python3
"""
Step-by-step GitHub repository creator for huggingface-local-models.

This version is designed to be more resilient. It pauses at key steps
so you can confirm in the browser or handle any CAPTCHAs/logins manually.

Run it, and follow the prompts.
"""

import nest_asyncio
nest_asyncio.apply()

from browser_connector import WebBrowserConnector
import time
import sys

def main():
    print("=" * 70)
    print("GitHub Repository Setup: huggingface-local-models")
    print("=" * 70)
    print("This will guide you through creating the repo using your live browser.")
    print("The glowing panda will be disabled to avoid GitHub CSP issues.")
    print()

    input("Press Enter when your Chrome debug session (port 9222) is running and you are logged into GitHub... ")

    conn = WebBrowserConnector(cdp_url="http://localhost:9222", auto_indicator=False)

    def pause(msg="Press Enter to continue..."):
        input(f"\n{msg} ")

    try:
        # Step 1
        print("\n[Step 1] Going to GitHub new repository page...")
        conn.goto("https://github.com/new")
        time.sleep(2)
        conn.screenshot("/tmp/step1_new_repo_page.png")
        print("  Screenshot: /tmp/step1_new_repo_page.png")
        print(f"  Current title: {conn.get_title()}")
        pause("Confirm you see the 'Create a new repository' page, then press Enter")

        # Step 2 - Repo name
        print("\n[Step 2] Filling repository name...")
        try:
            conn.page.locator("#repository-name-input").first.fill("huggingface-local-models")
            print("  Name filled: huggingface-local-models")
        except Exception as e:
            print(f"  Selector issue: {e}")
            print("  Please manually fill 'huggingface-local-models' in the name field.")
            pause()

        conn.screenshot("/tmp/step2_name_filled.png")
        pause()

        # Step 3 - Description
        print("\n[Step 3] Adding description...")
        desc = "Tools, scripts, and guides for running Hugging Face models locally using llama.cpp, Ollama, and other backends."
        try:
            conn.page.locator('input[name="Description"], #_r_d_').first.fill(desc)
            print("  Description filled.")
        except:
            print("  Please manually add the description if the field is visible.")
        conn.screenshot("/tmp/step3_description.png")
        pause()

        # Step 4 - Options
        print("\n[Step 4] Setting visibility and initialization options...")
        print("  Please manually ensure:")
        print("    - Visibility: Public")
        print("    - [x] Add a README file")
        print("    - .gitignore: Python")
        print("    - License: MIT License")
        conn.screenshot("/tmp/step4_options.png")
        pause("Check the boxes as described above, then press Enter when ready to create")

        # Step 5 - Create
        print("\n[Step 5] Creating the repository...")
        try:
            conn.page.locator('button:has-text("Create repository")').first.click()
            print("  Clicked Create repository button.")
        except Exception as e:
            print(f"  Click failed: {e}")
            print("  Please click the 'Create repository' button manually.")

        print("  Waiting for repo creation (up to 15s)...")
        time.sleep(8)

        current_url = conn.get_url()
        if "huggingface-local-models" in current_url and "/new" not in current_url:
            print(f"\n\u2705 SUCCESS! Repository created at: {current_url}")
            conn.screenshot("/tmp/step5_repo_created.png")
            print("Final screenshot saved.")
        else:
            print(f"\nCurrent URL: {current_url}")
            print("The repo may have been created. Please check the browser.")
            conn.screenshot("/tmp/step5_final_state.png")

        print("\n" + "=" * 70)
        print("Basic repo creation flow complete.")
        print("You can now manually add topics (huggingface, llm, local-llm, etc.)")
        print("or continue with further automation if needed.")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        conn.screenshot("/tmp/error_state.png")
        print("Error state screenshot saved.")
        print("You can continue manually in the browser or provide more details for fixes.")

if __name__ == "__main__":
    main()
