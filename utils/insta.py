import time
import random
from playwright.sync_api import sync_playwright

# ===================================================================================
# --- CONFIGURATION ---
# ===================================================================================

# 1. Chrome user data directory (where your login is saved)
user_data_dir = r"C:\\Users\\ajayk\\AppData\\Local\\Chromium\\User Data"

# 2. Full image path
image_filename = r"D:\\Gaypr\\final\\instagram_reel.mp4"

# 3. Caption text
caption = "oh my goooood wow!"

# ===================================================================================
# --- HELPERS ---
# ===================================================================================

def human_delay(min_s=1.5, max_s=3.5):
    """Wait a random amount of time like a human would."""
    t = random.uniform(min_s, max_s)
    time.sleep(t)

def human_scroll(page, steps=3):
    """Scroll the feed a bit to mimic human browsing."""
    for _ in range(steps):
        scroll_amount = random.randint(200, 800)
        page.mouse.wheel(0, scroll_amount)
        human_delay(0.8, 2.0)

def human_hover(page, locator):
    """Hover randomly before clicking."""
    box = locator.bounding_box()
    if box:
        x = box["x"] + random.randint(5, int(box["width"]) - 5)
        y = box["y"] + random.randint(5, int(box["height"]) - 5)
        page.mouse.move(x, y, steps=random.randint(15, 40))
        human_delay(0.5, 1.2)

# ===================================================================================
# --- SCRIPT LOGIC ---
# ===================================================================================

# ===================================================================================
# --- SCRIPT LOGIC (CORRECTED) ---
# ===================================================================================
def post(caption, image_filename):
    def run(playwright):
        print("--- Starting Instagram Automation Script ---")

        context = playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            channel="chrome",
            slow_mo=150,
            args=["--start-maximized"],
            no_viewport=True
        )

        page = context.new_page()

        try:
            print("Step 1: Navigating to Instagram...")
            page.goto("https://www.instagram.com", timeout=60000)
            human_delay(3, 5)

            # Mimic browsing feed first
            print("   👀 Scrolling feed before posting...")
            human_scroll(page, steps=random.randint(2, 5))

            # --- Click "Create" button ---
            print("Step 2: Clicking 'Create' button...")
            create_btn = page.locator('svg[aria-label="New post"]').first
            create_btn.wait_for(state="visible", timeout=15000)
            human_hover(page, create_btn)
            create_btn.click()
            print("   ✅ Create button clicked.")
            human_delay(2, 4)  # Wait for the "Create new post" modal to open

            # --- DELETED STEP 3 ---
            # The "Create new post" window now opens directly.
            # There is no longer a separate "Post" option to click.
            # --- Click "Post" in dropdown ---
            print("Step 3: Clicking 'Post' option...")
            # This is a more specific selector that targets the clickable menu item
            # instead of just any text on the page.
            page.get_by_role("link", name="Post Post").click()
            print("   ✅ Post option clicked.")
            human_delay()
            # --- Upload Image ---
            print("Step 4: Uploading image...")
            # The selector for the upload button is robust enough to find the new one.
            with page.expect_file_chooser() as fc_info:
                upload_btn = page.locator(
                    'button:has-text("Select from computer")'
                )
                upload_btn.wait_for(state="visible", timeout=15000)
                upload_btn.first.click()
            file_chooser = fc_info.value
            file_chooser.set_files(image_filename)
            print(f"   ✅ Image selected: {image_filename}")
            human_delay()

            # --- First Next (Crop) ---
            print("Step 5: Clicking first 'Next' button...")
            next_btn = page.get_by_role("button", name="Next")
            next_btn.wait_for(state="visible", timeout=15000)
            human_hover(page, next_btn)
            next_btn.click()
            print("   ✅ First Next clicked.")
            human_delay()

            # --- Second Next (Filter) ---
            print("Step 6: Clicking second 'Next' button...")
            next_btn = page.get_by_role("button", name="Next")
            next_btn.wait_for(state="visible", timeout=15000)
            human_hover(page, next_btn)
            next_btn.click()
            print("   ✅ Second Next clicked.")
            human_delay()

            # --- Caption ---
            print("Step 7: Writing caption...")
            caption_box = page.locator('div[aria-label="Write a caption..."]')
            caption_box.wait_for(state="visible", timeout=15000)
            human_hover(page, caption_box)
            caption_box.click()

            # Type like a human instead of instant fill
            for char in caption:
                caption_box.type(char, delay=random.randint(30, 90))

            print("   ✅ Caption typed like a human.")
            human_delay()

            # --- Share ---
            print("Step 8: Clicking 'Share'...")
            share_btn = page.get_by_role("button", name="Share")
            share_btn.wait_for(state="visible", timeout=15000)
            human_hover(page, share_btn)
            share_btn.click()
            print("   ✅ Post shared.")

            # --- Wait until post confirmation ---
            print("Step 9: Waiting for confirmation...")
            page.locator('text=Your post has been shared').wait_for(timeout=60000)
            print("\n🎉 --- Post submitted successfully! --- 🎉")

        except Exception as e:
            print("\n❌ --- SCRIPT FAILED --- ❌")
            print(f"Error: {e}")
            print("Check which step failed above.")
            # Taking a screenshot on failure can be very helpful for debugging
            page.screenshot(path="debug_screenshot.png")
            print("   📸 Saved a screenshot to debug_screenshot.png")

        finally:
            print("--- Closing browser in 20 seconds ---")
            time.sleep(20)
            context.close()

# Run script
    with sync_playwright() as playwright:
        run(playwright)

