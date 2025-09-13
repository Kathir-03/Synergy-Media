# ReConstruct — Pro UI Edition
# ------------------------------------------------------
# Key upgrades:
# - Theme system (Dark/Light) + Preferences in Profile
# - Glassmorphism + card components + iconography
# - Sidebar with avatar, role badge, and active nav highlighting
# - Stepper-style progress for content generation
# - Download all generated outputs as .txt or .csv
# - Enhanced Dashboard with filters and polished charts
# - Tabbed Profile (General | Security | Preferences)
# - Better error surfaces for Instagram API calls
# - Cleaner routing + utilities
# ------------------------------------------------------
from celery.result import AsyncResult
import streamlit as st
import time
import os
import re
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.streamlit_integration import transcription_agent, twitter_agent,linkedin_agent, instagram_agent, AgentState
from utils.multi_x import tweet,clean_text
from utils.insta import post
from utils.link_new import linkedin_post
from utils.poster_generator import generate_poster   
# Optional: Lottie animations (auto-disable if not installed)
try:
    from streamlit_lottie import st_lottie
    HAS_LOTTIE = True
except Exception:
    HAS_LOTTIE = False

# -------------------------
# App Config
# -------------------------
st.set_page_config(
    page_title="ReConstruct",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------
# Dummy DB (session-based)
# -------------------------
if "user_db" not in st.session_state:
    st.session_state.user_db = {
        "user": {
            "password": "password",
            "email": "user@example.com",
            "full_name": "Demo User",
            "role_details": None,
            "avatar_bytes": None,
        }
    }

# -------------------------
# State Init
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "landing"
    st.session_state.logged_in = False
    st.session_state.user_data = {}
    st.session_state.outputs = []
    st.session_state.editing_idx = None
    st.session_state.role = None
    st.session_state.selected_platform = "instagram"
    st.session_state.theme = "dark"  # "dark" or "light"
    st.session_state.compact_mode = False

# -------------------------
# Instagram (placeholders)
# -------------------------
# In production, move to st.secrets and never hardcode credentials.
ACCESS_TOKEN = "EAAjcn6puMnUBPfAz8vWvkOEwmpgndBRzf0kC5wKoBXVN4CR9n5IiaxgM30xCNMan5ZCmiZB0jnTngSsZAtsO54IfmsgQpBxRmE9JhaBvLE0UHVuSC6flqBPObBo7iwi2lAScfbKdmmIb9tv9pxBwIGZBGSG2gxBCLF5gDHLNIA4IspGcd4npZBFDiZBW5k"
IG_USER_ID = "REPLACE_WITH_YOUR_IG_USER_ID"

# -------------------------
# Helpers
# -------------------------
def is_valid_youtube_url(url: str):
    regex = r"^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$"
    return re.match(regex, url)

def get_youtube_title(link: str):
    if "v=dQw4w9WgXcQ" in link:
        return "Rick Astley - Never Gonna Give You Up (Official Music Video)"
    return "A Great Video Title from URL"

def process_youtube_link(link: str):
    title = get_youtube_title(link)
    return [
        f"**Tweet Thread (3/3):**\n\n1️⃣ Key insight from \"{title}\" is the importance of A. It challenges traditional views by highlighting B.\n\n#summary #insight",
        f"**LinkedIn Post:**\n\nJust watched \"{title}\" and was struck by the presenter's take on innovation. The core message: '...' is a powerful reminder for all professionals. Key takeaways include X, Y, and Z. Highly recommend for anyone in our field. What are your thoughts?\n\n#professionaldevelopment #learning",
        f"**Blog Post Idea:**\n\n**Title:** 5 Actionable Lessons from \"{title}\"\n\n**Intro:** The video \"{title}\" provides a masterclass in [Topic]. This post breaks down the five most critical lessons you can apply to your own work today, starting with the principle of..."
    ]

def redo_function(output: str):
    return f"✨ Regenerated variation -> {output.split('->')[-1].strip()}"

def post_to_platform(output: str):
    platform = "Twitter"
    if "LinkedIn" in output:
        platform = "LinkedIn"
    elif "Blog" in output:
        platform = "your blog"
    return f"✅ Successfully scheduled for posting to {platform}!"

def dummy_save_function(content: str):
    return content

def go_to(page_name: str):
    st.session_state.page = page_name
    st.rerun()
ACCESS_TOKEN = "EAAjcn6puMnUBPfAz8vWvkOEwmpgndBRzf0kC5wKoBXVN4CR9n5IiaxgM30xCNMan5ZCmiZB0jnTngSsZAtsO54IfmsgQpBxRmE9JhaBvLE0UHVuSC6flqBPObBo7iwi2lAScfbKdmmIb9tv9pxBwIGZBGSG2gxBCLF5gDHLNIA4IspGcd4npZBFDiZBW5ks"
IG_USER_ID = "17841476668085378"


# ✅ Get account info (followers, following, posts)
def get_account_info():
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}"
    params = {
        "fields": "followers_count,follows_count,media_count",
        "access_token": ACCESS_TOKEN
    }
    return requests.get(url, params=params).json()

def get_profile():
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}"
    params = {
        "fields": "username,profile_picture_url",
        "access_token": ACCESS_TOKEN
    }
    response = requests.get(url, params=params).json()
    return response

