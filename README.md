# Tutorial Teacher

An interactive CLI tool that helps developers follow YouTube coding tutorials with AI assistance.

## Features

- Fetches YouTube video transcripts automatically
- Segments tutorials into digestible chunks
- AI-powered Q&A about any part of the tutorial
- Beautiful terminal UI with rich formatting

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/tutorial-teacher.git
cd tutorial-teacher

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .
```

## Setup

1. Copy `.env.example` to `.env`
2. Add your Anthropic API key to `.env`

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
# Start a tutorial session (freeform Q&A mode)
tt https://www.youtube.com/watch?v=VIDEO_ID

# With a GitHub repo for code context
tt https://www.youtube.com/watch?v=VIDEO_ID --repo https://github.com/user/repo

# Step-through mode (navigate segment by segment)
tt https://www.youtube.com/watch?v=VIDEO_ID --mode step
```

## Commands (in freeform mode)

- Type any question to ask about the tutorial
- `/help` - Show available commands
- `/segments` - List all segments
- `/segment <n>` - Jump to segment n
- `/quit` or `/q` - Exit the session

## Requirements

- Python 3.10+
- Anthropic API key
