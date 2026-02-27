# CLAUDE.md — DeutschLerner (德语学习助手)

> **This file is the single source of truth for AI agents (Claude Code, Copilot, etc.) working on this project.**
> Read this ENTIRE file before making any changes.

---

## 1. Project Overview

**DeutschLerner** is a self-hosted German language learning assistant that:

- Uses multiple AI providers (Claude, GPT, Gemini, Kimi, DeepSeek, etc.) OR Claude Code CLI (no API key) to generate learning content
- Tracks vocabulary & sentences the user has/hasn't learned (mark system)
- Maintains persistent memory files (SQLite + JSON export)
- Generates contextual German learning topics based on user input (taught in **Chinese → German**)
- Sends daily "heartbeat" learning topics via **Discord** and/or **WhatsApp** bot
- Exposes a REST API so external platforms (OpenClaw, cron jobs, other services) can control it
- Is fully deployable on Linux servers via Docker

**Language**: Python 3.11+
**Framework**: FastAPI (API server) + APScheduler (heartbeat) + discord.py / Twilio (notifications)
**Database**: SQLite (via SQLAlchemy + aiosqlite)
**CLI**: Rich + Click (interactive terminal UI)

---

## 2. Architecture

```
deutsch-lerner/
│
├── CLAUDE.md                          # THIS FILE — project brain for AI
├── README.md                          # Human-readable project docs (auto-generated at end)
├── pyproject.toml                     # Project metadata & dependencies (use this, NOT setup.py)
├── requirements.txt                   # Pinned dependencies for pip install
├── .env.example                       # Template for environment variables
├── config.yaml                        # Runtime configuration (AI provider, schedule, etc.)
├── Dockerfile                         # Multi-stage Docker build
├── docker-compose.yml                 # Full stack: app + optional reverse proxy
├── Makefile                           # Common commands: make run, make test, make docker
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/                          # ── Business Logic ──
│   │   ├── __init__.py
│   │   ├── engine.py                  # LearningEngine: orchestrates learning sessions
│   │   ├── topic_generator.py         # Generates topics based on user input context
│   │   ├── marker.py                  # Mark vocabulary/sentences as known/unknown/learning
│   │   └── memory.py                  # MemoryManager: CRUD for learned items + dedup
│   │
│   ├── ai/                            # ── AI Provider Abstraction ──
│   │   ├── __init__.py
│   │   ├── base.py                    # ABC: AIProvider with generate() / stream() methods
│   │   ├── claude_api.py              # Anthropic SDK provider
│   │   ├── openai_api.py              # OpenAI SDK provider (GPT-4o, etc.)
│   │   ├── gemini_api.py              # Google GenAI SDK provider
│   │   ├── kimi_api.py                # Moonshot (Kimi) API provider
│   │   ├── deepseek_api.py            # DeepSeek API provider
│   │   ├── claude_cli.py              # Claude Code CLI subprocess provider (NO API key)
│   │   └── factory.py                 # ProviderFactory: create provider by name string
│   │
│   ├── storage/                       # ── Data Persistence ──
│   │   ├── __init__.py
│   │   ├── database.py                # SQLite connection manager (async via aiosqlite)
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── repository.py              # Data access layer (all DB queries here)
│   │   └── migrations.py              # Auto-migration on startup (alembic-lite)
│   │
│   ├── api/                           # ── REST API Server ──
│   │   ├── __init__.py
│   │   ├── server.py                  # FastAPI app factory + lifespan events
│   │   ├── dependencies.py            # Dependency injection (DB session, AI provider, etc.)
│   │   ├── middleware.py              # API key auth, CORS, rate limiting, logging
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── learning.py            # POST /learn — generate topic from input
│   │       ├── vocabulary.py          # CRUD /vocabulary — manage vocab items
│   │       ├── sentences.py           # CRUD /sentences — manage sentences
│   │       ├── memory.py              # GET /memory/export, POST /memory/import
│   │       ├── heartbeat.py           # Heartbeat control: start/stop/status/trigger
│   │       ├── provider.py            # GET /providers, PUT /provider — switch AI
│   │       └── health.py              # GET /health — for load balancers & monitoring
│   │
│   ├── heartbeat/                     # ── Scheduled Learning Push ──
│   │   ├── __init__.py
│   │   ├── scheduler.py              # APScheduler wrapper: cron config, start/stop
│   │   ├── topic_selector.py         # Random topic + history dedup check
│   │   └── dispatcher.py             # Route topic → notification channels
│   │
│   ├── notifications/                 # ── Notification Channels ──
│   │   ├── __init__.py
│   │   ├── base.py                    # ABC: Notifier with send() method
│   │   ├── discord_bot.py            # discord.py bot: send to channel or DM
│   │   └── whatsapp.py               # Twilio WhatsApp API integration
│   │
│   └── cli/                           # ── CLI Interactive Mode ──
│       ├── __init__.py
│       └── interactive.py             # Rich-based terminal UI for learning sessions
│
├── data/                              # ── Runtime Data (gitignored except structure) ──
│   ├── .gitkeep
│   └── deutsch_lerner.db             # SQLite database (auto-created)
│
├── prompts/                           # ── System Prompts (version controlled) ──
│   ├── topic_generation.md            # Prompt: generate learning topic (Chinese→German)
│   ├── vocabulary_practice.md         # Prompt: vocabulary quiz / explanation
│   ├── sentence_practice.md           # Prompt: sentence construction practice
│   └── heartbeat_topic.md            # Prompt: daily heartbeat topic generation
│
├── tests/                             # ── Test Suite ──
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures (test DB, mock AI provider)
│   ├── test_ai_providers.py           # Test each AI provider's generate()
│   ├── test_engine.py                 # Test LearningEngine logic
│   ├── test_marker.py                 # Test mark/unmark operations
│   ├── test_memory.py                 # Test memory dedup, export, import
│   ├── test_api.py                    # Test all REST endpoints (httpx + pytest)
│   ├── test_heartbeat.py             # Test scheduler + topic dedup
│   └── test_notifications.py         # Test Discord/WhatsApp dispatching (mocked)
│
└── scripts/
    ├── setup.sh                       # One-click setup: venv + deps + .env + DB init
    └── deploy.sh                      # Deploy to Linux server (systemd or docker)
```