# ✅ Get insights (reach, engagement, etc.)
def get_account_insights():
    url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/insights"

    # 1️⃣ Time-series metrics
    time_series_params = {
        "metric": "reach",
        "period": "day",
        "access_token": ACCESS_TOKEN
    }

    # 2️⃣ Total-value metrics (daily counters)
    total_value_params = {
        "metric": "profile_views,website_clicks,accounts_engaged,total_interactions",
        "metric_type": "total_value",
        "period": "day",
        "access_token": ACCESS_TOKEN
    }

    # 3️⃣ Demographics (if available)
    demographics_params = {
        "metric": "engaged_audience_demographics,follower_demographics",
        "period": "lifetime",
        "metric_type": "total_value",
        "timeframe": "this_week",
        "breakdown": "age,city,country,gender",
        "access_token": ACCESS_TOKEN
    }

    ts_data = requests.get(url, params=time_series_params).json()
    tv_data = requests.get(url, params=total_value_params).json()
    demo_data = requests.get(url, params=demographics_params).json()

    return {"time_series": ts_data, "total_value": tv_data, "demographics": demo_data}


# -------------------------
# Theming & CSS
# -------------------------
def theme_vars():
    if st.session_state.theme == "dark":
        return {
            "--bg": "#0f1115",
            "--panel": "rgba(255,255,255,0.04)",
            "--panel-strong": "rgba(255,255,255,0.08)",
            "--text": "#EAEAEA",
            "--muted": "#a2a7b1",
            "--primary": "#7c5cff",
            "--accent": "#00d1b2",
            "--danger": "#ff5c7a",
            "--warning": "#ffb020",
            "--shadow": "0 10px 30px rgba(0,0,0,0.35)",
            "--border": "rgba(255,255,255,0.08)",
        }
    else:
        return {
            "--bg": "#f6f7fb",
            "--panel": "rgba(255,255,255,0.85)",
            "--panel-strong": "rgba(255,255,255,0.95)",
            "--text": "#1f2430",
            "--muted": "#596070",
            "--primary": "#5b53ff",
            "--accent": "#06b6d4",
            "--danger": "#e11d48",
            "--warning": "#f59e0b",
            "--shadow": "0 10px 30px rgba(31,36,48,0.12)",
            "--border": "rgba(31,36,48,0.08)",
        }

