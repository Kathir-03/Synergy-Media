import time
import random
from playwright.sync_api import sync_playwright

# ===================================================================================
# --- CONFIGURATION ---
# ===================================================================================

# 1. Chrome user data directory (where you are logged into LinkedIn already)
user_data_dir = r"C:\\Users\\Admin\\AppData\\Local\\Chromium\\User Data"

# 2. List of full image paths for the post
# To post a single image, just put one path in the list: [r"path/to/image.jpg"]
image_filenames = [
    r"E:\\test\\play\\rajni.jpg",
    r"E:\\test\\play\\fallback.jpg",
    r"E:\\test\\play\\coolie.jpg"
]

# 3. Post caption (this will be the overall caption for all photos)
caption = "🚀 Kicking off the week with a project showcase! Here's a look at our latest design concepts. Each image highlights a different feature. #ProjectLaunch #UIUX #Automation"

# ===================================================================================
# --- HELPERS ---
# ===================================================================================

def human_delay(min_s=1.2, max_s=2.5):
    """Wait for a random duration to mimic human pause."""
    time.sleep(random.uniform(min_s, max_s))

def human_hover(page, locator):
    """Move the mouse randomly over a locator before clicking."""
    box = locator.bounding_box()
    if box:
        x = box["x"] + random.randint(5, int(box["width"]) - 5)
        y = box["y"] + random.randint(5, int(box["height"]) - 5)
        page.mouse.move(x, y, steps=random.randint(15, 40))
        human_delay(0.5, 1.2)

# ===================================================================================
# --- SCRIPT LOGIC ---
# ===================================================================================
def linkedin_post():
    def run(playwright):
        print("--- Starting Direct LinkedIn Post Script ---")

        context = playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            channel="chrome",
            slow_mo=120,
            args=["--start-maximized"],
            no_viewport=True
        )

        page = context.new_page()

        try:
            # --- Open LinkedIn ---
            print("Step 1: Navigating to LinkedIn...")
            page.goto("https://www.linkedin.com/feed/", timeout=60000)
            human_delay(3, 5)
            
            ## --- CHANGE --- Removed the human_scroll() section for faster posting.

            # --- Open Post Dialog ---
            print("Step 2: Opening 'Start a post' dialog...")
            start_post_btn = page.get_by_role("button", name="Start a post")
            start_post_btn.wait_for(state="visible", timeout=20000)
            human_hover(page, start_post_btn)
            start_post_btn.click()
            print("   ✅ Post dialog opened.")
            human_delay()

            # --- Add Image(s) ---
            print("Step 3: Uploading image(s)...")
            with page.expect_file_chooser() as fc_info:
                media_btn = page.get_by_label("Add media")
                media_btn.wait_for(state="visible", timeout=20000)
                human_hover(page, media_btn)
                media_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(image_filenames)
            print(f"   ✅ {len(image_filenames)} image(s) selected.")
            
            # --- Confirm Media Selection ---
            print("Step 4: Confirming media selection...")
            page.get_by_role("button", name="Next").click()
            print("   ✅ Media selection confirmed.")
            human_delay()

        
            # --- Step 5: Writing caption with human-like typing ---
            print("Step 5: Writing overall caption...")
            text_area = page.get_by_role("paragraph")
            text_area.wait_for(state="visible", timeout=20000)
            text_area.click() # Ensure the text box is focused before typing

            # Loop through each character in the caption string
            for char in caption:
                # Type one character at a time with a random delay
                page.get_by_role("textbox", name="Text editor for creating").type(char, delay=random.randint(40, 110))

            print("   ✅ Caption typed like a human.")
            human_delay()

            # --- Click Post ---
            print("Step 6: Clicking 'Post' button...")
            page.get_by_role("button", name="Post", exact=True).click()
            print("   ✅ Post submitted.")

            # --- Wait for Confirmation ---
            print("Step 7: Waiting for confirmation...")
            success_msg = page.locator("text='Post successful.'")
            success_msg.wait_for(state="visible", timeout=30000)
            print("\n🎉 --- LinkedIn Photo Gallery Submitted Successfully! --- 🎉")

        except Exception as e:
            print("\n❌ --- SCRIPT FAILED --- ❌")
            print(f"Error: {e}")
            page.screenshot(path="linkedin_error.png")
            print("   📸 Saved a screenshot to linkedin_error.png for debugging.")
            print("Check the last successful step above to find the issue.")

        finally:
            print("--- Closing browser in 20 seconds ---")
            time.sleep(20)
            context.close()


    # Run Script
    with sync_playwright() as playwright:
        run(playwright)