---

## 3. Database Schema (SQLite via SQLAlchemy)

```sql
-- Core vocabulary tracking
CREATE TABLE vocabulary (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    german      TEXT NOT NULL,               -- German word (e.g., "Wohnung")
    chinese     TEXT NOT NULL,               -- Chinese translation (e.g., "住房")
    phonetic    TEXT,                         -- IPA or simplified pronunciation
    part_of_speech TEXT,                      -- noun, verb, adj, etc.
    gender      TEXT,                         -- der/die/das (for nouns)
    example     TEXT,                         -- Example sentence in German
    status      TEXT NOT NULL DEFAULT 'unknown',  -- unknown | learning | known
    difficulty  INTEGER DEFAULT 0,           -- 0-5 scale
    review_count INTEGER DEFAULT 0,          -- how many times reviewed
    last_reviewed_at TIMESTAMP,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(german)
);

-- Sentence tracking
CREATE TABLE sentences (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    german      TEXT NOT NULL,               -- German sentence
    chinese     TEXT NOT NULL,               -- Chinese translation
    grammar_notes TEXT,                       -- Grammar explanation
    source_topic TEXT,                        -- Which topic generated this
    status      TEXT NOT NULL DEFAULT 'unknown',
    review_count INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMP,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Topic history (for heartbeat dedup)
CREATE TABLE topic_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    topic       TEXT NOT NULL,               -- Topic title/description
    category    TEXT,                         -- grammar, vocabulary, culture, daily, etc.
    content     TEXT NOT NULL,               -- Full generated content
    source      TEXT DEFAULT 'heartbeat',    -- heartbeat | user_input | api
    sent_via    TEXT,                         -- discord | whatsapp | api | cli
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning sessions log
CREATE TABLE learning_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_type TEXT NOT NULL,              -- topic | vocabulary_review | sentence_practice
    user_input  TEXT,                         -- What user typed to trigger this
    ai_provider TEXT NOT NULL,               -- claude | openai | gemini | kimi | claude_cli
    content     TEXT NOT NULL,               -- AI-generated content
    vocab_added INTEGER DEFAULT 0,           -- # new vocab from this session
    sentences_added INTEGER DEFAULT 0,       -- # new sentences from this session
    duration_seconds INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration store (runtime overrides)
CREATE TABLE app_config (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. AI Provider Interface

Every AI provider MUST implement this interface:

```python
# src/ai/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional

