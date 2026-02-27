# DeutschLerner — 德语学习助手

A self-hosted German language learning assistant that uses AI to generate structured lessons taught in **Chinese → German**.

## Features

- **Multi-AI Provider**: Claude, GPT, Gemini, Kimi, DeepSeek, or Claude Code CLI (no API key needed)
- **Structured Lessons**: Each topic includes vocabulary, sentences, grammar tips, and exercises
- **Vocabulary Tracking**: Mark words as known/learning/unknown with spaced review
- **Heartbeat System**: Daily learning topics sent via Discord and/or WhatsApp
- **REST API**: Full API for integration with external services
- **Interactive CLI**: Rich-based terminal UI for learning sessions
- **Data Portability**: Export/import all learning data as JSON

## Quick Start

```bash
# Clone and setup
git clone <repo-url> && cd deutsch-lerner
bash scripts/setup.sh

# Edit your API keys
nano .env

# Start the API server
python main.py serve

# Or start interactive CLI
python main.py cli
python main.py cli --provider claude_cli  # No API key needed
```

## Usage

### CLI Mode

```bash
python main.py cli --provider gemini
```

Inside the CLI, type a topic or use commands:

```
/topic 在超市购物     — Generate a lesson about supermarket shopping
/review               — Review vocabulary
/mark 42 known        — Mark word #42 as known
/stats                — Show learning statistics
/provider claude_cli  — Switch AI provider
/help                 — Show all commands
```

### API Server

```bash
python main.py serve --port 8000
```

API docs available at `http://localhost:8000/docs`

```bash
# Generate a topic
curl -X POST http://localhost:8000/api/v1/learn \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"input": "在餐厅点餐"}'

# List vocabulary
curl http://localhost:8000/api/v1/vocabulary -H "X-API-Key: your-key"

# Mark as known
curl -X PATCH http://localhost:8000/api/v1/vocabulary/1 \
  -H "X-API-Key: your-key" \
  -d '{"status": "known"}'
```

### Docker

```bash
docker-compose up -d
```

## Configuration

Edit `config.yaml` to configure:

- **AI provider**: Default provider and model
- **Heartbeat**: Schedule, timezone, notification channels
- **Learning**: Difficulty level (A1-B2), words per topic

Edit `.env` for API keys and secrets.

## AI Providers

| Provider | Setup | Notes |
|----------|-------|-------|
| Claude | `ANTHROPIC_API_KEY` | Default, high quality |
| GPT | `OPENAI_API_KEY` | GPT-4o support |
| Gemini | `GOOGLE_API_KEY` | Fast, generous free tier |
| Kimi | `KIMI_API_KEY` | Good for Chinese content |
| DeepSeek | `DEEPSEEK_API_KEY` | Cost-effective |
| Claude CLI | No key needed | Uses local Claude Code binary |

## Project Structure

```
src/
├── ai/             # AI provider abstraction (6 providers + factory)
├── core/           # Business logic (engine, memory, marker, topic gen)
├── storage/        # SQLite via SQLAlchemy (models, repository, migrations)
├── api/            # FastAPI server + routes
├── heartbeat/      # Scheduled topic generation + dispatch
├── notifications/  # Discord bot + WhatsApp via Twilio
└── cli/            # Rich-based interactive terminal
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=src

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## License

MIT
