import time
import random
from playwright.sync_api import sync_playwright

# ===================================================================================
# --- CONFIGURATION ---
# ===================================================================================

# 1. Chrome user data directory (where you are logged into LinkedIn already)
user_data_dir = r"C:\\Users\\ajayk\\AppData\\Local\\Chromium\\User Data" # 👈 UPDATE THIS PATH

# 2. Full path to the PDF file you want to upload
pdf_filename = r"D:\\Gaypr\\final\\linkedin_post.pdf" # 👈 UPDATE THIS PATH

# 3. Title for the document (this appears on the document viewer on LinkedIn)
document_title = "Q3 Project Analysis & Key Findings"

# 4. Post caption (this is the main text that accompanies your document)
caption = "Sharing our key findings from the Q3 project analysis. This document covers performance metrics, challenges, and the roadmap for Q4. Your feedback is welcome! #ProjectManagement #DataAnalysis #QuarterlyReview"

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
        print("--- Starting LinkedIn PDF Post Script ---")

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

            # --- Open Post Dialog ---
            print("Step 2: Opening 'Start a post' dialog...")
            start_post_btn = page.get_by_role("button", name="Start a post")
            start_post_btn.wait_for(state="visible", timeout=20000)
            human_hover(page, start_post_btn)
            start_post_btn.click()
            print("   ✅ Post dialog opened.")
            human_delay()
            page.get_by_role("button", name="More").click()
            # --- Select 'Add a document' option ---
            print("Step 3: Selecting 'Add a document'...")
            
            # NEW: Click the 'More' button first to reveal hidden options
            page.get_by_role("button", name="Add a document").click()
            human_delay(0.5, 1.5) # Wait for menu to appear
            page.get_by_text("Choose file").click()
            
            
            # --- Upload PDF file ---
            print("Step 4: Uploading PDF file...")
            with page.expect_file_chooser() as fc_info:
            # This click triggers the file chooser event that we are expecting.
                page.get_by_role("button", name="Choose file").click(force=True)

            # Now, we get the file_chooser object from the event...
            file_chooser = fc_info.value
            # ...and set the files on it.
            file_chooser.set_files(pdf_filename)

            print("   ✅ PDF file selected.")
            human_delay()
            
            # --- Add Document Title ---
            print("Step 5: Adding document title...")
            title_input = page.get_by_role("textbox", name="Document title")
            title_input.wait_for(state="visible", timeout=20000)
            title_input.fill(document_title)
            human_delay()
            page.get_by_role("button", name="Done").click()
            print("   ✅ Document title set and confirmed.")
            human_delay()

            # --- Write Post Caption ---
            print("Step 6: Writing post caption...")
            text_area=page.get_by_role("paragraph")
            text_area.wait_for(state="visible", timeout=20000)
            text_area.click() # Ensure focus

            # Type caption with a human-like delay
            for char in caption:
                page.get_by_role("textbox", name="Text editor for creating").type(char, delay=random.randint(40, 110))

            print("   ✅ Caption typed.")
            human_delay()

            # --- Click Post ---
            print("Step 7: Clicking 'Post' button...")
            page.get_by_role("button", name="Post", exact=True).click()
            print("   ✅ Post submitted.")

            # --- Wait for Confirmation ---
            print("Step 8: Waiting for confirmation...")
            success_msg = page.locator("text='Post successful.'")
            success_msg.wait_for(state="visible", timeout=30000)
            print("\n🎉 --- LinkedIn Document Submitted Successfully! --- 🎉")

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