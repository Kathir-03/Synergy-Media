import time
import sys
import asyncio
from playwright.sync_api import sync_playwright
import re
# ===================================================================================
# --- CONFIGURATION ---
# ===================================================================================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# Path to your Chrome user data directory (keeps you logged in)
user_data_dir = r"C:\\Users\\ajayk\\AppData\\Local\\Chromium\\User Data"
def clean_text(text):
    # Remove emojis
    text = re.sub(r"[^\w\s.,!?#]", " ", text)
    # Remove hashtags and the word that follows them
    # The pattern r'#\w+\s?\w*' is already a raw string literal,
    # so it does not need to be enclosed in a string like "r'...'"
    text = re.sub(r'#\w+\s?\w*', '', text)
    # Remove extra spaces left after removal
    text = re.sub(r"\s+", " ", text).strip()
    return text
# Thread posts (list of strings)
thread_posts = ["Feeling stuck in a rut? 🤯 What if I told you 30 days is ALL you need to transform your life, add a new habit, or finally try that thing you've always dreamed of? This simple challenge changed everything for me. #30DayChallenge #LifeHack #NewHabits", 
                'It\'s not just about forming habits! 🚀 My 30-day experiments made time more memorable & genuinely boosted my "self-joy burner." You won\'t believe how much you remember when you actively engage with each day. ✨ #Productivity #Mindfulness', "Think you can't write a novel? I did it in 30 days! 🤯 (It was awful, but I'm a novelist now!) If you want something badly enough, you *can* do anything for 30 days. It's about changing your identity, not just the outcome. #GoalSetting #AchieveAnything", "BUT here's the *real* secret: Small, sustainable changes STICK. Big, crazy challenges are fun, but often temporary (like my sugar-free month ending in a sugar crash!). Focus on what you can *keep* doing. 🌱 #HabitFormation #Sustainability", "The next 30 days are going to pass anyway. So, what are YOU waiting for? 🤔 What's that one thing you've always wanted to try? Give it a shot for 30 days. Your future self will thank you. 👇 #TakeAction #StartToday #PersonalGrowth"]

# ===================================================================================
# --- SCRIPT LOGIC (Final Version) ---
# ===================================================================================
def tweet(posts: list[str]):
    thread_posts=posts
    print(thread_posts)
    def run(playwright):
        print("--- Starting X (Twitter) Thread Automation Script ---")

        context = playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            channel="chrome",
            args=["--start-maximized"],
            no_viewport=True
        )
        
        page = context.new_page()

        try:
            print("Step 1: Navigating to X.com/home...")
            page.goto("https://x.com/home", timeout=60000)

            # First post
            print("Step 2: Typing the first post...")
            first_editor = page.locator('div[data-testid="tweetTextarea_0"]')
            first_editor.wait_for(state="visible", timeout=30000)
            first_editor.click()
            # CHANGE: Use .type() to simulate human typing instead of .fill()
            first_editor.type(thread_posts[0], delay=50) # delay of 50ms between each character
            print(f"   ✅ Typed: \"{thread_posts[0][:40]}...\"")

            # Remaining posts
                    # Remaining posts
                    # Remaining posts
            for i, post_text in enumerate(thread_posts[1:], start=1):
                print(f"Step {i+2}: Adding post {i+1} to the thread...")

                # Click Add post button
                add_post_button = page.locator('[aria-label="Add post"]')
                add_post_button.click(force=True)

                # Get all editable textboxes
                editors = page.locator('div[role="textbox"][data-testid^="tweetTextarea_"]')

                # Wait for new editor to appear
                editors.nth(i).wait_for(state="visible", timeout=10000)

                # Select the new editor
                new_editor = editors.nth(i)
                new_editor.click()
                new_editor.type(post_text, delay=50)

                print(f"   ✅ Typed: \"{post_text[:40]}...\"")



            # Click Post button
            print("Step Final: Posting the thread...")
            post_all_button = page.get_by_role("button", name="Post all")
            # By using .type(), the button should now be enabled naturally, no sleep needed.
            post_all_button.click()

            print("\n🎉 --- Thread submitted successfully! --- 🎉")

        except Exception as e:
            print("\n❌ --- SCRIPT FAILED --- ❌")
            print(f"An error occurred: {e}")
            print("Use Inspect in browser to verify 'aria-label' or 'data-testid' values.")

        finally:
            print("--- Script finished. Closing browser in 10 seconds. ---")
            time.sleep(10)
            context.close()

    # Run script
    with sync_playwright() as playwright:
        run(playwright)
cleaned_posts = [clean_text(post) for post in thread_posts]
