# AI Agent - Intelligent Automation Platform

A comprehensive AI-powered automation platform that combines natural language processing, document analysis, log analysis, calendar management, and GitHub PR review capabilities using Claude AI (Anthropic) and LangChain.

## 🚀 Overview

This AI-assistant is designed to facilitate efficient machine learning model training (RAG-based, storing issues and resolutions in a local vector database), automate pull request reviews with detailed comments on code quality and optimization, manage Gmail calendar, compose and send/delete mail with voice-controlled instructions, and summarize logs/documents/reports.

It uses **Claude AI** (Anthropic's state-of-the-art LLM) for fast, reliable, and intelligent responses. Python (as the backend) wrapped in FastAPI and React as the Frontend.

## 👁️ Preview
<img width="1050" height="703" alt="image" src="https://github.com/user-attachments/assets/95ee41c5-5a9d-4bd0-a1f9-bf4b6cccee42" />

## Features

### 🤖 AI Chat Agent
- Natural language interface powered by Claude AI (Anthropic)
- Context-aware conversations with superior reasoning
- Mathematical computation support
- Document Q&A capabilities
- Faster response times compared to local LLMs

### 📄 Document Analysis
- Upload and analyze PDF and text documents
- AI-powered document summarization
- Question-answering on uploaded documents

### 📊 RAG-based Log Analyzer
- Upload and index log files
- Semantic search across logs using FAISS vector store
- Natural language queries for log analysis
- Support for multiple log files with consolidated indexing

### 📅 Google Calendar Integration
- OAuth 2.0 authentication
- Create, view, and delete calendar events
- Schedule meetings with Google Meet links
- Retrieve events by date
- Support for attendees and locations

### 📧 Gmail Integration
- Read and summarize emails
- Mark emails as read/unread
- AI-powered email summarization

### 🔍 GitHub PR Review
- Automated pull request review
- Code quality analysis
- Vulnerability detection
- Best practices suggestions
- AI-generated review comments

### 🧠 RAG based Training & Knowledge Base
- Save issue-resolution pairs
- RAG based engine selects three most relevant solutions from the local saved resolution history, before sending to the LLM for final verdict.
- Training history management

## Architecture

```
AI-python/
├── main_fastapi.py           # Main FastAPI backend server
├── math_ai_agent_doc.py       # LLaMA 3 agent with tool support
├── rag_log_analyzer.py        # RAG-based log analysis
├── training_store.py          # Issue resolution training store
├── pr_review.py               # GitHub PR review automation
├── gmail_auth.py              # Gmail OAuth authentication
├── ai-agent-ui/               # React frontend
├── logs/                      # Log files directory
├── embeddings/                # FAISS vector store
├── uploaded_docs/             # Uploaded documents storage
└── credentials_*.json         # OAuth credentials
```

## Prerequisites

### System Requirements
- Python 3.10+
- Node.js 16+ (for frontend)
- Claude CLI (Claude Code) - Command-line interface for Claude AI

### Claude CLI Setup
This application now uses the **Claude CLI** instead of the Claude API for better integration and ease of use.

1. **Install Claude CLI:**
   ```bash
   # Using npm (recommended)
   npm install -g @anthropic-ai/claude-code

   # Verify installation
   claude --version
   ```

2. **Authenticate with Claude:**
   ```bash
   # Sign in to Claude CLI
   claude auth login

   # Test the connection
   claude chat -m "Hello, Claude!"
   ```

3. **Important Note:**
   - If running inside a Claude Code session, you'll need to unset the `CLAUDECODE` environment variable when starting your backend
   - The backend will automatically handle this in most cases

**Why Claude CLI instead of local LLMs or API?**
- **10-100x faster** than local Ollama/LLaMA
- **No GPU required** - runs entirely in the cloud
- **Superior reasoning** and code understanding
- **More reliable** responses with better formatting
- **No API key management** - authentication handled by CLI
- **Lower resource usage** on your machine

## Installation

### Quick Setup

Use the automated setup script:
```bash
./setup.sh
```

Or follow manual installation:

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/sandeepknd/AI-agents.git
cd AI-agents
```

2. Install Claude CLI (if not already installed):
```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example file (if it exists)
cp .env.example .env 2>/dev/null || touch .env

# Edit .env and add your tokens:
# GITHUB_TOKEN=your_github_token_here (required for PR review)
# HF_TOKEN=your_huggingface_token (optional, for better rate limits)
#
# NOTE: ANTHROPIC_API_KEY is NO LONGER NEEDED - we use Claude CLI instead
```

5. Configure Google OAuth:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project and enable Google Calendar API and Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials and save as:
     - `credentials_calendar.json` (for Calendar)
     - `credentials_per_gmail.json` (for Gmail)

### Frontend Setup

```bash
cd ai-agent-ui
npm install
```

## Running the Application

### Start Backend Server

```bash
# From the root directory
# If running OUTSIDE Claude Code session:
uvicorn main_fastapi:app --reload --host 0.0.0.0 --port 8000

# If running INSIDE Claude Code session (unset CLAUDECODE variable):
unset CLAUDECODE && uvicorn main_fastapi:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Note:** The first request may take a few seconds as the Claude CLI initializes.

### Start Frontend

```bash
# From ai-agent-ui directory
cd ai-agent-ui
npm start
```

The UI will be available at: http://localhost:3000

## API Endpoints

### Chat & AI Agent
- `POST /ask` - Send queries to the AI agent
  ```json
  {
    "query": "What is the derivative of x^2?"
  }
  ```

### Document Management
- `POST /upload` - Upload and analyze documents
- `POST /upload-log` - Upload log files for indexing
- `POST /analyze-log` - Query log files

### Calendar Operations
- `GET /authorize-calendar` - Start OAuth flow
- `GET /oauth2callback` - OAuth callback
- `GET /get-events` - Get upcoming events
- `POST /create-event` - Create calendar event
- `GET /get-events-by-date?date=YYYY-MM-DD` - Get events for specific date
- `POST /schedule-meeting` - Schedule meeting with Google Meet
  ```json
  {
    "title": "Team Standup",
    "start_time": "2024-03-15T10:00:00",
    "end_time": "2024-03-15T11:00:00",
    "description": "Daily standup meeting",
    "attendees": ["user@example.com"],
    "create_meet_link": true
  }
  ```
- `DELETE /delete-event?event_id=xxx` - Delete event

### Training & Knowledge Base
- `POST /train-model` - Save issue-resolution pair
  ```json
  {
    "issue": "Server not responding",
    "resolution": "Restart the service using systemctl restart app"
  }
  ```
- `POST /suggest-resolution` - Get AI-powered resolution suggestions
- `GET /get-training-history` - View training history
- `DELETE /clear-training-history` - Clear training data

### GitHub PR Review
- `POST /webhook` - GitHub webhook for PR events
- `POST /comment` - Post comment on PR
  ```json
  {
    "pr_url": "https://github.com/user/repo/pull/123",
    "comment": "LGTM! Great work on this feature."
  }
  ```
- `POST /generate-comment` - Generate AI review comment
  ```json
  {
    "pr_url": "https://github.com/user/repo/pull/123"
  }
  ```

## Usage Examples

### Chat with AI Agent
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 15 factorial?"}'
```

### Upload and Analyze Log
```bash
curl -X POST http://localhost:8000/upload-log \
  -F "file=@application.log"

curl -X POST http://localhost:8000/analyze-log \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all error messages"}'
```

### Schedule a Meeting
```bash
curl -X POST http://localhost:8000/schedule-meeting \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Project Review",
    "start_time": "2024-03-20T14:00:00",
    "end_time": "2024-03-20T15:00:00",
    "attendees": ["team@example.com"],
    "create_meet_link": true
  }'