def render_app_css():
    v = theme_vars()
    compact = "6px" if st.session_state.compact_mode else "12px"
    st.markdown(f"""
    <style>
        :root {{
            --bg: {v['--bg']};
            --panel: {v['--panel']};
            --panel-strong: {v['--panel-strong']};
            --text: {v['--text']};
            --muted: {v['--muted']};
            --primary: {v['--primary']};
            --accent: {v['--accent']};
            --danger: {v['--danger']};
            --warning: {v['--warning']};
            --shadow: {v['--shadow']};
            --border: {v['--border']};
        }}
        .stApp {{
            background: var(--bg);
            color: var(--text);
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--panel-strong), var(--panel));
            border-right: 1px solid var(--border);
            backdrop-filter: blur(10px);
        }}
        .glass {{
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: var(--shadow);
            padding: 18px;
        }}
        .card {{
            background: var(--panel-strong);
            border: 1px solid var(--border);
            border-radius: 16px;
            box-shadow: var(--shadow);
            padding: {compact};
        }}
        .hero {{
            padding: 48px 24px;
            border-radius: 18px;
            background: radial-gradient(1000px 400px at 10% 0%, rgba(124,92,255,0.25), transparent),
                        radial-gradient(1200px 500px at 90% 20%, rgba(6,182,212,0.25), transparent),
                        var(--panel-strong);
            border: 1px solid var(--border);
            text-align: center;
            box-shadow: var(--shadow);
        }}
        .kpi {{
            display:flex; align-items:center; gap:12px;
            padding: 14px; border-radius: 14px; border:1px solid var(--border);
            background: var(--panel);
        }}
        .kpi .icon {{
            font-size: 20px; opacity: 0.9;
        }}
        .kpi .label {{
            font-size: 13px; color: var(--muted);
        }}
        .kpi .value {{
            font-size: 22px; font-weight: 700; color: var(--text);
        }}
        .nav-btn > button {{
            width: 100%;
            text-align: left !important;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 12px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text);
        }}
        .nav-btn > button:hover {{
            background: var(--panel);
        }}
        .nav-active > button {{
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(124,92,255,0.25);
        }}
        .role-badge {{
            display:inline-flex; align-items:center; gap:8px;
            padding: 6px 10px; border-radius: 999px; border: 1px solid var(--border);
            background: var(--panel);
            font-size: 12px; color: var(--muted);
        }}
        .pill {{
            padding: 6px 10px; border-radius: 999px;
            background: var(--panel); border: 1px solid var(--border); color: var(--muted);
            font-size: 12px;
        }}
        .danger-btn > button {{
            border-color: var(--danger) !important; color: var(--danger) !important;
        }}
        .primary > button {{
            background: var(--primary) !important; color: white !important; border: none !important;
        }}
        .accent > button {{
            background: var(--accent) !important; color: white !important; border: none !important;
        }}
        .warning > button {{
            background: var(--warning) !important; color: black !important; border: none !important;
        }}
        .small-muted {{ color: var(--muted); font-size: 12px; }}
        .codebox pre {{
            background: var(--panel) !important; border: 1px solid var(--border) !important;
            border-radius: 12px !important;
        }}
        .center {{ display:flex; align-items:center; justify-content:center; }}
        #MainMenu, footer {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

def metric_card(icon: str, label: str, value: str, delta: str = None):
    with st.container():
        st.markdown(f"""
        <div class="kpi">
            <div class="icon">{icon}</div>
            <div>
                <div class="label">{label}</div>
                <div class="value">{value}</div>
                <div class="small-muted">{'' if not delta else delta}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def sidebar_nav():
    with st.sidebar:
        user = st.session_state.user_data if st.session_state.logged_in else {}
        avatar_bytes = None
        if st.session_state.logged_in:
            db_user = st.session_state.user_db[user['username']]
            avatar_bytes = db_user.get("avatar_bytes")
        st.markdown("### ReConstruct ✨")
        # Profile header
        if st.container().button("Profile", use_container_width=True):
            go_to("profile")
        if st.container().button("Reconstruct", use_container_width=True):
            go_to("content_reconstruction")
        if st.container().button("Trending", use_container_width=True):
            go_to("trend")
        if st.container().button("Content generator", use_container_width=True):
            go_to("details_collection")
        if st.container().button("Dashboard", use_container_width=True):
            go_to("dashboard")
        # Quick theme toggle
        theme_col1, theme_col2 = st.columns(2)
        with theme_col1:
            if st.button("🌙 Dark", type="secondary", use_container_width=True):
                st.session_state.theme = "dark"
                st.rerun()
        with theme_col2:
            if st.button("☀️ Light", type="secondary", use_container_width=True):
                st.session_state.theme = "light"
                st.rerun()

        st.checkbox("Compact mode", key="compact_mode")
        if st.session_state.compact_mode:
            st.caption("Reduced paddings enabled.")

        st.write("---")
        if st.session_state.logged_in:
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_data = {}
                st.toast("You have been logged out.")
                go_to("landing")
        else:
            if st.button("Login", use_container_width=True):
                go_to("auth")

# -------------------------
# Pages
# -------------------------
def page_landing():
    st.markdown(
        """
        <div class="hero">
            <h1 style="margin:0; font-weight:800; font-size:44px;">ReConstruct your social presence</h1>
            <p style="opacity:0.9; margin:10px auto 0; max-width:700px;">
                Transform long-form content into a cascade of engaging, on-brand posts — automatically.
            </p>
            <div style="display:flex; gap:10px; justify-content:center; margin-top:18px;">
                <span class="pill">⚡ AI-powered rewriting</span>
                <span class="pill">🎯 Platform-optimized</span>
                <span class="pill">📈 Insights-ready</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.container().button("Get started", use_container_width=True):
            go_to("details_collection")
    with c2:
        if st.container().button("👀 Learn More", use_container_width=True):
            st.info("ReConstruct helps creators and businesses repurpose content effortlessly.")

    st.write("")
    with st.container():
        st.markdown("#### Why ReConstruct?")
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown(
                """
                <div class="card">
                    <h4>🧠 Smart Repurposing</h4>
                    <p class="small-muted">Turn videos and blogs into threads, posts, and carousels with minimal effort.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with colB:
            st.markdown(
                """
                <div class="card">
                    <h4>🎨 On-brand Output</h4>
                    <p class="small-muted">Consistent tone, hashtags, and CTAs across platforms.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with colC:
            st.markdown(
                """
                <div class="card">
                    <h4>📊 Performance Ready</h4>
                    <p class="small-muted">Insights-friendly structure and UTM-ready captions.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )




def page_onboarding_role():
    sidebar_nav()
    st.title("🚀 Onboarding: Choose Your Role")
    st.caption("We’ll tailor your experience.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='card'><h4>🏢 I'm a Business</h4><p class='small-muted'>Maximize your content ROI.</p></div>", unsafe_allow_html=True)
        if st.button("Select Business", use_container_width=True):
            st.session_state.role = "business"
            go_to("details_collection")
    with col2:
        st.markdown("<div class='card'><h4>🎤 I'm an Influencer</h4><p class='small-muted'>Grow reach across platforms.</p></div>", unsafe_allow_html=True)
        if st.button("Select Influencer", use_container_width=True):
            st.session_state.role = "influencer"
            go_to("details_collection")

def page_onboarding_details():
    sidebar_nav()
    role = st.session_state.get("role")
    if not role:
        st.warning("Please select a role first.")
        if st.button("Go back to Role Selection"):
            go_to("select_role")
        return
    st.title("📝 Onboarding: Tell Us More")
    with st.container():
        with st.form("details_form"):
            details = {}
            if role == "business":
                st.subheader("Business Details")
                product_name = st.text_input("Product Name")
                st.file_uploader("Product Image (Optional)", type=["png", "jpg", "jpeg"])
                product_description = st.text_area("Product Description")
                submitted = st.form_submit_button("Complete Setup", use_container_width=True)
                if submitted:
                    details = {"product_name": product_name, "product_description": product_description}
            else:
                st.subheader("Content Details")
                content_name = st.text_input("Content Name (e.g., your channel/blog name)")
                content_type = st.selectbox("Primary Content Type", ["YouTube", "Podcast", "Blog", "Twitch Stream", "Other"])
                content_description = st.text_area("Briefly describe your content")
                submitted = st.form_submit_button("Complete Setup", use_container_width=True)
                if submitted:
                    details = {"content_name": content_name, "content_type": content_type, "content_description": content_description}
            if submitted and details:
                username = st.session_state.user_data["username"]
                st.session_state.user_db[username]["role_details"] = details
                st.toast("Setup complete! Welcome to ReConstruct.", icon="🎉")
                go_to("home")

def page_home():
    sidebar_nav()
    st.markdown(
        f"""
        <div class="hero">
            <h2 style="margin:0;">Welcome back, {st.session_state.user_data.get('full_name', 'User')}!</h2>
            <p class="small-muted" style="margin-top:8px;">Here’s a snapshot of your performance.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    kc1, kc2, kc3 = st.columns(3)
    with kc1: metric_card("🧩", "Total Reconstructions", "42", "10 in the last 7 days")
    with kc2: metric_card("📅", "Posts Scheduled", "35", "8 in the last 7 days")
    with kc3: metric_card("⭐", "Avg. Post Quality", "8.9/10", "↑ steady")

    st.write("")
    st.subheader("Recent Activity")
    with st.container():
        st.success("✅ A new Tweet thread was posted successfully yesterday.")
        st.info("📈 Your last reconstruction ‘Top 5 AI Tools’ got 1.2K views on LinkedIn.")

def generation_stepper(total=4, delay=0.4):
    steps = ["Parsing", "Analyzing", "Reconstructing", "Finalizing"]
    prog = st.progress(0, text="Starting…")
    for i, s in enumerate(steps, start=1):
        prog.progress(i / total, text=f"{s}…")
        time.sleep(delay)
    prog.empty()

def page_content_reconstruction():
    sidebar_nav()

    st.title("🎥 Content Reconstruction")
    st.write("Enter a YouTube link below to generate new content from your long-form video.")
    
    link = st.text_input("YouTube Video Link:", key="youtube_link_input", placeholder="https://www.youtube.com/watch?v=...")

    if st.button("Generate Content", key="process_btn", use_container_width=True):
        if link:
            with st.spinner("Processing video... This may take a while depending on video length."):
                try:
                    # Initialize your agent state
                    state = AgentState(link)
                    transcription_success = transcription_agent(state)
                    
                    if transcription_success:
                        # Run other agents
                        twitter_agent(state)
                        linkedin_agent(state)
                        instagram_agent(state)

                        # Structure the outputs for session state
                        outputs = [
                            {"type": "twitter", "content": "\n\n".join(state.get("twitter_thread"))},
                            {"type": "linkedin", "content": "linkedin_post.pdf"},
                            {"type": "instagram", "content": "instagram_reel.mp4"}
                        ]

                        st.session_state.outputs = outputs
                        st.session_state.editing_idx = None # Reset editing index
                        st.success("Content generated successfully! ✅")
                        st.balloons()
                    else:
                        st.error("Transcription failed, cannot proceed.")
                except Exception as e:
                    st.error(f"Error during processing: {e}")

    # --- Display Generated Outputs ---
    if "outputs" in st.session_state and st.session_state.outputs:
        st.markdown("---")
        st.subheader("Generated Outputs")
        
        for idx, output in enumerate(st.session_state.outputs, start=1):
            with st.expander(f"Output {idx} — {output['type'].capitalize()}", expanded=(idx == 1)):
                
                is_editable = (output["type"] == "twitter") # Only Twitter thread is text-editable

                # --- Edit Mode UI ---
                if st.session_state.get("editing_idx") == idx:
                    st.info("✏️ Edit mode")
                    new_text = st.text_area("Modify Content", value=output["content"], height=200, key=f"edit_area_{idx}")
                    c1, c2, _ = st.columns([1, 1, 4])
                    with c1:
                        if st.button("💾 Save", key=f"save_{idx}", use_container_width=True):
                            st.session_state.outputs[idx - 1]["content"] = new_text
                            st.session_state.editing_idx = None
                            st.toast("Changes saved!", icon="✅")
                            st.rerun()
                    with c2:
                        if st.button("✖️ Cancel", key=f"cancel_{idx}", use_container_width=True):
                            st.session_state.editing_idx = None
                            st.rerun()

                # --- Display Mode UI ---
                else:
                    if output["type"] == "twitter":
                        st.markdown("### 🧵 Twitter Thread")
                        st.text_area("Thread Preview", value=output["content"], height=200, disabled=True)
                        threads=output["content"].split("\n\n")
                        print(threads)
                    elif output["type"] == "linkedin":
                        st.markdown("### 💼 LinkedIn Carousel PDF")
                        pdf_path = output["content"]
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            st.download_button("⬇️ Download LinkedIn PDF", data=pdf_bytes, file_name="linkedin_post.pdf", mime="application/pdf")
                            # st.pdf(pdf_bytes) # Uncomment if you have a component that can render PDFs

                    elif output["type"] == "instagram":
                        st.markdown("### 📹 Instagram Reel")
                        video_path = output["content"]

                        if os.path.exists(video_path):
                            with open(video_path, "rb") as f:
                                video_bytes = f.read()
                            st.video(video_bytes)
                            st.download_button("⬇️ Download Reel", data=video_bytes, file_name="instagram_reel.mp4", mime="video/mp4")

                    st.markdown("---") # Visual separator

                    # --- Action Buttons (Regenerate, Edit, Post) ---
                    show_edit_button = (idx == 1 and is_editable)

                    if show_edit_button:
                        # Layout for the first output with "Edit" button
                        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
                        with c1:
                            if st.button("✨ Regenerate", key=f"redo_{idx}", use_container_width=True):
                                with st.spinner("Regenreating Tweet thread..."):
                                    state = AgentState(link)
                                    transcription_success = transcription_agent(state)
                                    if transcription_success:
                                        twitter_agent(state)
                                st.rerun()
                        with c2:
                            if st.button("✏️ Edit", key=f"edit_{idx}", use_container_width=True):
                                st.session_state.editing_idx = idx
                                st.rerun()
                        with c3:
                            if st.button("🚀 Post", key=f"post_{idx}", use_container_width=True):
                                tweet(threads)
                    else:
                        # Layout for other outputs without "Edit" button
                        c1, c2, _ = st.columns([1, 1, 4])
                        with c1:
                            if st.button("✨ Regenerate", key=f"redo_{idx}", use_container_width=True):
                                if idx==2:
                                    with st.spinner("Regenreating LinkedIn post..."):
                                        state = AgentState(link)
                                        transcription_success = transcription_agent(state)
                                        if transcription_success:
                                            linkedin_agent(state)
                                else:
                                    with st.spinner("Regenreating Instagram reel..."):
                                        state = AgentState(link)
                                        transcription_success = transcription_agent(state)
                                        if transcription_success:
                                            instagram_agent(state)
                                st.rerun()
                        with c2:
                            if st.button("🚀 Post", key=f"post_{idx}", use_container_width=True):
                                if idx==2:
                                    linkedin_post()
                                else:
                                    post("test post nanba",r"D:\\Gaypr\\final\\instagram_reel.mp4")                                
def page_dashboard():
    sidebar_nav()
    st.title("📊 Social Media Dashboards")
    st.caption("Analyze and track your content performance across platforms.")

    # Platform selector
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("📱 Instagram", use_container_width=True):
            st.session_state.selected_platform = "instagram"
            st.rerun()
    with col2:
        if st.button("🐦 Twitter", use_container_width=True):
            st.session_state.selected_platform = "twitter"
            st.rerun()
    with col3:
        st.markdown(f'<span class="pill">Selected: {st.session_state.selected_platform.title()}</span>', unsafe_allow_html=True)

    # Date filter (demo)
    st.write("")
    fd1, fd2, fd3 = st.columns([1.2, 1.2, 6])
    with fd1:
        window = st.selectbox("Window", ["7 days", "14 days", "30 days"], index=1)
    with fd2:
        agg = st.selectbox("Aggregate", ["Daily", "Cumulative"], index=0)

    # Main chart (sample)
    st.subheader("📈 Cross-Platform Engagement Trends")
    with st.container():
        days = pd.to_datetime(pd.date_range(end=pd.Timestamp.now(), periods=14))
        ig_engagement = [120, 135, 150, 140, 165, 180, 200, 190, 210, 230, 220, 240, 255, 270]
        tw_engagement = [80, 85, 90, 100, 95, 110, 115, 125, 130, 140, 135, 150, 160, 155]
        if agg == "Cumulative":
            ig_engagement = pd.Series(ig_engagement).cumsum().tolist()
            tw_engagement = pd.Series(tw_engagement).cumsum().tolist()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=ig_engagement, mode='lines+markers', name='Instagram'))
        fig.add_trace(go.Scatter(x=days, y=tw_engagement, mode='lines+markers', name='Twitter'))
        fig.update_layout(
            title=f"Engagement ({window})",
            plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)',
            font_color=theme_vars()["--text"],
            legend=dict(bgcolor='rgba(0,0,0,0.05)'),
            xaxis=dict(gridcolor='rgba(128,128,128,0.15)'),
            yaxis=dict(gridcolor='rgba(128,128,128,0.15)')
        )
        st.plotly_chart(fig, use_container_width=True, theme=None)

    st.markdown("---")
    if st.session_state.selected_platform == "instagram":
        st.subheader("📸 Instagram Deep Dive")

        # --- 1. Fetch Data from API ---
        profile_info = get_profile()
        account_info = get_account_info()
        insights_data = get_account_insights()

        # --- 2. Check for API Errors ---
        if any("error" in d for d in [profile_info, account_info, insights_data]):
            st.error("Could not fetch Instagram data. Check your Access Token and User ID.")
            with st.expander("Troubleshooting tips", expanded=False):
                st.write("- Ensure your token has the required scopes: `instagram_basic`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`.")
                st.write("- Verify the IG_USER_ID is for your Instagram Business or Creator account.")
                st.write("- Check if your token has expired and that your Facebook App is in Live mode.")
        else:
            # --- 3. Display Profile Header & KPIs (if no errors) ---
            profile_pic_url = profile_info.get("profile_picture_url", None)
            username = profile_info.get("username", "N/A")

            hdr1, hdr2 = st.columns([1, 5])
            with hdr1:
                if profile_pic_url:
                    st.image(profile_pic_url, width=80)
                else:
                    # Placeholder if no profile picture is available
                    st.markdown('<div class="center" style="width:80px;height:80px;border-radius:50%;border:1px solid #444;background:#222;font-size:36px;text-align:center;line-height:80px;">📷</div>', unsafe_allow_html=True)
            with hdr2:
                st.markdown(f"### @{username}")
                st.caption("Business account overview and daily insights")

            k1, k2, k3 = st.columns(3)
            k1.metric("Followers", f'{account_info.get("followers_count", 0):,}')
            k2.metric("Following", f'{account_info.get("follows_count", 0):,}')
            k3.metric("Posts", f'{account_info.get("media_count", 0):,}')
            
            st.divider()

            # --- START: NEW INTEGRATED INSIGHTS PROCESSING ---

            # -------------------------------------------------
            # 4. Time-series metrics (e.g., Reach)
            # -------------------------------------------------
            ts_data = insights_data["time_series"].get("data", [])
            time_series = []
            for metric in ts_data:
                for v in metric.get("values", []):
                    time_series.append({
                        "metric": metric["name"],
                        "date": v["end_time"][:10],
                        "value": v["value"]
                    })

            if time_series:
                df_ts = pd.DataFrame(time_series)
                st.subheader("📈 Reach Over Time")
                fig = px.line(df_ts, x="date", y="value", color="metric", markers=True)
                # Apply custom styling for a modern look
                fig.update_layout(
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor='rgba(128, 128, 128, 0.2)')
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No time-series data (like Reach) available.")

            # -------------------------------------------------
            # 5. Total-value metrics (e.g., Profile Views)
            # -------------------------------------------------
            tv_data = insights_data["total_value"].get("data", [])
            totals = []
            for metric in tv_data:
                # Use 'name' instead of 'title' as it's more reliable
                metric_name = metric.get("name", "Unknown").replace("_", " ").title()
                totals.append({
                    "metric": metric_name,
                    "value": metric.get("total_value", {}).get("value", 0)
                })

            if totals:
                df_tv = pd.DataFrame(totals)
                st.subheader("📌 Daily Engagement Metrics")
                
                # Display metrics in columns for a clean KPI layout
                cols = st.columns(len(df_tv))
                for i, row in df_tv.iterrows():
                    with cols[i]:
                        st.metric(label=row["metric"], value=f'{row["value"]:,}')
                
                # Also display as a bar chart for visual comparison
                fig_tv = px.bar(df_tv, x="metric", y="value", text="value", color="metric",
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_tv.update_traces(textposition="outside")
                fig_tv.update_layout(
                    showlegend=False,
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)',
                    yaxis=dict(showgrid=False)
                )
                st.plotly_chart(fig_tv, use_container_width=True)
            else:
                st.info("No total-value metrics (like Profile Views or Clicks) available.")

            # -------------------------------------------------
            # 6. Demographics (e.g., Followers by Country)
            # -------------------------------------------------
            demo_data = insights_data["demographics"].get("data", [])
            if demo_data:
                st.subheader("👥 Audience Demographics")
                st.info("Demographics data is available. Displaying raw JSON as a placeholder. You can build charts from this data.")
                # Placeholder: Display the raw JSON data in an expander
                with st.expander("View Raw Demographics JSON"):
                    st.json(demo_data)
            else:
                st.info("No demographics data available for this account.")
                
            # --- END: NEW INTEGRATED INSIGHTS PROCESSING ---

    # Fallback for other platforms
    elif st.session_state.selected_platform == "twitter":
        st.subheader("🐦 Twitter Deep Dive")
        st.info("Twitter analytics integration is coming soon!")
        st.image(
            "https://images.unsplash.com/photo-1611605698335-8b1569810432?q=80&w=1974&auto=format&fit=crop",
            caption="Analytics for Twitter are under construction.",
        )

def page_profile():
    sidebar_nav()
    st.title("👤 Profile")
    st.caption("Manage your account and preferences.")

    tabs = st.tabs(["General", "Security", "Preferences"])

    # --- General ---
    with tabs[0]:
        st.subheader("Your Information")
        if st.session_state.logged_in and st.session_state.user_data:
            user = st.session_state.user_data
            db_user = st.session_state.user_db[user['username']]
            avatar_bytes = db_user.get("avatar_bytes")

            colA, colB = st.columns([1, 2])
            with colA:
                if avatar_bytes:
                    st.image(avatar_bytes, caption=None, width=120)
                else:
                    st.markdown(
                        '<div class="center" style="width:120px;height:120px;border-radius:16px;border:1px solid var(--border);background:var(--panel);font-size:54px;">🧑‍💻</div>',
                        unsafe_allow_html=True
                    )
                up = st.file_uploader("Upload avatar", type=["png", "jpg", "jpeg"], key="up_avatar")
                if up is not None:
                    db_user["avatar_bytes"] = up.read()
                    st.toast("Avatar updated!", icon="🖼️")
                    st.rerun()
            with colB:
                with st.form("profile_form"):
                    st.text_input("Username", value=user.get('username', 'N/A'), disabled=True)
                    full_name = st.text_input("Full Name", value=db_user.get('full_name', ''))
                    email = st.text_input("Email", value=db_user.get('email', ''))
                    submitted = st.form_submit_button("Update Profile", use_container_width=True)
                    if submitted:
                        st.session_state.user_db[user['username']]['full_name'] = full_name
                        st.session_state.user_db[user['username']]['email'] = email
                        st.session_state.user_data['full_name'] = full_name
                        st.session_state.user_data['email'] = email
                        st.toast("Profile updated successfully!", icon="✅")
        else:
            st.warning("You are not logged in.")

    # --- Security ---
    with tabs[1]:
        st.subheader("Security")
        st.caption("Update your password.")
        if st.session_state.logged_in and st.session_state.user_data:
            user = st.session_state.user_data
            with st.form("security_form"):
                old_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                new_pw2 = st.text_input("Confirm New Password", type="password")
                if st.form_submit_button("Change Password", use_container_width=True):
                    if old_pw != st.session_state.user_db[user["username"]]["password"]:
                        st.error("Current password is incorrect.")
                    elif not new_pw or len(new_pw) < 6:
                        st.error("New password must be at least 6 characters.")
                    elif new_pw != new_pw2:
                        st.error("New password and confirm password do not match.")
                    else:
                        st.session_state.user_db[user["username"]]["password"] = new_pw
                        st.success("Password changed successfully.")
        else:
            st.info("Log in to manage security.")

    # --- Preferences ---
    with tabs[2]:
        st.subheader("Preferences")
        st.caption("Personalize the look & feel.")
        col1, col2 = st.columns(2)
        with col1:
            theme = st.radio("Theme", ["dark", "light"], index=0 if st.session_state.theme == "dark" else 1, horizontal=True)
            if theme != st.session_state.theme:
                st.session_state.theme = theme
                st.rerun()
        with col2:
            st.checkbox("Compact mode", key="compact_mode_pref")
            if st.session_state.compact_mode != st.session_state.compact_mode_pref:
                st.session_state.compact_mode = st.session_state.compact_mode_pref
                st.rerun()
        st.info("Preferences are saved instantly.")
import streamlit as st
from PIL import Image
import os
import google.generativeai as gen

from utils.poster_generator import generate_poster   # 👈 Import external function

def product_content_generator_app():
    sidebar_nav()
    from PIL import Image
    import os

    # ----------------- Sample product data -----------------
    product_name = "Sample Product"
    product_description = "This is a sample description."
    product_image_path = "sample_product.jpg"

    # ----------------- Helper functions -----------------
    def generate_twitter_content(name, description):
        
        """Generates a Twitter thread from the transcript."""
        print("\n--- AGENT: Twitter ---")
        
        prompt = f"""
        You are an expert social media manager specializing in creating viral Twitter threads.
            YOu have to greate a engaging twitter thread that according to the product name{name} and description {description} should
            provide with the best hook to pull audience to increase engagement. It should not give any false advertisment.
            Create the best engaging post for all range of audience


            RULES:
            - Make the first thread a compulsive one so that it has the right hook to view immediately
            - Make it all come together a single content while being different threads
            - The thread must start with a powerful, attention-grabbing hook.
            - The thread should consist of 3 to 7 tweets.
            - Each tweet must be under 280 characters.
            - Do not use  emojis and hashtags.
            - IMPORTANT: Format the output as a single block of text.
            Separate each tweet with '---'.


        """
        
        try:
            model = gen.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            thread = response.text
            thread = thread.replace('\n', '')
            val = thread.split('---')
            return val

            print("✅ Twitter thread generated.")
        except Exception as e:
            print(f"❌ ERROR in Twitter Agent: {e}")

    def generate_instagram_content(name, description, image_path):
        return {"caption": f"Check out {name}! {description}", "image": image_path}

    def save_uploaded_image(uploaded_file, save_path="uploaded_image.jpg"):
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return save_path

    # ----------------- Page layout -----------------
    st.title("Product Content Generator")

    # --- Product Name ---
    name = st.text_input("Product Name", value=product_name)
    if not name.strip():
        st.text_input("Enter Product Name")

    # --- Product Description ---
    description = st.text_area("Product Description", value=product_description)
    if not description.strip():
        st.text_area("Enter Product Description")

    # --- Product Image ---
    st.subheader("Product Image")
    image_file = None
    image_path = None
    if os.path.exists(product_image_path):
        try:
            image_file = Image.open(product_image_path)
            st.image(image_file, caption="Current Product Image", use_column_width=True)
            image_path = product_image_path
        except Exception:
            st.warning("Failed to load the product image.")

    uploaded_image = st.file_uploader("Upload new product image", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        image_path = save_uploaded_image(uploaded_image)
        image_file = Image.open(image_path)

    # --- Generate Content Button ---
    if st.button("Generate Content"):
        with st.spinner("Generating content...."):
            if not name or not description:
                st.error("Please provide product name and description.")
            elif not image_path or not os.path.exists(image_path):
                st.error("Please provide a valid product image.")
            else:
                twitter_content = generate_twitter_content(name, description)
                instagram_content = generate_instagram_content(name, description, image_path)
                txt = ''
                for i in twitter_content:
                    txt+=i
                # --- Twitter Container ---
                st.subheader("Twitter Content")
                st.text_area("Twitter Thread", value=txt, height=200, key="twitter_thread")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Regenerate Twitter", key="regen_twitter"):
                        with st.spinner("Generating content...."):
                            generate_twitter_content(name, description)
                            st.success("Twitter content regenerated!")
                        st.rerun()
                with col2:
                    if st.button("Edit Twitter", key="edit_twitter"):
                        st.info("Edit Twitter content manually.")
                with col3:
                    if st.button("Post to Twitter", key="post_twitter"):
                        tweet(twitter_content)
                        st.success("Posted to Twitter!")

                # --- Instagram Container ---
                st.subheader("Instagram Content")
                # st.image(instagram_content["image"], caption="Instagram Image", use_column_width=True)
                caption = st.text_area("Instagram Caption", value=instagram_content["caption"], key="insta_caption")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Regenerate Instagram", key="regen_insta"):
                        with st.spinner("Generating content...."):
                            generate_instagram_content(name, description)
                            st.success("Twitter content regenerated!")
                        st.rerun()
                with col2:
                    if st.button("Post to Instagram", key="post_insta"):
                        post(instagram_content["caption"],r"D:\\Gaypr\\final\\poster.png")
                        st.success("Posted to Instagram!")

                # --- Poster (Gemini) Container ---
                st.subheader("AI Generated Poster")
                poster_text, poster_image = generate_poster(name, description, image_path)
                if poster_text:
                    st.text_area("Poster Text", value=poster_text, height=50, key="poster_text")
                if poster_image:
                    st.image(poster_image, caption="Generated Poster", use_column_width=True)

                # --- Redo Poster ---
                if st.button("Regenerate Poster", key="regen_poster"):
                    poster_text, poster_image = generate_poster(name, description, image_path)
                    if poster_text:
                        st.text_area("Poster Text", value=poster_text, height=200, key="poster_text_redo")
                    if poster_image:
                        st.image(poster_image, caption="Regenerated Poster", use_column_width=True)

import streamlit as st
import requests
import pandas as pd

def trend():
    """Fetch Instagram media data, compute engagement, and display top posts + recommendations in Streamlit."""
    sidebar_nav()
    # --- Helper functions ---
    def get_account_insights():
        url = f"https://graph.facebook.com/v22.0/{IG_USER_ID}/insights"
        params = {
            "metric": "reach,impressions,profile_views,follower_count",
            "period": "day",
            "access_token": ACCESS_TOKEN
        }
        return requests.get(url, params=params).json()

    def get_media_insights(media_id, media_type):
        if media_type not in ["IMAGE", "VIDEO"]:
            return {}
        url = f"https://graph.facebook.com/v22.0/{media_id}/insights"
        params = {"metric": "reach,saved,likes,comments,shares", "access_token": ACCESS_TOKEN}
        res = requests.get(url, params=params).json()
        data = {}
        for i in res.get("data", []):
            if "values" in i:
                data[i["name"]] = i["values"][0].get("value", 0)
            elif "value" in i:
                data[i["name"]] = i.get("value", 0)
        return data

    def collect_media_data():
        url = f"https://graph.facebook.com/v22.0/{IG_USER_ID}/media"
        params = {"fields": "id,caption,timestamp,media_type,permalink", "access_token": ACCESS_TOKEN}
        res = requests.get(url, params=params).json()
        media_data = []
        for media in res.get("data", []):
            media_id = media["id"]
            insights = get_media_insights(media_id, media["media_type"])
            media_data.append({
                "media_id": media_id,
                "caption": media.get("caption", ""),
                "timestamp": media["timestamp"],
                "media_type": media["media_type"],
                "permalink": media["permalink"],
                **insights
            })
        return media_data

    def generate_recommendations(df):
        best_hour = df.groupby("hour")["engagement"].mean().idxmax()
        hour_score = df.groupby("hour")["engagement"].mean().max()
        best_day = df.groupby("day_of_week")["engagement"].mean().idxmax()
        day_score = df.groupby("day_of_week")["engagement"].mean().max()
        best_type = df.groupby("media_type")["engagement"].mean().idxmax()
        type_score = df.groupby("media_type")["engagement"].mean().max()
        return f"""
        ### 📊 Social Media Posting Recommendations

        1. ⏰ **Best Time to Post:** Around **{best_hour}:00**  
        → Posts at this hour get the **highest average engagement ({hour_score:.1f})**.

        2. 📅 **Best Day to Post:** Day {best_day} (0=Mon, 6=Sun)  
        → This day has an average engagement of **{day_score:.1f}**.

        3. 📸 **Best Content Type:** {best_type}  
        → Performs best with engagement of **{type_score:.1f}**.

        ---
        """
    # --- Streamlit UI ---
    st.set_page_config(page_title="Instagram Analysis", layout="wide")
    st.title("📈 Instagram Insights & Recommendations")

    with st.spinner("Fetching media data..."):
        media_data = collect_media_data()
        df = pd.DataFrame(media_data)

    if df.empty:
        st.warning("No media data found for this account.")
        return

    # Preprocess
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["caption_length"] = df["caption"].fillna("").apply(len)
    df["engagement"] = df[["likes", "comments", "shares", "saved"]].sum(axis=1)

    # Top 3 posts
    st.subheader("🔥 Top 3 Performing Posts")
    top_posts = df.sort_values(by="engagement", ascending=False).head(3)
    cols = st.columns(3)
    for i, post in enumerate(top_posts.to_dict(orient="records")):
        with cols[i]:
            st.markdown(f"**{i+1}. {post['caption'] or '(No Caption)'}**")
            st.write(f"🗓️ {post['timestamp'].date()} | 📌 {post['media_type']}")
            st.write(f"**Reach:** {post.get('reach', 0)} | **Engagement:** {post['engagement']}")
            st.markdown(f"[🔗 View on Instagram]({post['permalink']})")
            st.components.v1.iframe(post["permalink"] + "embed", height=500, scrolling=False)

    # Recommendations
    st.subheader("🤖 Recommendations")
    st.markdown(generate_recommendations(df))

# -------------------------
# Main Router
# -------------------------
def main():
    render_app_css()

    if st.session_state.logged_in:
        if st.session_state.page in ["landing", "auth", "signup"]:
            go_to("home")
            return
        pages = {
            "home": page_home,
            "select_role": page_onboarding_role,
            "details_collection": product_content_generator_app,
            "content_reconstruction": page_content_reconstruction,
            "dashboard": page_dashboard,
            "profile": page_profile,
        }
        pages.get(st.session_state.page, page_home)()
    else:
        public_pages = {
            "landing": page_landing,
            "home": page_home,
            "select_role": page_onboarding_role,
            "details_collection": product_content_generator_app,
            "content_reconstruction": page_content_reconstruction,
            "dashboard": page_dashboard,
            "profile": page_profile,
            "trend": trend,
        }
        public_pages.get(st.session_state.page, page_landing)()

if __name__ == "__main__":  
    main()