@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    raw_response: Optional[dict] = None

class AIProvider(ABC):
    """Base class for all AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name: 'claude', 'openai', 'gemini', 'kimi', 'deepseek', 'claude_cli'"""
        ...

    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        """Generate a complete response."""
        ...

    @abstractmethod
    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        """Stream response chunks for CLI mode."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is accessible."""
        ...
```

### Provider-Specific Notes

| Provider | SDK Package | Auth | Notes |
|----------|-------------|------|-------|
| Claude API | `anthropic` | `ANTHROPIC_API_KEY` | Use claude-sonnet-4-20250514 default |
| OpenAI/GPT | `openai` | `OPENAI_API_KEY` | Support gpt-4o, gpt-4o-mini |
| Gemini | `google-genai` | `GOOGLE_API_KEY` | Use gemini-2.0-flash default |
| Kimi | `openai` (compat) | `KIMI_API_KEY` | Moonshot API, OpenAI-compatible endpoint |
| DeepSeek | `openai` (compat) | `DEEPSEEK_API_KEY` | OpenAI-compatible endpoint |
| Claude CLI | subprocess | None | Calls `claude` binary, parses stdout |

### Claude CLI Provider Implementation

```python
# src/ai/claude_cli.py — Key implementation details
import asyncio
import subprocess
import json

class ClaudeCLIProvider(AIProvider):
    """Uses Claude Code CLI binary — NO API key needed."""

    @property
    def name(self) -> str:
        return "claude_cli"

    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        full_prompt = f"{system_prompt}\n\n{user_message}"
        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", full_prompt, "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {stderr.decode()}")
        return AIResponse(
            content=stdout.decode().strip(),
            provider="claude_cli",
            model="claude-code",
        )
```

---

## 5. Core Learning Engine

```python
# src/core/engine.py — Key design

class LearningEngine:
    """
    Central orchestrator for all learning activities.

    Responsibilities:
    1. Accept user input (a topic, question, or context)
    2. Build a prompt that includes memory context (known/unknown items)
    3. Send to AI provider
    4. Parse response to extract new vocabulary & sentences
    5. Store results in database
    6. Return formatted learning content
    """

    def __init__(self, ai_provider: AIProvider, memory: MemoryManager, db: Repository):
        self.ai = ai_provider
        self.memory = memory
        self.db = db

    async def learn_topic(self, user_input: str) -> LearningResult:
        """
        Main learning flow:
        1. Load user's current vocabulary status from memory
        2. Build context-aware prompt (include known words to avoid repetition)
        3. Generate topic content via AI
        4. Extract vocabulary and sentences from AI response
        5. Auto-mark new items as 'unknown'
        6. Return structured result
        """
        ...

    async def review_vocabulary(self, count: int = 10) -> list[VocabItem]:
        """Pick 'unknown' or 'learning' items for review, prioritize low review_count."""
        ...

    async def mark_item(self, item_type: str, item_id: int, status: str) -> bool:
        """Mark a vocabulary word or sentence as known/unknown/learning."""
        ...
```

---

## 6. Topic Generation System

### How Topics Are Generated

The AI receives a system prompt (from `prompts/topic_generation.md`) that instructs it to:

1. **Use Chinese as the teaching language** (用中文教德语)
2. Based on the user's input, create a structured lesson with:
   - **主题 (Topic)**: A German topic title + Chinese explanation
   - **核心词汇 (Core Vocabulary)**: 5-10 German words with Chinese meanings, gender, examples
   - **重点句型 (Key Sentence Patterns)**: 3-5 German sentences with Chinese translation + grammar notes
   - **语法提示 (Grammar Tips)**: Brief grammar explanation in Chinese
   - **练习 (Exercise)**: A mini exercise for practice
3. The AI response is parsed into structured data (vocab items + sentences) and stored

### System Prompt Template (`prompts/topic_generation.md`)

```markdown
你是一位专业的德语教师，用中文教授德语。根据用户提供的主题或输入内容，生成一个结构化的德语学习课程。

## 输出格式（必须严格遵守JSON格式）

请以以下JSON格式输出：

