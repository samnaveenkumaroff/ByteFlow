# ⚡ PriceRadar — Agentic Competitive Intelligence for Indian E-Commerce

> **ByteFlow Mart** · Problem Statement **PS D 3**

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

**PriceRadar** is a local-first, privacy-preserving, agentic competitive intelligence platform for Indian e-commerce sellers.

It autonomously monitors competitor listings across major marketplaces, analyzes pricing gaps, delivery advantages, discounts, and review sentiment, and produces **priority-ranked, one-click actionable strategies** powered by a hybrid rule engine and on-device LLM — without sending any seller data to external APIs.

---

## 📋 Table of Contents

- [Problem Statement — PS D 3](#problem-statement--ps-d-3)
- [What Is PriceRadar?](#what-is-priceradar)
- [Full Workflow](#full-workflow)
- [System Architecture](#system-architecture)
- [Why This Approach](#why-this-approach)
- [Why Qwen3-8B-Instruct — LLM Benchmark Comparison](#why-qwen3-8b-instruct--llm-benchmark-comparison)
- [How We Use Qwen3-8B-Instruct](#how-we-use-qwen3-8b-instruct)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup-without-docker)
- [Docker Deployment](#docker--development-mode)
- [API Reference](#api-reference)
- [Dataset](#dataset)
- [License](#license)

---

## Problem Statement — PS D 3

Sellers face a **competitive intelligence overload** where rapid cross-platform price shifts, delivery advantages, and sentiment signals exceed human monitoring capacity.

Traditional scraping tools provide raw data but lack reasoning capability to connect signals — such as:

- A price drop triggered by negative reviews
- Delivery advantage driving conversion shifts
- Discount wars across platforms
- Feature complaints influencing demand

This creates a strategic blind spot requiring an **agentic layer that proactively recommends actions before revenue loss occurs.**

---

## What Is PriceRadar?

PriceRadar is a full-stack competitive intelligence system that:

✔ Scrapes live competitor data  
✔ Matches equivalent products across platforms  
✔ Computes market gaps and trends  
✔ Analyzes review sentiment  
✔ Generates actionable strategies  
✔ Applies updates with one click  
✔ Works fully offline with local AI  

Supported platforms:

- Flipkart  
- Amazon  
- Croma  
- Reliance Digital  
- Vijay Sales  

---

## Full Workflow
Seller Input → Scraping → Matching → Market Analysis →
Strategy Generation → LLM Advisory → Seller Action →
Monitoring → Alerts → One-Click Update


Key outputs:

- Optimized pricing recommendations
- Delivery improvements
- Promotional strategies
- Competitive positioning insights
- Automated update suggestions

---

## System Architecture

### Core Components

Frontend → FastAPI Backend → Strategy Engine → LLM → Data Layer → Scraper → Scheduler

**Rule Engine:** Deterministic logic for instant decisions  
**LLM Layer:** Context-aware strategic reasoning  
**Scheduler:** Autonomous 24-hour monitoring loop  

---

## Why This Approach

### Hybrid Rule Engine + LLM

Pure LLM systems are slow and unpredictable.  
Pure rule systems cannot handle novel situations.

PriceRadar combines both:

| Feature | Rule Engine | LLM | Hybrid |
|----------|------------|------|--------|
Speed | ⚡ Instant | Slow | Fast |
Reliability | High | Variable | High |
Reasoning | Low | High | High |
Offline | Yes | No | Yes |
Explainability | High | Medium | High |

---

## Why Qwen3-8B-Instruct — LLM Benchmark Comparison

Selected for:

- Strong instruction following
- High numerical reasoning accuracy
- Local inference capability
- Apache 2.0 license
- CPU-friendly quantized deployment
- No external API dependency

Runs via Ollama:

ollama pull qcwind/qwen3-8b-instruct-Q4-K-M


---

## How We Use Qwen3-8B-Instruct

The LLM acts as a strategic advisor, not a decision maker.

### Use Cases

1. Strategy explanation based on market data  
2. Insights from review sentiment  
3. Competitive positioning suggestions  
4. Marketing ideas grounded in evidence  

All core actions remain deterministic for reliability.

---

## Tech Stack

| Layer | Technology |
|--------|------------|
Backend | FastAPI |
LLM Runtime | Ollama |
Model | Qwen3-8B-Instruct |
Scraping | Playwright |
Scheduler | Python schedule |
Storage | JSON files |
Frontend | Streamlit / Static Web |
Containerization | Docker |
Language | Python 3.11+ |

---

## Project Structure
project/
├── ai/
├── strategy/
├── scraper/
├── scheduler/
├── data/
├── dashboard.py
├── server.py
├── requirements.txt


---

## Local Setup (Without Docker)

### Prerequisites

- Python 3.11+
- Ollama installed

### Installation

git clone <repo>
cd priceradar
pip install -r requirements.txt
pip install playwright
playwright install chromium


### Pull Model

ollama pull qcwind/qwen3-8b-instruct-Q4-K-M
ollama serve


### Run Application

python server.py


---

## Docker — Development Mode

docker compose --profile dev up --build

---

## API Reference

### Seller

GET `/api/seller/products` — List products  
POST `/api/seller/analyze` — Analyze competition  
POST `/api/seller/alerts/scan-all` — Run monitoring  
POST `/api/seller/alerts/ai-strategy/{pid}` — Generate AI insights  

### Strategy Dashboard

GET `/api/strategy/data` — Market dataset  
POST `/api/strategy/apply-all` — Apply optimizations  
POST `/api/strategy/reset` — Restore original data  

---

## Dataset

5 flagship smartphones × 5 platforms × 10 reviews each

Total: **250 real review samples**

---

## License

MIT License — free for academic and commercial use.

---

<p align="center">
Built with ⚡ for PS D 3 · PriceRadar by ByteFlow Mart
</p>
