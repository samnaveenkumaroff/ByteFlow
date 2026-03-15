# ⚡ ByteFlow Mart PriceRadar🧠 Agentic Competitive Intelligence for Indian E-Commerce

> **ByteFlow Mart** · Problem Statement **PS D-3**
Sellers have hit a competitive intelligence wall where the sheer
velocity of cross-platform pricing shifts, sentiment nuances in
thousands of reviews, and shifting competitor tactics has outpaced
human analytical capacity. Traditional data scraping fails because it
lacks the autonomous reasoning to connect disparate signals—like a
specific material complaint in a reviewto a pricing drop in a
rival'scatalog. This creates a strategic blind spot that requiresan
agentic layerto independently monitor,synthesize, and proactively
suggest pivot strategies before market opportunities evaporate.
<p align="center">
  <img src="https://img.shields.io/badge/PS-D_3-FFD700?style=for-the-badge&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/LLM-Qwen3--8B--Instruct-7C3AED?style=for-the-badge&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/Scraping-Playwright-2EAD33?style=for-the-badge&logo=playwright&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/Runtime-Ollama-black?style=for-the-badge&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&labelColor=0d1117" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/Build-Stable-brightgreen?style=for-the-badge&labelColor=0d1117" />
  <img src="https://img.shields.io/badge/Platform-Local--First-blue?style=for-the-badge&labelColor=0d1117" />
</p>

---

## 🚀 Overview

**PriceRadar** is a local-first, privacy-preserving, agentic competitive intelligence platform designed for Indian e-commerce sellers.

It autonomously monitors competitor listings across major marketplaces, analyzes pricing gaps, delivery advantages, discounts, and review sentiment, and generates **priority-ranked, one-click actionable strategies** using a hybrid rule engine and on-device Large Language Model (LLM).

🔒 No seller data leaves the machine.  
⚡ No external API dependency.  
🧠 Real-time strategic intelligence.

---

## 📋 Table of Contents

