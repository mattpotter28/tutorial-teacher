# Tutorial Teacher

An interactive CLI tool that helps developers follow YouTube coding tutorials with AI assistance. Stop pausing and rewinding - let AI guide you through step by step.

## Features

- **Transcript Fetching** - Automatically extracts YouTube video transcripts
- **Two Learning Modes**:
  - **Freeform Q&A** - Ask questions about any part of the tutorial
  - **Step-through** - Guided segment-by-segment learning with AI-generated instructions
- **GitHub Integration** - Add a repo URL for code context in AI responses
- **Beautiful Terminal UI** - Rich formatting with streaming responses

## Installation

```bash
# Clone the repo
git clone https://github.com/mattpotter28/tutorial-teacher.git
cd tutorial-teacher

# Create virtual environment (Python 3.10+ required)
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e .
```

## Setup

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-...
```

Get an API key at [console.anthropic.com](https://console.anthropic.com)

## Usage

```bash
# Basic usage - freeform Q&A mode
tt https://www.youtube.com/watch?v=VIDEO_ID

# Step-through mode - guided learning
tt https://www.youtube.com/watch?v=VIDEO_ID --mode step

# With GitHub repo for code context
tt https://www.youtube.com/watch?v=VIDEO_ID --repo https://github.com/user/repo

# Combine both
tt https://www.youtube.com/watch?v=VIDEO_ID --mode step --repo https://github.com/user/repo
```

## Modes

### Freeform Mode (default)

Ask any question about the tutorial. The AI has access to the full transcript.

**Commands:**
| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/segments` | List all tutorial segments |
| `/segment <n>` | Show segment n details |
| `/clear` | Clear conversation history |
| `/quit`, `/q` | Exit |

Just type a question to ask about the tutorial.

### Step-through Mode (`--mode step`)

Navigate the tutorial segment by segment. The AI breaks down each section into clear, actionable steps.

**Commands:**
| Command | Description |
|---------|-------------|
| `/next`, `/n` | Go to next section |
| `/back`, `/b` | Go to previous section |
| `/overview`, `/o` | Show all sections |
| `/jump <n>` | Jump to section n |
| `/raw` | Show raw transcript for current section |
| `/help` | Show commands |
| `/quit`, `/q` | Exit |

Type a question to ask about the current section.

## GitHub Integration

Add `--repo` to include repository code in the AI's context:

```bash
tt https://youtu.be/VIDEO_ID --repo https://github.com/user/repo
```

**Features:**
- Fetches file tree and key source files
- Supports public repos (no token needed)
- Supports private repos with `GITHUB_TOKEN`

**For private repos**, add to `.env`:
```
GITHUB_TOKEN=ghp_...
```

Create a token at [github.com/settings/tokens](https://github.com/settings/tokens) (no special scopes needed for public repos).

## Examples

```bash
# Follow a Go tutorial with its repo
tt "https://www.youtube.com/watch?v=7VLmLOiQ3ck" \
   --repo https://github.com/sikozonpc/ecom-go-api-project \
   --mode step

# Quick Q&A about a Python tutorial
tt "https://youtu.be/dQw4w9WgXcQ"
```

## Requirements

- Python 3.10+
- Anthropic API key
- Internet connection (for YouTube transcripts and GitHub repos)

## License

MIT
