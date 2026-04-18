# 🤖 Multi-Agent Expense Tracker (MAS)

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.38-green)](https://langchain-ai.github.io/langgraph/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

&gt; **Autonomous multi-agent system for personal expense tracking with AI-powered budget insights.**
&gt; 
&gt; Built with LangGraph + Local LLMs (Llama 3.2 3B) | Zero cloud costs | 100% privacy-focused

---

## Project Overview

This project implements a **4-agent orchestration system** that automates expense tracking through natural language input. Designed as part of SLIIT CTSE4010 Assignment 2 (Multi-Agent Systems), it demonstrates core agentic AI concepts including state management, tool integration, and observability.

### Why This Matters

| Traditional Expense Apps | This Multi-Agent System |
|-------------------------|------------------------|
| Manual form filling | Natural language input ("spent $50 on lunch") |
| Static categorization | AI-assisted category detection |
| No budget insights | Real-time validation + spending advice |
| Cloud-dependent | **Fully local** (privacy-first) |

---

### Agent Responsibilities

| Agent | Role | Key Tool | Output |
|-------|------|----------|--------|
| **Parser** | Natural language understanding | Regex + Pattern Matching | `amount`, `description`, `category` |
| **Validator** | Budget compliance checking | SQLite Budget Query | `validation_status`, `warnings` |
| **Categorizer** | Data normalization | Record Builder | `db_record`, `final_category` |
| **Advisor** | Insight generation | Ollama LLM (3.2 3B) | `advice`, `spending_summary` |

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed locally
- 4GB+ RAM (for local LLM)

### Installation

```bash
# Clone repository
git clone https://github.com/shashitha2002/expense-tracker-mas.git
cd expense-tracker-mas

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Pull local LLM (3.2 3B - lightweight)
ollama pull llama3.2:3b