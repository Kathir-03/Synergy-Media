import os
import ast
import time
import subprocess
import yt_dlp
import whisper
import google.generativeai as gen
import asyncio  # For running agents asynchronously
from typing import List, Dict, Any, Tuple
# Corrected moviepy imports
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, vfx
from PIL import Image
from io import BytesIO
import re
from google import genai
import img2pdf


# --- Configuration ---
# Ensure your GOOGLE_API_KEY is set as an environment variable
gen.configure(api_key=os.environ["GOOGLE_API_KEY"])
# --- 1. The Central State ---
# This dictionary will be passed between agents to share data.
class AgentState:
    def __init__(self, youtube_url: str):
        self.state: Dict[str, Any] = {
            "youtube_url": youtube_url,
            "video_path": None,
            "transcript_segments": [],
            "full_transcript_text": "",
            "twitter_thread": [],
            "linkedin_cards_content": [],
            "linkedin_image_paths": [],
            "instagram_reel_path": None,
            "final_reel_with_captions_path": None,
        }
    
    def update(self, key: str, value: Any):
        print(f"🔄 State update: '{key}' updated.")
        self.state[key] = value

    def get(self, key: str) -> Any:
        return self.state.get(key)

# --- 2. The Specialist Agents & Tools ---

# A. Transcription Agent (The First Step)
def transcription_agent(state: AgentState):
    """Downloads, extracts audio, and transcribes the video."""
    print("\n--- AGENT: Transcription ---")
    video_url = state.get("youtube_url")
    video_filename = "downloaded_video.mp4"
    audio_filename = "temp_audio.mp3"
    
    try:
        # 1. Download Video
        ydl_opts = {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'outtmpl': video_filename, 'noplaylist': True, 'overwrites': True}
        print("📥 Downloading video...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        state.update("video_path", video_filename)
        print("✅ Video downloaded.")

        # 2. Extract Audio
        print("\n🔩 Extracting audio...")
        subprocess.run(['ffmpeg', '-i', video_filename, '-q:a', '0', '-map', 'a', audio_filename, '-y'], check=True, capture_output=True)
        
        # 3. Transcribe
        print("\n✍️ Transcribing audio...")
        model = whisper.load_model("base")
        transcription = model.transcribe(audio_filename, fp16=False)
        os.remove(audio_filename)
        




        segments = transcription['segments']
        transcript = []
        if segments:
            for i in segments:
                arr = [i['start'], i['end'], i['text']]
                transcript.append(arr)

        txt = ''
        for i in transcript:
            txt += i[2]
        state.update('full_transcript_text', txt)
        state.update("transcript_segments", transcript)
        print("✅ Transcription complete.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR in Transcription Agent: {e}")
        raise


# B. Twitter Agent
def twitter_agent(state: AgentState):
    """Generates a Twitter thread from the transcript."""
    print("\n--- AGENT: Twitter ---")
    full_transcript_text = state.get("full_transcript_text")
    
    prompt = f"""
    You are an expert social media manager specializing in creating viral Twitter threads.
        Your task is to distill the most important, engaging, and shareable insights from the
        following video transcript. You don't have to reduce the entire volume of the content you 
        can repurpose them in such a way that they do not miss out anything

        RULES:
        - Make the first thread a compulsive one so that it has the right hook to view immediately
        - Make it all come together a single content while being different threads
        - The thread must start with a powerful, attention-grabbing hook.
        - The thread should consist of 3 to 7 tweets.
        - Each tweet must be under 280 characters.
        - Do not use  emojis and hashtags.
        - IMPORTANT: Format the output as a single block of text.
          Separate each tweet with '---'.

        Here is the transcript:
    Transcript: --- {full_transcript_text}
    """
    
    try:
        model = gen.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        thread = response.text
        thread = thread.replace('\n', '')
        val = thread.split('---')

        state.update("twitter_thread", val)
        print("✅ Twitter thread generated.")
    except Exception as e:
        print(f"❌ ERROR in Twitter Agent: {e}")


# C. LinkedIn Agent (A Multi-Step Agent)
def linkedin_agent(state: AgentState):
    """Generates content and then images for LinkedIn cards."""
    print("\n--- AGENT: LinkedIn ---")
    full_transcript_text = state.get("full_transcript_text")
    prompt = f"""
        You are a LinkedIn content strategist and thought leader. Your task is to
        distill the following video transcript into 1 powerful, professional
        takeaways for a LinkedIn carousel post.

        RULES:
        - Each takeaway must have a short, bold **Title:** and a concise **Body:** paragraph.
        - The tone should be inspiring, professional, and actionable.
        - Do not include hashtags in this part.
        - Should contain 3-5 different content
        - IMPORTANT: it has to be in the format as a list of the list it should contain 2 elements 1st element should be the title and the 2nd should be body like this [[] , [] ,[] ..]

        Here is the transcript:
        ---
        {full_transcript_text}
    """

    model = gen.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)

    print("✅ LinkedIn content generated successfully.")
    a = response.text
    print(a)
    blocks = re.findall(r'\[(.*?)\]', a, re.DOTALL)

    takeaways_list = []
    for block in blocks:
        # Find all content within double quotes "..." inside each block.
        parts = re.findall(r'"(.*?)"', block, re.DOTALL)

        if len(parts) == 2:
        # The first match is the title. Remove asterisks and extra whitespace.
            title = parts[0].replace('**', '').strip()
            # The second match is the body. Strip extra whitespace.
            body = parts[1].strip()

            takeaways_list.append({
                "title": title,
                "body": body
            })
        

        cleaned_list = []
        for item in takeaways_list:
            # Remove "Title: " from the title string and strip any extra whitespace
            cleaned_title = item.get('title', '').replace('Title: ', '').strip()
            
            # Remove "**Body:**" from the body string and strip any extra whitespace
            cleaned_body = item.get('body', '').replace('**Body:**', '').strip()

            cleaned_list.append({
                'title': cleaned_title,
                'body': cleaned_body
            })
    print(takeaways_list)
    print(cleaned_list)
    # Extract list-like output
    

    print("🤖 Generating LinkedIn card content...")
    state.update("linkedin_cards_content", cleaned_list)

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    # Generate images
    image_paths = []
        # Initialize the specific image generation model
    background_style_prompt = "A clean and modern graphic design. The background features soft, wavy, abstract shapes with a bright color palette, with a subtle gradient effect. In the center, there is a frosted glass card with rounded corners, giving a blurred, translucent effect to the background. Make the card very large."
    for i, card in enumerate(cleaned_list[:1]):

        prompt = f"""
        You are a professional graphic designer creating a 1080x1080 pixel image for a LinkedIn carousel post.

        **BACKGROUND STYLE:**
        {background_style_prompt}

        **FOREGROUND ELEMENTS & TEXT:**
        1.  **Frosted Glass Card:** In the center, place a large, semi-transparent frosted glass card with rounded corners. It should be the main focus.
        2.  **Body Text:** On top of this frosted glass card, render the following text in a clear, professional, sans-serif font. Ensure it is perfectly legible and well-formatted and at the center of the frosted glass for more alignment:
            "{card['body']}"
        3.  **Title Text:** Above the frosted glass card, render the following title as a large, bold header. Use an elegant, eye-catching font that complements the design:
            "{card['title']}"

        Generate the complete, single image with all these elements perfectly combined. Do not output code.
        """
        time.sleep(10)
        response = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=[prompt],
    )
        file_name = f'linkedin_image_{i}.png'
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                image = Image.open(BytesIO(part.inline_data.data))
                image.save(file_name)
                image_paths.append(file_name)
        
                print(f"✅ Image saved successfully as '{file_name}'")

    state.update("linkedin_image_paths", image_paths)
    print("✅ LinkedIn images generated.")



    pdf_data = img2pdf.convert(image_paths)
    with open('linkedin_post.pdf', 'wb') as file:
        file.write(pdf_data)



