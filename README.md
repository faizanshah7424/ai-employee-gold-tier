# AI Employee - Silver Level

A Personal AI Employee implementation following the **Silver Tier** requirements from the "Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026".

**COMPLETION STATUS: 100% Silver Tier**

## Silver Tier Features

✅ **All Bronze requirements** - Complete foundation
✅ **Two or more Watcher scripts** - File System + Gmail
✅ **Automatically Post on LinkedIn** - LinkedIn MCP Server
✅ **Claude reasoning loop with Plan.md** - Structured plans with checkboxes
✅ **One working MCP server** - Main MCP + LinkedIn MCP
✅ **Human-in-the-loop approval** - Pending_Approval workflow
✅ **Basic scheduling via cron/Task Scheduler** - Windows Task Scheduler
✅ **All AI as Agent Skills** - Modular skills architecture

---

## Architecture

```
Watchers (File, Gmail) → /Inbox → Orchestrator → /Needs_Action
                                                      ↓
                                            Agent Skills (AI)
                                                      ↓
                                    Plans → Approval → Actions (MCP)
```

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `.env`:
```
OPENAI_API_KEY=your_openrouter_key_here
LINKEDIN_ACCESS_TOKEN=your_linkedin_token_here  # Optional
```

### 3. Start the System

**Option A: Manual Start**
```bash
# Terminal 1: Main orchestrator
python orchestrator.py

# Terminal 2: MCP Server (external API)
python mcp_server.py

# Terminal 3: LinkedIn MCP Server
python linkedin_mcp_server.py
```

**Option B: Scheduled Task (Windows)**
```bash
# Install (runs on login + every 30 seconds)
python scheduler.py install

# Check status
python scheduler.py status
```

---

## Usage

### Create Task via API

```bash
curl -X POST http://localhost:5000/create-task ^
  -H "Content-Type: application/json" ^
  -d "{\"title\": \"Test Task\", \"content\": \"Analyze this...\"}"
```

### Create LinkedIn Post

```bash
curl -X POST http://localhost:5001/create-post ^
  -H "Content-Type: application/json" ^
  -d "{\"text\": \"Excited to announce our new product!\", \"title\": \"Product Launch\"}"
```

### Agent Skills

```python
from skills import get_skill

# Use a skill
create_plan = get_skill("create_plan")
result = create_plan.execute(task_content="Your task here...")
```

---

## Documentation

- **Full Documentation:** See `SILVER_TIER_README.md`
- **Hackathon Document:** `Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md`

---

## Folder Structure

```
ai-employee-silver/
├── orchestrator.py          # Main coordinator
├── agent.py                 # Uses Agent Skills
├── skills/                  # Modular AI skills
├── mcp_server.py            # Main API server
├── linkedin_mcp_server.py   # LinkedIn integration
├── scheduler.py             # Task Scheduler
├── filesystem_watcher.py    # File monitor
├── gmail_watcher.py         # Gmail monitor
└── AI_Employee_Vault/       # Obsidian vault
```

---

## Compliance

**Silver Tier: 8/8 requirements (100%)**

See `SILVER_TIER_README.md` for detailed compliance checklist.

---

*AI Employee v0.2 - Silver Level*
*Ready for Hackathon Submission*
