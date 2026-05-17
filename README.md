# YouTube Automation — End-to-End Content Production System

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Domain](https://img.shields.io/badge/domain-Affiliate%20Marketing-ccff00.svg)

> **Autonomous content production at scale.** A complete pipeline that turns raw footage into branded, monetized YouTube videos with zero manual intervention.

---

## Project Preview

<div align="center">
  <img src="./preview.png" width="60%" style="border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.5);">
  <p><i>Generated split-screen format: Amazon product showcase (top) + viral content (bottom)</i></p>
</div>

---

## About the Project

This system automates the **entire YouTube content lifecycle** — from sourcing raw material to publishing final episodes with affiliate monetization. After a one-time daily material upload, the system handles everything: editing, branding, scheduling, and uploading.

The pipeline is built around a **branded episodic format** combining viral content with curated product showcases, optimized for both engagement and affiliate conversion.

### Key Features

* **Episodic Content System (v2):** Smart episode numbering, season management, and automatic best-moment detection
* **Professional Video Editing:** Automated color grading (saturation & coloristics), split-screen composition, and dynamic captions
* **Branded Visual Identity:** Custom overlays with product pricing, BebasNeue typography, and SFX integration
* **Amazon Affiliate Integration:** Live product price scraping with dynamic affiliate link generation per video
* **YouTube Upload via Selenium:** Bypasses API quota limits using authenticated browser automation with persistent cookies
* **Content Database:** SQLite-backed system tracking published content, queued videos, and product inventory
* **Worker Queue:** Async processing pipeline for handling multiple uploads per day

---

## Tech Stack

### Core
* **Language:** Python 3.12+
* **Video Processing:** MoviePy / FFmpeg
* **Browser Automation:** Selenium WebDriver

### Data & Integrations
* **Database:** SQLite (`database.py`)
* **YouTube Upload:** Selenium-based automation with cookie persistence
* **Amazon Scraping:** Custom product price extraction
* **Affiliate Tracking:** Dynamic affiliate link injection

### Assets
* **Typography:** BebasNeue-Regular (branded captions)
* **SFX Library:** Custom sound effects pool

---

## Project Architecture

---

## How It Works

1. **Daily Material Upload** — Place raw clips in the input directory (single morning task)
2. **Smart Episode Detection** — System identifies best moments and assigns episode numbers
3. **Automated Editing** — Color grading, saturation correction, and audio sync
4. **Split-Screen Generation** — Composes Amazon product (top) + viral content (bottom)
5. **Branded Overlays** — Adds price tags, captions, and SFX from the asset library
6. **Affiliate Link Injection** — Scrapes current Amazon prices, generates affiliate links
7. **Scheduled Upload** — Selenium publishes to YouTube with auto-generated metadata

The result: **a fully autonomous content engine** that produces multiple monetized videos per day, currently running across 5 product categories.

---

## Getting Started

### Prerequisites
* Python 3.12+
* Google Chrome (for Selenium)
* YouTube account with authenticated cookies
* Amazon Associates account (for affiliate IDs)

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/dazmanian/youtube_automation.git
   cd youtube_automation
```

2. **Install Dependencies**
```bash
   pip install -r requirements.txt
```

3. **Configuration**
   * Add YouTube authentication cookies to `cookies.txt`
   * Configure product database in `database.py`
   * Set up Amazon affiliate tag in environment variables

4. **Run the System**
```bash
   python main.py
```

---

## Roadmap

- [x] Episodic content system (v1 & v2)
- [x] Professional video editing pipeline
- [x] Split-screen composition with brand overlays
- [x] Amazon affiliate integration
- [x] Selenium-based upload bypass
- [x] SQLite content database
- [ ] AI-generated titles and descriptions (GPT integration)
- [ ] Multi-platform expansion (TikTok automation — currently manual)
- [ ] Performance analytics dashboard

---

## What I Learned

Building this system taught me how to architect **real-world automation pipelines** that operate without supervision:

- **Browser automation at scale**: Using Selenium to bypass API limitations while maintaining persistent authentication
- **Video processing fundamentals**: Color grading, audio synchronization, and dynamic compositing with code
- **Production-grade pipelines**: Designing async worker queues with error recovery and state persistence
- **Affiliate economics**: Understanding the technical infrastructure behind affiliate marketing automation
- **Episodic content design**: Building systems that maintain narrative consistency across automated outputs

---

## License

Distributed under the MIT License.

---