# AI Employee - Silver Tier Implementation

Complete implementation of Silver Tier requirements from the "Personal AI Employee Hackathon 0: Building Autonomous FTEs in 2026".

## Silver Tier Requirements - COMPLETION STATUS

| # | Requirement | Status | Implementation |
|---|-------------|--------|----------------|
| 1 | All Bronze requirements | ✅ | Complete |
| 2 | Two or more Watcher scripts | ✅ | File System + Gmail Watchers |
| 3 | Automatically Post on LinkedIn | ✅ | LinkedIn MCP Server |
| 4 | Claude reasoning loop with Plan.md | ✅ | Agent Skills create structured plans |
| 5 | One working MCP server | ✅ | Main MCP + LinkedIn MCP |
| 6 | Human-in-the-loop approval | ✅ | Pending_Approval workflow |
| 7 | Basic scheduling via cron/Task Scheduler | ✅ | Windows Task Scheduler integration |
| 8 | All AI as Agent Skills | ✅ | Modular skills architecture |

**COMPLETION: 8/8 (100%)**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WATCHERS (Perception)                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  File Watcher   │  Gmail Watcher  │      MCP Server API         │
└────────┬────────┴────────┬────────┴─────────┬───────────────────┘
         │                 │                  │
         └─────────────────┴──────────────────┘
                          │
                          ▼
                    /Inbox/
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                                 │
│  - Moves Inbox → Needs_Action                                   │
│  - Runs every 30 seconds (or via Task Scheduler)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT SKILLS (Reasoning)                     │
├──────────────────┬─────────────────┬────────────────────────────┤
│  CreatePlanSkill │ AnalyzeApproval │ CreateApprovalRequest      │
│  UpdateDashboard │ ExecuteAction   │ (modular architecture)     │
└──────────────────┴─────────────────┴────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ACTION LAYER                                 │
├──────────────────┬─────────────────┬────────────────────────────┤
│  MCP Server      │  LinkedIn MCP   │    Approval Handler        │
│  (port 5000)     │  (port 5001)    │    (Pending → Done)        │
└──────────────────┴─────────────────┴────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.13 or higher
- OpenRouter API key (or other OpenAI-compatible API)
- Gmail API credentials (for Gmail watcher)
- LinkedIn API credentials (for LinkedIn posting - optional)

### Setup

1. **Clone/Download** this repository

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment** (`.env` file):
   ```
   OPENAI_API_KEY=your_openrouter_key_here
   LINKEDIN_ACCESS_TOKEN=your_linkedin_token_here
   ```

5. **Install scheduled task** (optional):
   ```bash
   python scheduler.py install
   ```

---

## Usage

### Starting the System

**Option 1: Manual Start**
```bash
# Terminal 1: Start Orchestrator
python orchestrator.py

# Terminal 2: Start MCP Server
python mcp_server.py

# Terminal 3: Start LinkedIn MCP Server
python linkedin_mcp_server.py

# Terminal 4: Start File Watcher (optional)
python filesystem_watcher.py

# Terminal 5: Start Gmail Watcher (optional)
python gmail_watcher.py
```

**Option 2: Scheduled Task (Windows)**
```bash
# Install scheduled task (runs on login + every 30 seconds)
python scheduler.py install

# Check status
python scheduler.py status

# Remove scheduled task
python scheduler.py remove
```

### Agent Skills

The AI functionality is implemented as modular skills:

```python
from skills import get_skill, list_skills

# List all available skills
skills = list_skills()
for skill in skills:
    print(f"{skill['name']}: {skill['description']}")

# Use a skill
create_plan = get_skill("create_plan")
result = create_plan.execute(task_content="Analyze this document...")
```

**Available Skills:**
- `create_plan` - Create structured action plans
- `analyze_for_approval` - Determine if approval is needed
- `create_approval_request` - Create approval request files
- `update_dashboard` - Update Dashboard.md

### MCP Server Endpoints

**Main MCP Server (port 5000):**
```bash
# Create task via API
curl -X POST http://localhost:5000/create-task \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Task", "content": "Analyze this..."}'

# Get system status
curl http://localhost:5000/status
```

**LinkedIn MCP Server (port 5001):**
```bash
# Create LinkedIn post (requires approval)
curl -X POST http://localhost:5001/create-post \
  -H "Content-Type: application/json" \
  -d '{"text": "Excited to announce our new product!", "title": "Product Launch"}'

# Schedule LinkedIn post
curl -X POST http://localhost:5001/schedule-post \
  -H "Content-Type: application/json" \
  -d '{"text": "Post content", "scheduled_time": "2026-01-15T09:00:00"}'

# Get LinkedIn status
curl http://localhost:5001/status
```

---

## Silver Tier Features

### 1. Multiple Watchers ✅

**File System Watcher:**
- Monitors `drop_folder/` for new files
- Creates action files in `/Inbox`
- Supports any file type

**Gmail Watcher:**
- Monitors Gmail for unread, important emails
- AI filters spam vs important emails
- Creates action files in `/Inbox`
- Runs every 120 seconds

### 2. LinkedIn Auto-Posting ✅