```

### Generate PR Review
```bash
curl -X POST http://localhost:8000/generate-comment \
  -H "Content-Type: application/json" \
  -d '{"pr_url": "https://github.com/owner/repo/pull/42"}'
```

## Technology Stack

### Backend
- **FastAPI** - Modern web framework for APIs
- **LangChain** - LLM orchestration framework
- **Claude CLI (Anthropic)** - State-of-the-art LLM via command-line interface
- **FAISS** - Vector similarity search
- **Sentence Transformers** - Text embeddings
- **Google API Client** - Calendar and Gmail integration

### Frontend
- **React 19** - UI framework
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **React Icons** - Icon library

### AI/ML
- **Claude 3.5 Sonnet** - Latest Claude model for chat and reasoning
- **all-MiniLM-L6-v2** - HuggingFace embedding model for RAG
- **sentence-transformers** - Sentence similarity model

## Configuration

### Environment Variables
```bash
# .env file configuration
GITHUB_TOKEN=your_github_personal_access_token  # Required for PR review
HF_TOKEN=your_huggingface_token  # Optional, for higher rate limits

# NOTE: ANTHROPIC_API_KEY is NO LONGER needed
# Authentication is handled by Claude CLI (claude auth login)
```

### Calendar OAuth Scopes
The application requests the following Google Calendar scopes:
- `https://www.googleapis.com/auth/calendar`

