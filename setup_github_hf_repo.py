#!/usr/bin/env python3
"""
Automated GitHub repository setup for huggingface-local-models (temporary bootstrap name)
using the live browser connector (CDP).

NOTE: "huggingface-local-models" was the original temporary name used while bootstrapping
this repository. The project was later renamed to "automation-builder".

This script will:
1. Navigate to GitHub new repo page
2. Fill in repository details for the target repository
3. Create the repository
4. Add topics and improve the repo page

Run with the Chrome debug session active.
"""

import nest_asyncio
nest_asyncio.apply()

from browser_connector import WebBrowserConnector
import time
import os

def bootstrap_repository():  # Originally setup_huggingface_local_models_repo()
    print("=" * 60)
    print("Starting GitHub repo setup (historical bootstrap script)")
    print("=" * 60)

    conn = WebBrowserConnector(
        cdp_url="http://localhost:9222",
        auto_indicator=False  # GitHub has strict CSP that breaks the panda injector
    )

    screenshots_dir = "/tmp/github_repo_setup"
    os.makedirs(screenshots_dir, exist_ok=True)

    def snap(name):
        path = f"{screenshots_dir}/{name}.png"
        conn.screenshot(path)
        print(f"  [screenshot] {path}")

    try:
        # Step 1: Go to new repo page
        print("\n[1/6] Navigating to GitHub new repository page...")
        conn.goto("https://github.com/new")
        time.sleep(3)
        snap("01_new_repo_page")
        print(f"  Current page: {conn.get_title()}")

        # Step 2: Fill repository name
        print("\n[2/6] Filling repository name...")
        try:
            # Current GitHub selector (verified via live inspection)
            name_input = conn.page.locator("#repository-name-input").first
            name_input.fill("automation-builder")
            print("  Repository name set to target (originally used temp name during creation)")
        except Exception as e:
            print(f"  Error filling name: {e}")
            print("  Trying fallback selector...")
            try:
                conn.page.locator('input[aria-describedby*="repository-name"]').first.fill("automation-builder")
            except:
                pass

        snap("02_name_filled")

        # Step 3: Add description
        print("\n[3/6] Adding description...")
        description = "Tools, scripts, and guides for running Hugging Face models locally using llama.cpp, Ollama, and other inference backends."
        try:
            # Current GitHub description field (from live inspection)
            desc_input = conn.page.locator('input[name="Description"], #_r_d_').first
            desc_input.fill(description)
            print("  Description added.")
        except Exception as e:
            print(f"  Could not fill description (non-critical): {e}")

        snap("03_description_filled")

        # Step 4: Set visibility to Public and initialize repo
        print("\n[4/6] Setting options (Public + Initialize with README + .gitignore + License)...")

        # Make sure Public is selected (usually default)
        try:
            public_radio = conn.page.locator('input[name="repository[visibility]"][value="public"]').first
            if public_radio.count() > 0:
                public_radio.click()
                print("  Set to Public.")
        except:
            pass

        # Initialize with README
        try:
            readme_checkbox = conn.page.locator('input[name="repository[auto_init]"]').first
            if readme_checkbox.count() > 0 and not readme_checkbox.is_checked():
                readme_checkbox.check()
                print("  Checked 'Add a README file'.")
        except:
            pass

        # Add .gitignore for Python
        try:
            gitignore_dropdown = conn.page.locator('summary[title=".gitignore template"]').first
            if gitignore_dropdown.count() > 0:
                gitignore_dropdown.click()
                time.sleep(0.5)
                python_option = conn.page.locator('div[role="menuitem"] >> text=Python').first
                python_option.click()
                print("  Added Python .gitignore.")
        except Exception as e:
            print(f"  Could not set .gitignore (non-critical): {e}")

        # Choose MIT license
        try:
            license_dropdown = conn.page.locator('summary[title="License"]').first
            if license_dropdown.count() > 0:
                license_dropdown.click()
                time.sleep(0.5)
                mit_option = conn.page.locator('div[role="menuitem"] >> text=MIT License').first
                mit_option.click()
                print("  Selected MIT License.")
        except Exception as e:
            print(f"  Could not set license (non-critical): {e}")

        snap("04_options_set")

        # Step 5: Create the repository
        print("\n[5/6] Creating the repository...")
        try:
            create_btn = conn.page.locator('button:has-text("Create repository")').first
            create_btn.click()
            print("  Clicked 'Create repository' button.")
        except Exception as e:
            print(f"  Error clicking create button: {e}")
            # Fallback
            conn.page.keyboard.press("Enter")

        # Wait for repo creation (can take a few seconds)
        print("  Waiting for repository to be created...")
        time.sleep(6)

        current_url = conn.get_url()
        if "/automation-builder" in current_url:
            print(f"  SUCCESS! Repo created at: {current_url}")
            snap("05_repo_created_success")
        else:
            print(f"  Current URL after creation attempt: {current_url}")
            snap("05_repo_creation_result")

        # Step 6: Post-creation improvements (add topics, etc.)
        print("\n[6/6] Adding repository topics and improving the page...")
        try:
            # Go to the repo page if not already there
            if "/automation-builder" not in current_url:
                conn.goto("https://github.com/YOUR_USERNAME/automation-builder")  # Will need username

            # Click "Manage topics" or similar (GitHub UI varies)
            time.sleep(2)
            topics_button = conn.page.locator('a:has-text("Manage topics"), button:has-text("Add topics")').first
            if topics_button.count() > 0:
                topics_button.click()
                time.sleep(1)
                # Add common topics
                topics_input = conn.page.locator('input[placeholder*="Add a topic"]').first
                for topic in ["huggingface", "llm", "local-llm", "llama.cpp", "ollama", "machine-learning", "browser-automation", "llm-agent"]:
                    topics_input.fill(topic)
                    topics_input.press("Enter")
                    time.sleep(0.3)
                print("  Topics added.")
            snap("06_topics_added")
        except Exception as e:
            print(f"  Post-creation steps had issues (common with dynamic GitHub UI): {e}")

        print("\n" + "=" * 60)
        print("GitHub repository setup process completed!")
        print(f"Final URL: {conn.get_url()}")
        print(f"Check screenshots in: {screenshots_dir}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        conn.screenshot("/tmp/github_error_state.png")
        print("Error screenshot saved to /tmp/github_error_state.png")
        print("You may need to continue manually or provide more specific instructions.")
        raise

if __name__ == "__main__":
    bootstrap_repository()  # Originally setup_huggingface_local_models_repo()