**Features:**
- Create post drafts via API
- Human approval required before posting (security)
- Schedule posts for later
- Track post history in Logs

**Workflow:**
1. API receives post request
2. Creates approval file in `Pending_Approval/`
3. User reviews and moves to `Approved/`
4. Orchestrator executes post via LinkedIn API
5. Logs result

### 3. Agent Skills Architecture ✅

All AI functionality implemented as modular skills:
- Easy to extend with new skills
- Clean separation of concerns
- Testable independently
- Follows hackathon document requirements

### 4. Task Scheduler Integration ✅

**Windows Task Scheduler:**
- Installs as system task
- Starts on login (1 minute delay)
- Runs every 30 seconds
- Background execution

**Linux/Mac (cron):**
```bash
python scheduler.py cron
# Copy cron entry to crontab
```

### 5. Human-in-the-Loop Approval ✅

**Approval Workflow:**
```
Task → Plan Created → Approval Analysis
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
        Approval Required             No Approval Needed
              ↓                               ↓
    Pending_Approval/                  Execute Directly
              ↓                               ↓
    User moves to Approved/            Move to Done/
              ↓
    Orchestrator executes
              ↓
    Move to Done/
```

---

## Folder Structure

```
ai-employee-silver/
├── # Core System
├── orchestrator.py          # Main coordinator
├── agent.py                 # Task processor (uses skills)
├── qwen_agent.py           # AI interface
├── approval_handler.py      # Approval execution
│
├── # Watchers
├── filesystem_watcher.py    # File monitor
├── gmail_watcher.py         # Gmail monitor
│
├── # MCP Servers
├── mcp_server.py            # Main API server
├── linkedin_mcp_server.py   # LinkedIn integration
│
├── # Agent Skills
├── skills/
│   ├── __init__.py         # Skill registry
│   └── (modular skills)
│
├── # Scheduling
├── scheduler.py             # Task Scheduler integration
│
├── # Configuration
├── .env                     # API keys
├── .gitignore               # Git ignore rules
├── requirements.txt         # Dependencies
│
├── # Documentation
├── README.md                # This file
├── Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md
│
├── # Runtime
├── drop_folder/             # Drop files here
├── venv/                    # Virtual environment
│
└── AI_Employee_Vault/       # Obsidian vault
    ├── Dashboard.md
    ├── Company_Handbook.md
    ├── Business_Goals.md
    ├── Inbox/
    ├── Needs_Action/
    ├── Plans/
    ├── Pending_Approval/
    ├── Approved/
    ├── Rejected/
    ├── Done/
    ├── Logs/
    └── Briefings/
```

---

## Testing

### Test Agent Skills
```bash
python -m skills
```

### Test MCP Servers
```bash
# Start servers
python mcp_server.py
python linkedin_mcp_server.py

# Test endpoints (in another terminal)
curl http://localhost:5000/status
curl http://localhost:5001/status
```

### Test Scheduler
```bash
python scheduler.py status
```

### Full System Test
```bash
# 1. Start all components
python orchestrator.py &
python mcp_server.py &
python linkedin_mcp_server.py &

# 2. Drop a test file
echo "Test task" > drop_folder/test.txt

# 3. Watch it process through the system
# Check AI_Employee_Vault/Plans/ for created plan
# Check AI_Employee_Vault/Pending_Approval/ for approval request
```

---

## Compliance Checklist

### Silver Tier Requirements

- [x] **All Bronze requirements** - Complete
- [x] **Two or more Watcher scripts** - File System + Gmail
- [x] **Automatically Post on LinkedIn** - LinkedIn MCP Server implemented
- [x] **Claude reasoning loop with Plan.md** - Agent Skills create structured plans
- [x] **One working MCP server** - Main MCP + LinkedIn MCP
- [x] **Human-in-the-loop approval** - Pending_Approval workflow
- [x] **Basic scheduling** - Windows Task Scheduler + cron support
- [x] **All AI as Agent Skills** - Modular skills architecture

### Documentation

- [x] README with setup instructions
- [x] Architecture overview
- [x] API endpoint documentation
- [x] Usage examples
- [x] Compliance checklist

---

## Security Notes

**Credentials:**
- Never commit `.env` file
- Store LinkedIn access token securely
- Gmail credentials in `credentials.json` (not committed)

**Approval Workflow:**
- All LinkedIn posts require human approval
- No automatic external actions without approval
- Audit trail in Logs/

---

## Troubleshooting

**Orchestrator not processing tasks:**
- Check if running: `python scheduler.py status`
- Check Logs/YYYY-MM-DD.md for errors
- Ensure API key is configured in `.env`

**MCP Server not responding:**
- Check if port 5000/5001 is in use
- Verify Flask is installed: `pip show flask`

**Scheduled task not running:**
- Open Task Scheduler
- Find "AI_Employee_Orchestrator"
- Check "Last Run Result"
- Right-click → Run to test manually

---

## Version

AI Employee v0.2 - Silver Level (100% Complete)

---

*Implementation follows the hackathon document exactly.*
*All Silver Tier requirements fulfilled.*
