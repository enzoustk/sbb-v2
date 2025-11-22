# 🤖 SBB v2: High-Frequency Betting Bot

> **Context:** Unlike standard educational projects, this bot was architected for **real financial profit**. It runs in production using proprietary data feeds to execute EV+ strategies.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Model](https://img.shields.io/badge/Model-XGBoost%20%7C%20Scikit--Learn-orange)](https://scikit-learn.org/)
[![Bot](https://img.shields.io/badge/Interface-Telegram%20API-2CA5E0)](https://core.telegram.org/bots/api)

### ⚠️ Replication Notice
**This repository is for demonstration/portfolio purposes only.**
The system relies on private APIs and paid data streams containing sensitive keys. You will not be able to run `main.py` locally without these specific credentials.

---

### 🛠️ The Stack
Built 100% in Python, focusing on speed and data integrity.
* **Core ML:** `xgboost`, `scikit-learn` (Retrained dynamically)
* **Data Processing:** `pandas`, `numpy`, `openpyxl`
* **Infrastructure:** `python-telegram-bot`, `requests`, `python-dotenv`

### ⚡ Architecture & Workflow
The bot operates on a continuous data-driven loop:

1.  **Ingestion:** Fetches historical and live match data via API.
2.  **Processing:** Structures raw data into predictive features in real-time.
3.  **Inference:** Runs the latest XGBoost model on live matches.
4.  **Execution:** Identifies **EV+ (Positive Expected Value)** opportunities and pushes alerts to Telegram.
5.  **Warehousing:** Logs every prediction context (bet taken vs. skipped).
6.  **Settlement:** Automatically verifies match results once concluded.
7.  **Reporting:** Updates the database, edits the original Telegram message with the result (Win/Loss), and generates a 24h ROI report.

---



---
*Developed by Enzo Araujo.*