# D. Instagram Agent (A Multi-Step Agent)
def instagram_agent(state: AgentState):
    """Identifies highlights, creates a reel, and adds captions."""
    print("\n--- AGENT: Instagram ---")
    transcript_segments = state.get("transcript_segments")
    video_path = state.get("video_path")

    # Step 1: Get Highlight Timestamps from AI
    print("🤖 Identifying highlight clips for reel...")
    try:
        transcript_for_prompt = "\n".join(
            [f"start: {seg[0]}, end: {seg[1]}, text: {seg[2]}" for seg in transcript_segments]
        )

        # This new prompt focuses on narrative and completeness.
        prompt = f"""
        You are an expert video editor tasked with creating a short, viral reel that tells a complete story.
        Analyze the following transcript and select the key segments that, when combined, create a
        coherent and compelling narrative.

        RULES:
        - The selected segments MUST form a logical story from start to finish.
        - The combined duration should be approximately 30 seconds, but prioritize narrative completeness.
        - Your output MUST be a valid Python list of tuples, where each tuple contains the 'start'
          and 'end' time of a selected segment.
        - Do not include any other text, explanation, or markdown formatting.

        Example Output Format:
        [(15.2, 22.5), (45.1, 58.3), (91.28, 101.28)]

        Here is the timestamped transcript:
        ---
        {transcript_for_prompt}
        """
        model = gen.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        highlight_timestamps = ast.literal_eval(response.text.strip())
        print("✅ Highlight timestamps identified.")

        # Step 2: Create the Reel
        output_filename = "instagram_reel.mp4"
        
        print(f"\n🎬 Assembling reel from {len(highlight_timestamps)} clips...")
        main_clip = VideoFileClip(video_path)
        
        subclips = []
        for start, end in highlight_timestamps:
            subclip = main_clip.subclipped(start, end)
            
            (w, h) = subclip.size
            target_width = h * 9 / 16
            x_center = w / 2
            x1 = x_center - (target_width / 2)
            
            cropped_subclip = subclip.cropped(x1=x1, width=target_width, y1=0, height=h)
            
            # ✅ fadein/fadeout are lowercase
            subclips.append(cropped_subclip)
        
        final_clip = concatenate_videoclips(subclips)
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")
        print(f"✅ Polished reel saved successfully as '{output_filename}'!")


    except Exception as e:
        print(f"❌ ERROR in Instagram Agent: {e}")

# --- 3. The Orchestrator ---
def main(youtube_url: str):
    """The main orchestrator that runs the entire agent workflow."""
    
    # Initialize the state
    agent_state = AgentState(youtube_url)
    
    # --- STAGE 1: Sequential Task ---
    # Transcription must complete before others can start.
    transcription_success = transcription_agent(agent_state)
    
    # --- STAGE 2: Parallel Tasks ---
    # Check the success status, not the content of the transcript
    if transcription_success:
        print("\n--- Running specialist agents in parallel ---")
        # Define the tasks to run 
        twitter_agent(agent_state)
        linkedin_agent(agent_state)
        instagram_agent(agent_state)
        
        # Run all tasks at once and wait for them to complete
        
        print("\n\n--- ✅ ALL AGENTS FINISHED ---")
        print("Final State:")
        import pprint
        pprint.pprint(agent_state.state)
    else:
        print("Transcription failed, cannot proceed with specialist agents.")


# --- 4. How to Run It ---
if __name__ == "__main__":
    TEST_URL = "https://www.youtube.com/watch?v=NHopJHSlVo4"  # A short video is good for testing
    
    # Run the main asynchronous orchestrator
    # For Python 3.7+
    main(TEST_URL)