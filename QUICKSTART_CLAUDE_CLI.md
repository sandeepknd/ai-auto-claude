# Quick Start Guide - Claude CLI Integration

## Prerequisites Check

Before starting, verify you have:

```bash
# 1. Python 3.10+
python --version

# 2. Node.js 16+
node --version

# 3. Claude CLI installed
claude --version
```

## Step-by-Step Setup

### 1. Install Claude CLI (if not installed)

```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Authenticate with Claude

```bash
claude auth login
```

Follow the prompts to sign in with your Anthropic account.

### 3. Install Python Dependencies

```bash
cd /home/skundu/automation/AI-python-agent
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
# Create .env file if it doesn't exist
touch .env

# Edit .env and add (if you need PR review functionality):
echo "GITHUB_TOKEN=your_github_token_here" >> .env
```

**Note:** You do NOT need `ANTHROPIC_API_KEY` anymore!

### 5. Configure Google OAuth (Optional)

Only needed if you want Calendar/Gmail features:

- Download OAuth credentials from Google Cloud Console
- Save as `credentials_calendar.json` and `credentials_per_gmail.json`

### 6. Start the Backend

```bash
# If running OUTSIDE Claude Code:
uvicorn main_fastapi:app --reload --host 0.0.0.0 --port 8000

# If running INSIDE Claude Code (like now):
unset CLAUDECODE && uvicorn main_fastapi:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start the Frontend (in a new terminal)

```bash
cd ai-agent-ui
npm install  # First time only
npm start
```

### 8. Test the Application

Open your browser and go to:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Quick Test

### Test Claude CLI Integration

```bash
# Simple test
python test_claude_cli.py
```

### Test via API

```bash
# Test the /ask endpoint
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 5 + 7?"}'
```

Expected response:
```json
{
  "response": "12"
}
```

## Common Commands

```bash
# Start backend (from project root)
uvicorn main_fastapi:app --reload --port 8000

# Start frontend (from ai-agent-ui directory)
npm start

# Test Claude CLI
claude chat -m "Hello"

# Check Claude auth status
claude auth status

# View API documentation
# Open: http://localhost:8000/docs
```

## Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill the process if needed
kill -9 <PID>
```

### Claude CLI errors

```bash
# Re-authenticate
claude auth logout
claude auth login

# Test connection
claude chat -m "test"
```

### "Nested session" error

```bash
# Unset the environment variable
unset CLAUDECODE

# Then start the server
uvicorn main_fastapi:app --reload --port 8000
```

## Next Steps

1. ✅ Backend running on port 8000
2. ✅ Frontend running on port 3000
3. ✅ Claude CLI authenticated
4. 🎉 Start using your AI agent!

Try these features:
- Chat with the AI agent
- Upload and analyze documents
- Schedule calendar events (after OAuth setup)
- Review GitHub PRs
- Train the model with issue-resolution pairs

## Files Structure

```
AI-python-agent/
├── claude_cli_client.py      # NEW - Claude CLI integration
├── math_ai_agent_doc.py       # Uses claude_cli_client
├── rag_log_analyzer.py        # Uses claude_cli_client
├── main_fastapi.py            # FastAPI backend
├── test_claude_cli.py         # Test script
├── requirements.txt           # Python dependencies (no anthropic package)
└── README.md                  # Full documentation
```

## Key Differences from API Version

| Feature | Claude API (Old) | Claude CLI (New) |
|---------|------------------|------------------|
| Installation | `pip install anthropic` | `npm install -g @anthropic-ai/claude-code` |
| Authentication | API key in .env | `claude auth login` |
| No. of dependencies | +1 Python package | 0 Python packages |
| Setup complexity | Medium | Easy |

## Support

If you encounter issues:
1. Check the main README.md
2. Run `python test_claude_cli.py`
3. Check Claude CLI: `claude --version`
4. Verify auth: `claude auth status`

Enjoy your AI-powered automation platform! 🚀