{
  "topic_title_de": "德语主题标题",
  "topic_title_cn": "中文主题标题",
  "summary_cn": "用2-3句中文概述这个主题",
  "vocabulary": [
    {
      "german": "德语单词",
      "chinese": "中文翻译",
      "gender": "der/die/das（名词必填）",
      "part_of_speech": "词性",
      "example_de": "德语例句",
      "example_cn": "例句中文翻译"
    }
  ],
  "sentences": [
    {
      "german": "德语句子",
      "chinese": "中文翻译",
      "grammar_note": "语法说明（中文）"
    }
  ],
  "grammar_tips": "语法提示（中文，简洁明了）",
  "exercise": "练习题（中文出题，要求用德语回答）"
}

## 规则
- 词汇数量：5-10个
- 句子数量：3-5个
- 所有解释用中文
- 德语内容需要准确，包含正确的冠词和变位
- 难度适中，适合A1-B1水平的学习者
- 如果用户输入的是一个生活场景，请围绕该场景展开
- 如果用户输入的是一个语法点，请重点讲解该语法
```

---

## 7. Heartbeat System

### Design

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  APScheduler │────▶│  TopicSelector   │────▶│   Dispatcher     │
│  (cron job)  │     │  - random pick   │     │  - Discord bot   │
│              │     │  - dedup check   │     │  - WhatsApp API  │
│  Configurable│     │  - category      │     │  - both          │
│  interval    │     │    rotation      │     │                  │
└──────────────┘     └─────────────────┘     └──────────────────┘
```

### Topic Selection Algorithm

```python
# src/heartbeat/topic_selector.py

TOPIC_CATEGORIES = [
    "daily_life",       # 日常生活 (shopping, cooking, transport)
    "grammar",          # 语法 (cases, tenses, word order)
    "culture",          # 文化 (festivals, traditions, customs)
    "business",         # 商务德语 (office, meetings, emails)
    "travel",           # 旅游 (directions, hotel, restaurant)
    "academic",         # 学术 (university, research, presentations)
    "idioms",           # 习语和谚语 (idioms and proverbs)
    "news_vocabulary",  # 新闻词汇 (politics, economy, technology)
]

class TopicSelector:
    async def select_topic(self) -> str:
        """
        1. Pick a random category (weighted: less-used categories get higher weight)
        2. Generate a specific topic within that category
        3. Check topic_history table: has this exact topic been sent before?
        4. If yes → regenerate (max 3 retries, then force a new category)
        5. If no → return topic for content generation
        6. Store in topic_history after sending
        """
```

### Heartbeat Configuration (in `config.yaml`)

```yaml
heartbeat:
  enabled: true
  schedule:
    type: "cron"           # cron | interval
    hour: 9                # Send at 9 AM
    minute: 0
    timezone: "Europe/Berlin"
  # OR interval mode:
  # type: "interval"
  # hours: 24
  channels:
    - type: "discord"
      enabled: true
    - type: "whatsapp"
      enabled: false
  max_retry_on_duplicate: 3
  category_weights: "auto"  # auto-balance or manual weights
```

---

## 8. REST API Design

Base URL: `http://<host>:8000/api/v1`

### Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| **Learning** | | | |
| POST | `/learn` | Generate topic from user input | API Key |
| POST | `/learn/review` | Get vocabulary review session | API Key |
| **Vocabulary** | | | |
| GET | `/vocabulary` | List all vocabulary (filter by status) | API Key |
| POST | `/vocabulary` | Add vocabulary manually | API Key |
| PATCH | `/vocabulary/{id}` | Update vocab status (mark known/unknown) | API Key |
| DELETE | `/vocabulary/{id}` | Remove vocabulary item | API Key |
| GET | `/vocabulary/stats` | Vocabulary statistics | API Key |
| **Sentences** | | | |
| GET | `/sentences` | List all sentences (filter by status) | API Key |
| POST | `/sentences` | Add sentence manually | API Key |
| PATCH | `/sentences/{id}` | Update sentence status | API Key |
| **Memory** | | | |
| GET | `/memory/export` | Export all data as JSON | API Key |
| POST | `/memory/import` | Import data from JSON | API Key |
| GET | `/memory/stats` | Overall learning statistics | API Key |
| **Heartbeat** | | | |
| GET | `/heartbeat/status` | Current heartbeat scheduler status | API Key |
| POST | `/heartbeat/start` | Start heartbeat scheduler | API Key |
| POST | `/heartbeat/stop` | Stop heartbeat scheduler | API Key |
| POST | `/heartbeat/trigger` | Manually trigger one heartbeat NOW | API Key |
| GET | `/heartbeat/history` | View past heartbeat topics | API Key |
| **Provider** | | | |
| GET | `/providers` | List available AI providers | API Key |
| GET | `/provider/current` | Get current provider | API Key |
| PUT | `/provider` | Switch AI provider | API Key |
| **System** | | | |
| GET | `/health` | Health check (for load balancers) | None |
| GET | `/info` | App version + config summary | API Key |