### Gmail OAuth Scopes
For Gmail integration:
- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/gmail.readonly`

## Troubleshooting

### Claude CLI Issues

**Test Claude CLI connection:**
```bash
# Check if Claude CLI is installed
claude --version

# Test basic functionality
claude chat -m "Hello, Claude!"

# Check authentication status
claude auth status
```

### Common Errors

**"Claude CLI command 'claude' not found"**
```bash
# Install Claude CLI
npm install -g @anthropic-ai/claude-code

# Check if it's in PATH
which claude

# If not in PATH, add to your shell profile (~/.bashrc or ~/.zshrc):
export PATH="$PATH:$HOME/.npm-global/bin"
```

**"Cannot be launched inside another Claude Code session"**
```bash
# When starting the backend, unset the environment variable:
unset CLAUDECODE && uvicorn main_fastapi:app --reload --host 0.0.0.0 --port 8000
```

**"Authentication failed" or "Not logged in"**
```bash
# Re-authenticate with Claude CLI
claude auth logout
claude auth login
```

**"Timeout" or "Slow responses"**
- First request may take longer (5-10 seconds) as CLI initializes
- Subsequent requests should be faster (1-3 seconds)
- Check your internet connection

### Import Errors
If you encounter LangChain import errors, ensure you have the correct packages:
```bash
pip install --upgrade langchain langchain-community langchain-text-splitters
```

### Testing the Integration
Run the test script to verify Claude CLI integration:
```bash
# From the project root
python test_claude_cli.py
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

## Development

### Running Tests
```bash
# Frontend tests
cd ai-agent-ui
npm test

# Backend tests (if implemented)
pytest
```

### Code Style
The project follows PEP 8 for Python and Prettier for JavaScript/React.

## Security Considerations

1. **Credentials**: Never commit `credentials_*.json`, `token.json`, or `.env` files to version control
2. **OAuth Tokens**: Tokens are stored locally in `token.json` and `token_mail.pickle`
3. **GitHub Token**: Store in environment variable or `.env` file
4. **Claude Authentication**: Managed by Claude CLI - credentials stored in `~/.claude/`
5. **CORS**: Frontend is restricted to `http://localhost:3000` in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Specify your license here]

## Acknowledgments

- Anthropic for Claude AI - the most capable AI assistant
- LangChain for the excellent LLM framework
- FastAPI for the modern Python web framework
- React community for the frontend ecosystem

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

Built with ❤️ using Claude AI, LangChain, and FastAPI