- [Problem Statement — PS D-3](#problem-statement--ps-d-3)
- [What Is PriceRadar?](#what-is-priceradar)
- [Full Workflow](#full-workflow)
- [System Architecture](#system-architecture)
- [Why This Approach](#why-this-approach)
- [LLM Selection — Qwen3-8B-Instruct](#llm-selection--qwen3-8b-instruct)
- [How the LLM Is Used](#how-the-llm-is-used)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup-without-docker)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Dataset](#dataset)
- [License](#license)

---

## Problem Statement — PS D-3

Sellers have hit a **competitive intelligence wall** where the velocity of cross-platform price changes, delivery competition, discount wars, and sentiment signals has exceeded human analytical capacity.

Traditional scraping tools provide raw data but lack reasoning ability to connect signals — for example:

- Price drops triggered by negative reviews  
- Faster delivery influencing conversion rates  
- Discount battles across marketplaces  
- Feature complaints impacting demand  

This creates a strategic blind spot requiring an **agentic layer that continuously monitors, synthesizes, and proactively recommends actions before revenue loss occurs.**

---

## What Is PriceRadar?

PriceRadar is a full-stack competitive intelligence system that:

✔ Scrapes live competitor data  
✔ Matches equivalent products across platforms  
✔ Computes market gaps and trends  
✔ Analyzes review sentiment  
✔ Generates actionable strategies  
✔ Applies optimizations with one click  
✔ Operates fully offline with local AI  

### Supported Platforms

- Flipkart  
- Amazon  
- Croma  
- Reliance Digital  
- Vijay Sales  

---

## Full Workflow

Seller Input
↓
Automated Scraping
↓
Product Matching
↓
Market Analysis
↓
Strategy Generation (Rule Engine)
↓
LLM Strategic Advisory
↓
Seller Decision / One-Click Apply
↓
Continuous Monitoring
↓
Alerts & Re-Optimization


### Key Outputs

- Optimal pricing recommendations  
- Delivery improvements  
- Promotion strategies  
- Competitive positioning insights  
- Automated update suggestions  

---

## System Architecture

### Core Pipeline

Frontend → FastAPI Backend → Strategy Engine → LLM Layer
→ Data Storage → Scraper → Scheduler


### Components

**Rule Engine**  
Deterministic logic for instant, reliable actions.

**LLM Layer**  
Context-aware reasoning and strategic insight.

**Scheduler**  
Autonomous 24-hour monitoring loop.

**Data Layer**  
Lightweight JSON storage for portability.

---

## Why This Approach

### Hybrid Rule Engine + LLM

Pure LLM systems are slow and unpredictable.  
Pure rule systems cannot handle novel situations.

PriceRadar combines both:

| Capability | Rule Engine | LLM | Hybrid |
|------------|------------|------|--------|
Speed | ⚡ Instant | Slow | Fast |
Reliability | High | Variable | High |
Reasoning | Low | High | High |
Offline Capability | Yes | No | Yes |
Explainability | High | Medium | High |

Result: **Deterministic core + intelligent advisory layer**

---

## LLM Selection — Qwen3-8B-Instruct

Chosen for:

- Excellent instruction adherence  
- Strong numerical reasoning  
- CPU-friendly quantized deployment  
- Fully offline inference  
- Apache 2.0 license  
- No external API requirement  

### Model Variant

Qwen3-8B-Instruct Q4-K-M (Quantized)


### Run via Ollama

bash
ollama pull qcwind/qwen3-8b-instruct-Q4-K-M
ollama serve

## 🧠 How the LLM Is Used

The LLM acts as a **strategic advisor — not the decision engine.**

### Primary Roles

- Explaining strategy recommendations  
- Interpreting review sentiment  
- Suggesting competitive positioning  
- Providing marketing insights  
- Highlighting risks and opportunities  

All operational actions remain **deterministic for reliability**, ensuring consistent system behavior even if the LLM is unavailable.

---

## 🛠 Tech Stack

### Frontend

- HTML / CSS / JavaScript  
- Streamlit Dashboard  

### Backend

- FastAPI  
- Uvicorn  
- Python 3.11+  

### AI / LLM Layer

- Qwen3-8B-Instruct (Q4-K-M quantized model)  
- Ollama — local LLM runtime  

### Scraping

- Playwright — headless browser scraping  
- Chromium Engine — executes JavaScript and waits for DOM  
- Extraction from JS-rendered pages  

#### Platforms Scraped

- Flipkart  
- Amazon  
- Croma  
- Reliance Digital  
- Vijay Sales  

### Automation

- `schedule` — 24-hour autonomous monitoring loop  
- Alert system for price and discount changes  

### Data Storage

Lightweight JSON flat files for portability and zero external dependencies.

#### Examples

- Products  
- Orders  
- Users  
- Competitor data  
- Bundles  
- Seller profile  

---

## 📁 Project Structure

project/
├── ai/ # LLM modules
├── strategy/ # Rule engine & apply logic
├── scraper/ # Competitor scraping
├── scheduler/ # Autonomous monitoring
├── data/ # JSON datasets
├── dashboard.py # Strategy dashboard
├── server.py # FastAPI backend
├── requirements.txt


---

## ⚙️ Local Setup (Without Docker)

### Prerequisites

- Python 3.11+
- Ollama installed

### Installation

bash
git clone <repository-url>
cd priceradar
pip install -r requirements.txt
pip install playwright
playwright install chromium


---

## ⚙️ Local Setup (Without Docker)

### Prerequisites

- Python 3.11+
- Ollama installed

### Installation

bash
git clone <repository-url>
cd priceradar
pip install -r requirements.txt
pip install playwright
playwright install chromium


---

## ⚙️ Local Setup (Without Docker)

### Prerequisites

- Python 3.11+
- Ollama installed

### Installation

bash
git clone <repository-url>
cd priceradar
pip install -r requirements.txt
pip install playwright
playwright install chromium

🐳 Docker Deployment
Development Mode
docker compose --profile dev up --build

📡 API Reference
Seller APIs
Endpoint	Description
GET /api/seller/products	List products
POST /api/seller/analyze	Analyze competition
POST /api/seller/alerts/scan-all	Run monitoring
POST /api/seller/alerts/ai-strategy/{pid}	Generate AI insights
Strategy Dashboard APIs
Endpoint	Description
GET /api/strategy/data	Market dataset
POST /api/strategy/apply-all	Apply optimizations
POST /api/strategy/reset	Restore original data
📊 Dataset

5 flagship smartphones × 5 platforms × 10 reviews each

Total: 250 real review samples

##📄 License

CIT License — free for academic and commercial use.

<p align="center"> ⚡ Built for PS D-3 · PriceRadar by ByteFlow Mart </p> ```