### Authentication

```python
# Simple API key authentication via header
# Header: X-API-Key: <your-key>
# Key is set in config.yaml or DEUTSCH_LERNER_API_KEY env var
```

### Example API Calls

```bash
# Generate a learning topic
curl -X POST http://localhost:8000/api/v1/learn \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"input": "我想学习在超市购物的德语", "provider": "claude"}'

# Mark vocabulary as known
curl -X PATCH http://localhost:8000/api/v1/vocabulary/42 \
  -H "X-API-Key: your-key" \
  -d '{"status": "known"}'

# Trigger heartbeat manually
curl -X POST http://localhost:8000/api/v1/heartbeat/trigger \
  -H "X-API-Key: your-key"

# Switch AI provider
curl -X PUT http://localhost:8000/api/v1/provider \
  -H "X-API-Key: your-key" \
  -d '{"provider": "gemini", "model": "gemini-2.0-flash"}'
```

---

## 9. Notification Channels

### Discord Bot (`src/notifications/discord_bot.py`)

```python
# Uses discord.py library
# Bot sends rich embeds with:
# - Topic title (German + Chinese)
# - Vocabulary table
# - Key sentences
# - Grammar tips
# - Mini exercise
#
# Config needed:
#   DISCORD_BOT_TOKEN=xxx
#   DISCORD_CHANNEL_ID=xxx  (or DM to specific user)
```

### WhatsApp via Twilio (`src/notifications/whatsapp.py`)

```python
# Uses Twilio Python SDK
# Sends formatted text message (WhatsApp has limited formatting)
#
# Config needed:
#   TWILIO_ACCOUNT_SID=xxx
#   TWILIO_AUTH_TOKEN=xxx
#   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
#   WHATSAPP_TO=whatsapp:+49xxxxxxxxx
```

---

## 10. Configuration System

### `config.yaml` (primary config)

```yaml
# DeutschLerner Configuration
app:
  name: "DeutschLerner"
  version: "1.0.0"
  debug: false
  log_level: "INFO"

server:
  host: "0.0.0.0"
  port: 8000
  api_key: "${DEUTSCH_LERNER_API_KEY}"  # env var reference

ai:
  default_provider: "claude"
  default_model: null  # null = use provider's default
  timeout: 60  # seconds
  max_retries: 3

database:
  path: "data/deutsch_lerner.db"

heartbeat:
  enabled: true
  schedule:
    type: "cron"
    hour: 9
    minute: 0
    timezone: "Europe/Berlin"
  channels:
    discord:
      enabled: true
      bot_token: "${DISCORD_BOT_TOKEN}"
      channel_id: "${DISCORD_CHANNEL_ID}"
    whatsapp:
      enabled: false
      account_sid: "${TWILIO_ACCOUNT_SID}"
      auth_token: "${TWILIO_AUTH_TOKEN}"
      from_number: "${TWILIO_WHATSAPP_FROM}"
      to_number: "${WHATSAPP_TO}"

learning:
  difficulty: "A2"  # A1, A2, B1, B2
  vocab_per_topic: 8
  sentences_per_topic: 4
  teaching_language: "chinese"
```

### `.env.example`

```bash
# === AI Provider API Keys (only need the ones you use) ===
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxx
KIMI_API_KEY=xxx
DEEPSEEK_API_KEY=sk-xxx

# === App Security ===
DEUTSCH_LERNER_API_KEY=your-secure-api-key-here

# === Discord Bot ===
DISCORD_BOT_TOKEN=xxx
DISCORD_CHANNEL_ID=123456789

# === WhatsApp (Twilio) ===
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
WHATSAPP_TO=whatsapp:+49xxxxxxxxxx
```

---

## 11. Deployment

### Docker

