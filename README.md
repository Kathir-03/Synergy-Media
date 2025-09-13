# Synergy-Media

[![Python Version](https://img.shields.io/badge/python-3.8.18-blue.svg)](https://www.python.org/downloads/release/python-3818/)
[![License](https://img.shields.io/github/license/Kathir-03/Synergy-Media)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/Kathir-03/Synergy-Media)](https://github.com/Kathir-03/Synergy-Media/commits/main)
[![Issues](https://img.shields.io/github/issues/Kathir-03/Synergy-Media)](https://github.com/Kathir-03/Synergy-Media/issues)
[![Stars](https://img.shields.io/github/stars/Kathir-03/Synergy-Media?style=social)](https://github.com/Kathir-03/Synergy-Media/stargazers)

**Synergy-Media** is an AI-powered social media automation and analytics platform designed for **influencers** and **businesses**.  
It leverages advanced AI agents to generate, repurpose, and publish content across platforms — while providing actionable insights with a cross-platform analytics dashboard.

---

## 🎯 Who Is It For?

- **Influencers**:  
  - Repurpose long-form videos into platform-specific posts  
  - Auto-generate threads, reels, carousels, and captions  
  - Automate publishing across Twitter, LinkedIn, and Instagram  

- **Businesses**:  
  - Upload product details (image, name, description)  
  - Get AI-driven **post recommendations** for Twitter & Instagram  
  - Automate posting to reach audiences effortlessly  

---

## 🚀 Core Features

### 👩‍🎤 Influencer Tools
- **Content Reconstruction**  
  - Convert YouTube videos into:  
    - Twitter threads  
    - LinkedIn carousel posts (AI-generated visuals)  
    - Instagram reels (auto-highlighted, 30-sec clips)  
- **Post Generation**  
  - AI-crafted captions & hashtags for higher engagement  
- **Automated Posting**  
  - Seamless publishing to connected accounts via automation  

### 🏢 Business Tools
- **Product Recommendation**  
  - Input: product image + description  
  - Output: optimized, ready-to-post content for Instagram & Twitter  
- **Automated Posting**  
  - AI-generated promotional posts auto-published across platforms  

### 📊 Analytics Dashboard
- Unified view of performance across Twitter, LinkedIn, and Instagram  
- **Key Metrics**: followers, engagement (likes/comments), demographics  
- **Cross-Platform Comparison**: discover which platform drives the most value  
- **Trends Insights**: top Instagram trends + recommended posting strategies  

---

## 🛠️ Tech Stack

Language : Python
- **Libraries & APIs**:  
  - Playwright → Twitter automation  
  - Nano Banana API → Image generation  
  - MoviePy → Video editing & reels  
  - Redis → Asynchronous task management  
  - Instagram Graph API → Analytics retrieval  

---

## 📂 Repository Structure

```

Synergy-Media/
├── utils/                 # Helper modules
├── st.py                  # Streamlit frontend entry point
├── pyproject.toml         # Project metadata & dependencies
├── uv.lock                # Lockfile for uv dependencies
├── .python-version        # Python version config
├── .gitignore             # Git ignore rules
└── README.md              # Project documentation

````

Got it 👍 I’ll clean it up and format the section neatly in **Markdown style** so it looks professional and consistent inside your README.

Here’s the polished version:

````markdown
## ⚙️ Installation

2. **Create a virtual environment**  
   ```bash
   uv venv
````

3. **Activate the environment**

   * **Windows (PowerShell)**

     ```bash
     .venv\Scripts\Activate.ps1
     ```

4. **Install dependencies**

   ```bash
   uv sync
   ```

---

## ▶️ Usage

Run the app locally:

```bash
python st.py
```

* **Influencers** → Provide a YouTube link and get:

  * Twitter threads
  * LinkedIn carousels
  * Instagram reels (auto-generated & posted)

* **Businesses** → Upload product details and get:

  * Optimized promotional content for Instagram & Twitter
  * Automated posting to connected accounts

* **Everyone** → Track engagement and insights via the **Analytics Dashboard**

---

## 📊 Requirements

* Python **3.8.18**
* [uv](https://github.com/astral-sh/uv) for dependency & environment management
* API access:

  * Twitter
  * LinkedIn
  * Instagram Graph API
  * Nano Banana API

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "Add my feature"`)
4. Push to your fork (`git push origin feature/my-feature`)
5. Open a Pull Request

```


