# WNG Content Platform - Master Documentation

---

## Part 1: Product Requirements Document (PRD)

### 1. Project Overview
The WNG Content Platform is a semi-automated content generation and publishing system tailored for the mental health space. It collects trending topics, generates high-quality, clinical-yet-accessible content intended for parents, and orchestrates publishing to a WordPress CMS and social media. It strictly enforces a human-in-the-loop (HITL) review process to ensure clinical safety, accuracy, and brand alignment.

### 2. Target Audience
- **Primary Users:** Content reviewers, clinical directors, and marketing managers at mental health clinics (e.g., Horizon Therapy Centre).
- **End Consumers (Content Audience):** Parents looking for practical guidance and professional insight regarding child and teen mental health issues.

### 3. Core Objectives
- Streamline the creation of SEO-optimized, engaging mental health content based on current trends.
- Eliminate the risk of publishing insensitive, plagiarized, or inaccurate AI content through forced human review.
- Automate the distribution pipeline (WordPress + multiple social platforms) post-approval.

### 4. Key Features & Functionality

#### 4.1. Trend Discovery & Ingestion
- **Automated Collection:** Uses Celery Beat to run scheduled tasks that scrape trusted RSS feeds and News APIs for trending mental health topics.
- **Duplicate Prevention:** Utilizes vector embeddings and similarity checks to ensure no duplicate or overly similar topics are drafted.

#### 4.2. AI Content Generation Pipeline (LangGraph)
A sequential AI workflow that processes a topic into a highly structured draft:
1. **Understand Problem:** Extracts key points and writes an opening scenario.
2. **Explain to Parent:** Rewrites clinical concepts into accessible child-experience explanations (6th-8th grade reading level).
3. **Research Backing:** Adds scientific context and mental health implications.
4. **Real-World Impact:** Explains daily-life effects and common parent misunderstandings.
5. **Professional Guidance:** Generates step-by-step actionable advice and defines "when to seek help."
6. **Service Mapping:** Connects the issue to specific clinic services.
7. **Reassurance:** Crafts a reassuring Call-To-Action (CTA).
8. **SEO Metadata:** Generates SEO titles, meta descriptions, and keywords.
9. **Social Media:** Drafts variations for Meta (Facebook/Instagram), LinkedIn, and X (Twitter).

#### 4.3. Reviewer Dashboard (Frontend)
- **Draft Management:** View pending drafts, modify text (via TipTap editor), and review AI-generated SEO/social metadata.
- **Human-in-the-Loop:** Explicit "Approve", "Reject", or "Publish" buttons.
- **Insights & Auditing:** View audit logs, track platform performance, competitor intel, and topic backlogs.

#### 4.4. Publishing & Syndication
- **CMS Integration:** Pushes approved content directly to WordPress via REST API.
- **Social Syndication:** Broadcasts associated social posts to Meta, X, and LinkedIn.
- **Compliance:** Automatically appends mandatory medical disclaimers ("This content is for educational purposes only") and source citations prior to publishing.

#### 4.5. Notifications & Logging
- **Alerts:** Notifies reviewers via Telegram or SMTP when new drafts require attention.
- **Audit Trails:** Comprehensive logging of all approvals, rejections, and publishing events to an `audit_logs` table for accountability.

### 5. Hard Guardrails & Constraints
- **NO Auto-Publish:** The backend strictly forbids publishing without an explicit `approved_by` and `approved_at` timestamp.
- **Anti-Plagiarism:** The prompt instructions explicitly forbid reproducing 7+ consecutive words from source materials.
- **Tone & Voice:** Responses must be in first-person plural ("we", "our") simulating a clinician speaking to parents. AI-isms and press-release tones are forbidden.

### 6. Success Metrics
- Reduction in time-to-publish for trending topics.
- Zero instances of unauthorized automated publishing.
- High SEO ranking and social engagement driven by the generated metadata.

---

## Part 2: Project Overview & Architecture

### 1. Executive Summary
The WNG Content Platform is a full-stack, AI-powered content orchestration system. It is designed to automatically ingest trending news, leverage LLMs to draft structured mental health guidance for parents, and await human approval before executing multi-channel publishing (WordPress, Meta, LinkedIn, X).

### 2. Technology Stack

#### Frontend
- **Framework:** Next.js (App Router)
- **Styling:** Tailwind CSS, shadcn/ui (Radix UI primitives)
- **Editor:** TipTap (Rich text WYSIWYG)
- **State/Data:** React Hook Form, Zod (validation)
- **Visuals:** Recharts (Analytics), Framer Motion (Animations)

#### Backend
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL (Relational data), SQLAlchemy (ORM), Alembic (Migrations)
- **Queue/Cache:** Redis, Celery (Distributed task queue & Beat scheduler)
- **AI/LLM orchestration:** LangGraph, LangChain
- **Monitoring:** Sentry

#### Infrastructure & Deployment
- **Containerization:** Docker & Docker Compose
- **Package Management:** `uv` for Python, `npm` for Node.js.

### 3. Architecture & Data Flow
1. **Ingestion (Celery Beat + Scraper Services):** Scheduled workers pull from RSS feeds and News APIs. Data is passed through trusted source filters.
2. **Drafting (FastAPI + LangGraph):** A drafted topic triggers the `ContentGraphRunner`. It moves through a 9-node state graph, prompting the LLM at each step to build specific sections (intro, science, guidance, SEO, social).
3. **Storage (PostgreSQL):** The complete draft, including HTML blocks and metadata, is saved to the database with a pending status.
4. **Review (Next.js Dashboard):** An admin logs in, reviews the draft, makes manual edits, and clicks "Approve" (which logs to the `audit_logs` table).
5. **Publishing (Celery Workers):** Upon the "Publish" command, background workers dispatch the HTML to WordPress via REST API and trigger social media API calls.

### 4. Codebase Structure
```text
wng_content_generator/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers (endpoints for drafts, topics, auth)
│   │   ├── core/          # App config, DB setup, Celery app init, Security
│   │   ├── models/        # SQLAlchemy Database Models (Topic, Article, AuditLog, etc.)
│   │   ├── schemas/       # Pydantic validation schemas (DTOs)
│   │   ├── services/      # Business logic (Scraping, CMS, Social, LLM integration)
│   │   ├── workflows/     # LangGraph definitions (`content_graph.py`)
│   │   └── workers/       # Celery task definitions
│   ├── alembic.ini        # Migration config
│   └── main.py            # FastAPI application entry point
├── frontend/
│   ├── app/               # Next.js App Router (Dashboard, Login, Layouts)
│   ├── components/        # Reusable React/Radix components
│   ├── lib/               # Utility functions
│   └── package.json       # Node dependencies
├── infra/                 # Infrastructure configs (Docker, SQL dumps)
├── docker-compose.yml     # Local orchestration
└── start.sh               # Unified bootstrap script
```

### 5. Development Setup
To run the project locally, a unified `start.sh` script is provided which:
1. Provisions local virtual environments (`uv`).
2. Starts PostgreSQL and Redis in Docker.
3. Runs Alembic database migrations.
4. Installs frontend dependencies.
5. Spawns FastAPI, Celery Worker, Celery Beat, and the Next.js dev server.

Alternatively, the entire stack can be run purely in containers via `docker compose up --build`.

### 6. Security & Safeguards
- **Authentication:** Standard JWT-based auth for dashboard access.
- **Strict State Machines:** A draft cannot physically be sent to the CMS service unless its DB state reflects an active `approved_by` user ID.
- **Auditing:** Every major CRUD and state-change action is recorded in `audit_logs` to maintain compliance transparency.