```dockerfile
# Dockerfile — Multi-stage build
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM base AS production
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.api.server:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: "3.8"
services:
  deutsch-lerner:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data          # Persist database
      - ./config.yaml:/app/config.yaml
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Systemd (alternative to Docker)

```ini
# /etc/systemd/system/deutsch-lerner.service
[Unit]
Description=DeutschLerner German Learning Assistant
After=network.target

[Service]
Type=simple
User=deutsch
WorkingDirectory=/opt/deutsch-lerner
EnvironmentFile=/opt/deutsch-lerner/.env
ExecStart=/opt/deutsch-lerner/.venv/bin/python -m uvicorn src.api.server:create_app --factory --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 12. CLI Interactive Mode

```bash
# Start interactive learning session
python -m src.cli.interactive

# Or via the main entry point
python main.py cli

# Or use specific AI provider
python main.py cli --provider claude_cli  # Uses Claude Code, no API key needed
python main.py cli --provider gemini
```

### CLI Commands (inside interactive mode)

```
Available commands:
  /topic <text>     — Generate a topic about <text>
  /review           — Review unknown/learning vocabulary
  /mark <id> known  — Mark vocabulary #id as known
  /mark <id> unknown— Mark vocabulary #id as unknown
  /stats            — Show learning statistics
  /export           — Export memory to JSON
  /provider <name>  — Switch AI provider
  /heartbeat on/off — Toggle heartbeat
  /help             — Show this help
  /quit             — Exit
```

---

## 13. Entry Points

```python
# main.py — Single entry point
"""
Usage:
    python main.py serve          # Start API server (+ heartbeat if enabled)
    python main.py cli            # Start interactive CLI
    python main.py heartbeat      # Run one heartbeat cycle and exit
    python main.py migrate        # Run database migrations
    python main.py export         # Export all data to JSON
    python main.py import <file>  # Import data from JSON
"""
```

---

## 14. Dependencies (`pyproject.toml`)

```toml
[project]
name = "deutsch-lerner"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    # Web framework
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",

    # Database
    "sqlalchemy>=2.0",
    "aiosqlite>=0.20.0",

    # AI SDKs
    "anthropic>=0.40.0",
    "openai>=1.50.0",
    "google-genai>=1.0.0",

    # Scheduling
    "apscheduler>=3.10",

    # Notifications
    "discord.py>=2.3",
    "twilio>=9.0",

    # CLI
    "click>=8.1",
    "rich>=13.0",

    # Config
    "pyyaml>=6.0",
    "python-dotenv>=1.0",

    # HTTP client (for Kimi/DeepSeek)
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
    "httpx>=0.27.0",     # For TestClient
    "ruff>=0.8.0",       # Linter + formatter
]
```

---

## 15. Implementation Order (for AI agents)

> **FOLLOW THIS ORDER.** Each step builds on the previous.

### Phase 1: Foundation
1. `pyproject.toml` + `requirements.txt` — dependency definitions
2. `config.yaml` + `.env.example` — configuration templates
3. `src/storage/models.py` — SQLAlchemy ORM models
4. `src/storage/database.py` — database connection + init
5. `src/storage/repository.py` — data access layer
6. `src/storage/migrations.py` — auto-create tables on startup

### Phase 2: AI Layer
7. `src/ai/base.py` — abstract provider interface
8. `src/ai/claude_api.py` — Claude provider
9. `src/ai/openai_api.py` — OpenAI/GPT provider
10. `src/ai/gemini_api.py` — Gemini provider
11. `src/ai/kimi_api.py` — Kimi provider (OpenAI-compatible)
12. `src/ai/deepseek_api.py` — DeepSeek provider (OpenAI-compatible)
13. `src/ai/claude_cli.py` — Claude Code CLI provider
14. `src/ai/factory.py` — provider factory

### Phase 3: Core Logic
15. `prompts/` — all system prompt templates
16. `src/core/memory.py` — memory manager
17. `src/core/marker.py` — vocabulary/sentence marker
18. `src/core/topic_generator.py` — topic generation with parsing
19. `src/core/engine.py` — main learning engine

### Phase 4: API Server
20. `src/api/middleware.py` — auth + CORS + logging
21. `src/api/dependencies.py` — DI setup
22. `src/api/routes/health.py` — health check
23. `src/api/routes/learning.py` — learning endpoints
24. `src/api/routes/vocabulary.py` — vocab CRUD
25. `src/api/routes/sentences.py` — sentence CRUD
26. `src/api/routes/memory.py` — export/import
27. `src/api/routes/heartbeat.py` — heartbeat control
28. `src/api/routes/provider.py` — provider switching
29. `src/api/server.py` — FastAPI app factory

