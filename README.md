# LogTriage

**High-throughput asynchronous log parsing engine and real-time streaming telemetry triage deck.**

## Overview

Modern microservice architectures generate an overwhelming volume of log data. When a shared dependency or infrastructure component fails, operations teams are often blinded by a sudden, massive spike of localized application exceptions, making immediate root-cause analysis incredibly slow and manual. 

`LogTriage` solves this by decoupling raw data ingestion from intelligent incident analysis. It acts as a highly optimized infrastructure sump, absorbing up to ~250,000 log events per second via multi-threaded memory queues, aggressively filtering out operational noise, and isolating concurrent errors across your system mesh. 

**Core Highlights:**
* **High-Velocity Data Plane:** Multi-threaded ingestion engine handling massive throughput via strictly managed `queue.Queue` structures to prevent thread blocking and data drops.
* **Non-Blocking Telemetry Desk:** A dedicated `asyncio` event loop streams live metrics and rolling data-wave timelines over native WebSockets to a decoupled HTML5/JS frontend.
* **Automated Failure Triage:** A sliding 5-second anomaly aggregation window automatically clusters microservice errors and dispatches context-rich root-cause analytics via the Gemini LLM engine.

---

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites & Dependencies](#prerequisites--dependencies)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Architecture Breakdown](#architecture-breakdown)

---

## Architecture Breakdown

The project is strictly modularized into functional domains:

```text
LogTriage/
├── pipeline/                   # Core Python Backend Package
│   ├── metrics.py              # Thread-safe telemetry counters
│   ├── workers.py              # High-speed log ingestion and consumption threads
│   ├── reporter.py             # Async WebSocket broadcaster
│   ├── analyzer.py             # 5s aggregation window and Gemini LLM interface
│   └── engine.py               # Lifecycle orchestrator
├── web/                        # Decoupled Frontend
│   ├── css/styles.css          # Dashboard styling and dynamic pulse alarms
│   ├── js/app.js               # WebSocket lifecycle and Chart.js rendering
│   └── dashboard.html          # UI framework
└── main.py                     # Application entrypoint
```

## Prerequisites & Dependencies

Before standing up the engine, ensure your local environment meets the following requirements:

* **OS:** Linux, macOS, or Windows
* **Runtime:** Python 3.8 or higher
* **API Credentials:** A valid Google Gemini API key exported to your environment variables
* **Frontend:** A modern web browser (Chrome, Edge, Firefox, or Safari) to render the HTML5 Canvas charts

**Required Python Packages:**
* `websockets` (for asynchronous telemetry broadcasting)
* `google-genai` (for autonomous incident summarization)
* `requests` (for optional webhook alerting)

---

## Installation

Run the following commands in your terminal to clone the repository, set up an isolated virtual environment, and install the required dependencies.

```bash
# 1. Clone the repository
git clone [https://github.com/yourusername/LogTriage.git](https://github.com/yourusername/LogTriage.git)
cd LogTriage

# 2. Create and activate a Python virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install core dependencies
pip install websockets google-genai requests

# 4. Set your Google Gemini API key as an environment variable
# On Windows (PowerShell):
$env:GEMINI_API_KEY="your_actual_api_key_here"
# On Linux/macOS:
export GEMINI_API_KEY="your_actual_api_key_here"
```

## Usage

`LogTriage` is separated into a headless data-plane (the Python pipeline) and a decoupled visualization layer (the web UI). You must run the backend engine before connecting the dashboard.

### 1. Start the Triage Engine

Initialize the multi-threaded backend from the root directory. This will spin up the log producers, consumers, the WebSocket broadcast server on port `8000`, and the Gemini aggregation thread.

```bash
# Ensure your virtual environment is active, then run:
python main.py
```

**Expected Output:**
```text
[SYSTEM] Starting Log Parsing Engine...
[SYSTEM] Engine running. Real-time metrics streaming on ws://localhost:8000
[SYSTEM] Press Ctrl+C to terminate gracefully.
```

### 2. Launch the Telemetry Dashboard

Because the UI relies purely on client-side JavaScript and WebSockets, no heavy web framework is required. Simply open the `dashboard.html` file in your preferred browser.

**Via CLI (Windows PowerShell):**
```powershell
Start-Process chrome.exe .\web\dashboard.html
```

**Via CLI (macOS):**
```bash
open ./web/dashboard.html
```

Once opened, the dashboard will immediately latch onto `ws://localhost:8000`. You will see the connection status turn green, the charts begin to roll, and live structural anomalies generated by the AI stream directly into the diagnostic desk.

---
