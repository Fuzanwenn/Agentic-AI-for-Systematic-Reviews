# LUMINA: Agentic AI Framework for Systematic Review Automation

[![Publication](https://img.shields.io/badge/Published-NEJM%20AI%202025-blue)](https://www.nejm-ai.org)  
[![LLM](https://img.shields.io/badge/Powered%20By-LLMs-orange)](https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/)  

---

## 📌 Overview
**LUMINA** (Learning-based Unified Multi-agent for INtegrated Article screening) is an **agentic AI framework** that leverages **large language models (LLMs)** to transform how systematic reviews and meta-analyses (SRMAs) are conducted.  

Manual screening in SRMAs is notoriously **time-consuming, error-prone, and inconsistent**. Our framework introduces **multi-agent collaboration**, **Chain-of-Thought reasoning**, and **peer-review style auditing** to achieve **human-level sensitivity with higher efficiency and reproducibility**.  

Published in **NEJM AI (2025)**, LUMINA demonstrates how **LLMs can augment medical evidence synthesis** with transparency, scalability, and cost efficiency.

---

## 🚀 Key Features

- **Multi-Agent Architecture**
  - **Classifier Agent** – triages citations (`Potentially Relevant`, `Likely Irrelevant`, `Uncertain`) with bias toward sensitivity.
  - **Detailed Screening Agent** – applies **structured Chain-of-Thought (CoT)** prompts aligned with the **PICOS framework** (Population, Intervention, Comparison, Outcome, Study design).
  - **Reviewer Agent** – audits decisions, ensures consistency, and invokes improvement when needed.
  - **Improvement Agent** – performs self-correction and refinement when conflicts or errors are detected.

- **Research-Grade Performance**
  - **Sensitivity:** 98.2% (SD 2.7%)  
  - **Specificity:** 87.9% (SD 8.4%)  
  - Outperformed state-of-the-art LLM screening baselines in **4 out of 15 SRMAs**.

- **Transparent + Scalable**
  - Decisions explained via structured reasoning.  
  - Can be scaled to thousands of citations per review.  

- **Cost-Efficient**
  - Average screening cost of ~$0.07 per 10 articles.  
  - Processing time ~6.7 minutes for 10 citations.  

---

## 🧠 Why LLMs?
Traditional machine learning models struggle with nuanced reasoning in biomedical literature.  
LLMs (GPT-4, GPT-4o, Claude, etc.) allow:
- **Semantic understanding** of complex clinical abstracts.  
- **Structured reasoning via Chain-of-Thought prompts.**  
- **Self-reflection and correction** when combined with agentic orchestration.  

LUMINA harnesses these capabilities in a **multi-agent loop** that mimics the **human peer-review process**.

---

## 🏗️ System Architecture

### 🧮 Classifier Agent
- **Role:** First pass triage of every citation.  
- **Outputs:** `Potentially Relevant | Uncertain | Likely Irrelevant`.  
- **Events Emitted:** `triage.event`.

### 🕵️ Reviewer Agent
- **Role:** Acts as the **first gatekeeper** after each classifier or screener decision.  
- **Decisions:**  
  - `agree?` → whether the decision is logically consistent.  
  - `include?` → whether to forward to the next stage.  
- **Events Emitted:** `review.event`.  
- **Notes:** Mirrors the two *diamond decision points* in the system diagram.

### 🔄 Improver Agent
- **Role:** Self-correction loop.  
- **Triggered When:** `agree? = false` at **any gate**.  
- **Action:** Generates an amended rationale/label and re-routes output back to the **Reviewer**.  

### 📑 Detailed Screening Agent
- **Role:** Secondary screening for items marked as *Potentially Relevant* or *Uncertain* **and** `include? = true` at the first gate.  
- **Method:** Produces **PICOS-grounded Chain-of-Thought reasoning** plus a **proposed final label**.  
- **Events Emitted:** `screen.event`.

### ✅ Decision Sink
- **Include Set:** Final accepted citations (green checklist).  
- **Discard:** Final rejected citations (yellow oval).  
- **Terminal State:** Every citation must end in either `Include` or `Discard`.  

📌 *Invariant:* Every decision made by Classifier or Detailed Screening Agent **must** pass through the Reviewer. Any disagreement is resolved through the Improver loop before advancing.

---

```mermaid
flowchart LR
  A[Classifier] --> R1[Reviewer]

  %% First review cycle
  R1 -->|Disagree| I1[Improver] --> R1
  R1 -->|Include: Potentially Relevant / Uncertain| S[Detailed Screening]
  R1 -->|Include: Likely Irrelevant| D[Discard]
  R1 -->|Exclude| D

  %% Detailed screening cycle
  S --> R2[Reviewer]
  R2 -->|Disagree| I2[Improver] --> R2
  R2 -->|Include| INC[(Include)]
  R2 -->|Exclude| D