### Phase 5: Heartbeat + Notifications
30. `src/notifications/base.py` — notifier interface
31. `src/notifications/discord_bot.py` — Discord bot
32. `src/notifications/whatsapp.py` — WhatsApp via Twilio
33. `src/heartbeat/topic_selector.py` — topic selection + dedup
34. `src/heartbeat/dispatcher.py` — notification dispatch
35. `src/heartbeat/scheduler.py` — APScheduler integration

### Phase 6: CLI + Entry Points
36. `src/cli/interactive.py` — Rich-based interactive CLI
37. `main.py` — entry point with Click commands

### Phase 7: Deployment + Tests
38. `Dockerfile` + `docker-compose.yml`
39. `Makefile`
40. `scripts/setup.sh` + `scripts/deploy.sh`
41. `tests/` — full test suite
42. `README.md` — comprehensive human-readable docs

---

## 16. Coding Standards

- **Python 3.11+** — use modern syntax (match/case, type hints, `|` union)
- **Async everywhere** — all DB and AI calls are async
- **Type hints required** — every function signature must have full type hints
- **Pydantic models** for all API request/response schemas
- **Error handling** — never let exceptions crash the server; use structured error responses
- **Logging** — use `logging` module with structured context (provider name, session ID, etc.)
- **No hardcoded strings** — prompts in `prompts/` folder, config in `config.yaml`
- **Docstrings** — every public class and function must have a docstring
- **Ruff** for linting and formatting (configured in `pyproject.toml`)

---

## 17. Key Design Decisions & Rationale

| Decision | Rationale |
|----------|-----------|
| SQLite over PostgreSQL | Single-server deployment, zero config, file-based backup, plenty fast for this use case |
| FastAPI over Flask | Async native, auto OpenAPI docs, Pydantic validation, modern Python |
| APScheduler over Celery | No need for Redis/RabbitMQ; APScheduler is lightweight for single-server cron |
| Provider factory pattern | Easy to add new AI providers without touching existing code |
| JSON prompt responses | Structured output makes it reliable to extract vocab/sentences automatically |
| Chinese teaching language | User requirement — all explanations in Chinese, German as target language |
| API key auth (not OAuth) | Simple, sufficient for personal/server-to-server use; can upgrade later |
| Claude CLI as provider | Allows usage without any API key; uses locally installed Claude Code binary |

---

## 18. Testing Strategy

```bash
# Run all tests
pytest tests/ -v --cov=src

# Run specific test
pytest tests/test_api.py -v

# Run with async support
pytest tests/ -v --asyncio-mode=auto
```

- **Unit tests**: each AI provider, engine logic, marker, memory manager
- **Integration tests**: full API endpoint tests with TestClient + test SQLite DB
- **Mock AI providers**: use a `MockProvider` that returns canned responses for deterministic tests
- **Test fixtures**: shared `conftest.py` with test DB, mock providers, sample data

---

## 19. Common Pitfalls — READ BEFORE CODING

1. **Claude CLI binary path**: On some systems, `claude` might not be in PATH. Add a config option for the binary path.
2. **SQLite async**: Must use `aiosqlite` with SQLAlchemy async engine. Don't use sync SQLite driver.
3. **Discord bot event loop**: `discord.py` runs its own event loop. Run it in a separate thread alongside FastAPI.
4. **APScheduler + FastAPI**: Use `AsyncIOScheduler` and attach to FastAPI's lifespan events.
5. **JSON parsing from AI**: AI responses may include markdown code fences. Strip them before `json.loads()`.
6. **Prompt injection**: Sanitize user input before sending to AI. Don't let user input override system prompts.
7. **Rate limiting**: AI APIs have rate limits. Implement exponential backoff in the base provider.
8. **Unicode**: German special chars (ä, ö, ü, ß) + Chinese chars — ensure UTF-8 everywhere.
9. **Timezone**: Heartbeat schedule must respect timezone. Use `pytz` or `zoneinfo`.
10. **Graceful shutdown**: Handle SIGTERM properly — stop scheduler, close DB, finish in-flight requests.
