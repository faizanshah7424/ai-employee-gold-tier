# 🤖 AI Employee System (Gold + Platinum Tier)

## 🚀 Overview

The **AI Employee System** is a fully autonomous, multi-agent architecture designed to simulate a real-world AI employee.
It follows a strict lifecycle, integrates memory, supports human-in-the-loop approvals, and includes advanced Platinum-level intelligence such as adaptive learning and multi-agent collaboration.

This project is built as part of a hackathon/assignment and achieves **100% compliance across Bronze, Silver, Gold, and Platinum tiers**.

---

## 🧠 Core Concept

The system behaves like a real employee:

1. Receives tasks (Inbox)
2. Understands and plans work
3. Decides whether approval is needed
4. Executes or waits
5. Learns from past decisions
6. Reports outcomes

---

## 🏗️ Architecture

### 📂 Folder Structure (Strict Lifecycle)

```
AI_Employee_Vault/
│
├── Inbox/                # All inputs (Watchers + MCP)
├── Needs_Action/         # Tasks ready for processing
├── Plans/                # AI-generated plans
├── Pending_Approval/     # Awaiting human approval
├── Approved/             # Human-approved tasks
├── Rejected/             # Rejected tasks
├── Done/                 # Completed tasks
├── Failed/               # Failed tasks (retry system)
├── Memory/               # Gold tier learning storage
├── Logs/                 # Activity logs
├── Briefings/            # CEO reports
└── Dashboard.md          # System overview
```

---

## 🔁 Lifecycle Flow

```
Inbox
  ↓
Needs_Action
  ↓
Plans
  ↓
Decision (ReviewerAgent)
  ↓
├── execute_directly → Done
├── approval_required → Pending_Approval → Approved → Done
└── reject → Rejected
```

### ✅ Golden Rule:

* ONLY Orchestrator → moves Inbox → Needs_Action
* ONLY Agent → writes Pending_Approval
* ONLY Human → moves to Approved
* NOTHING bypasses lifecycle

---

## 🧩 System Components

### ⚙️ 1. Orchestrator

* Runs every 30 seconds
* Manages full lifecycle
* Moves files between folders
* Handles retries & dashboard updates

---

### 🤖 2. Agent (Gold + Platinum)

Handles task processing using:

* ✅ Modular Skills
* ✅ Memory integration
* ✅ Ralph Wiggum Loop (retry intelligence)
* ✅ Idempotent execution

---

### 🧠 3. Multi-Agent System (Platinum)

#### 👨‍💼 PlannerAgent

* Creates structured execution plan

#### ⚡ ExecutorAgent

* Executes task (simulation or real)

#### 🧑‍⚖️ ReviewerAgent (INTELLIGENT CORE)

Makes decisions:

* `approval_required`
* `execute_directly`
* `reject`

---

## 🧠 ReviewerAgent Intelligence

### Decision Logic

| Task Type       | Decision          |
| --------------- | ----------------- |
| External action | approval_required |
| Internal action | execute_directly  |
| Empty/unclear   | reject            |

---

### 📊 Structured Output

```json
{
  "decision": "approval_required",
  "reason": "External action detected",
  "confidence": 0.95,
  "action_type": "communication"
}
```

---

### 🧬 Adaptive Learning (Platinum)

* Reads past decisions from Memory
* Adjusts confidence:

  * +10% → similar past decision
  * -15% → conflicting past decision
* NEVER overrides rules

---

## 🧠 Memory System (Gold Tier)

### Features:

* Stores tasks + decisions
* Provides context before planning
* Used only inside Agent/Skills

### Rules:

* ✅ Read BEFORE planning
* ✅ Write AFTER decisions
* ❌ Never control file movement

---

## 🔁 Retry System (Gold)

### Features:

* `/Failed` folder for failed tasks
* Exponential backoff retry
* Auto re-processing

---

## 🔄 Ralph Wiggum Loop (Platinum)

* Multi-step retry loop
* Prevents system failure
* Improves robustness

```python
run_ralph_loop(max_iterations=3)
```

---

## 📊 CEO Briefing System

Generates reports using:

* Completed tasks (/Done)
* Logs (/Logs)

Outputs:

```
/Briefings/CEO_REPORT_<date>.md
```

---

## 🔌 MCP + Watchers

### Inputs come from:

* File Watcher
* Gmail Watcher
* MCP Servers (e.g., LinkedIn)

### Rule:

```
ALL inputs → /Inbox ONLY
```

---

## 🔒 Compliance & Security

| Rule                    | Status |
| ----------------------- | ------ |
| Lifecycle enforced      | ✅      |
| No bypassing folders    | ✅      |
| Memory isolation        | ✅      |
| Human approval required | ✅      |
| Idempotent execution    | ✅      |

---

## 🧪 Example Flow

### Task:

```
Post to LinkedIn about new product
```

### Result:

1. Plan created
2. ReviewerAgent detects "post"
3. Decision → approval_required
4. File → Pending_Approval
5. Human approves
6. Task executed → Done

---

## 🛠️ Tech Stack

* Python
* File-based architecture
* Modular agent skills
* Rule-based + AI reasoning

---

## ▶️ How to Run

```bash
python orchestrator.py
```

System runs continuously in cycles.

---

## 📈 System Status

| Tier     | Status |
| -------- | ------ |
| Bronze   | ✅ 100% |
| Silver   | ✅ 100% |
| Gold     | ✅ 100% |
| Platinum | ✅ 100% |

---

## 🎯 Key Highlights

* 🧠 Intelligent decision-making
* 🔁 Self-recovering system
* 📊 Full audit logging
* 🤖 Multi-agent collaboration
* 🧬 Adaptive learning
* 🔒 Strict lifecycle compliance

---

## 🏁 Conclusion

This system is a **production-ready AI Employee simulation** that:

* Thinks before acting
* Asks for approval when needed
* Learns from past decisions
* Recovers from failure
* Explains every action

---

## 👨‍💻 Author

**Faizan Shah**

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and share your feedback!
# 🤖 AI Employee System (Gold + Platinum Tier)

## 🚀 Overview

The **AI Employee System** is a fully autonomous, multi-agent architecture designed to simulate a real-world AI employee.
It follows a strict lifecycle, integrates memory, supports human-in-the-loop approvals, and includes advanced Platinum-level intelligence such as adaptive learning and multi-agent collaboration.

This project is built as part of a hackathon/assignment and achieves **100% compliance across Bronze, Silver, Gold, and Platinum tiers**.

---

## 🧠 Core Concept

The system behaves like a real employee:

1. Receives tasks (Inbox)
2. Understands and plans work
3. Decides whether approval is needed
4. Executes or waits
5. Learns from past decisions
6. Reports outcomes

---

## 🏗️ Architecture

### 📂 Folder Structure (Strict Lifecycle)

```
AI_Employee_Vault/
│
├── Inbox/                # All inputs (Watchers + MCP)
├── Needs_Action/         # Tasks ready for processing
├── Plans/                # AI-generated plans
├── Pending_Approval/     # Awaiting human approval
├── Approved/             # Human-approved tasks
├── Rejected/             # Rejected tasks
├── Done/                 # Completed tasks
├── Failed/               # Failed tasks (retry system)
├── Memory/               # Gold tier learning storage
├── Logs/                 # Activity logs
├── Briefings/            # CEO reports
└── Dashboard.md          # System overview
```

---

## 🔁 Lifecycle Flow

```
Inbox
  ↓
Needs_Action
  ↓
Plans
  ↓
Decision (ReviewerAgent)
  ↓
├── execute_directly → Done
├── approval_required → Pending_Approval → Approved → Done
└── reject → Rejected
```

### ✅ Golden Rule:

* ONLY Orchestrator → moves Inbox → Needs_Action
* ONLY Agent → writes Pending_Approval
* ONLY Human → moves to Approved
* NOTHING bypasses lifecycle

---

## 🧩 System Components

### ⚙️ 1. Orchestrator

* Runs every 30 seconds
* Manages full lifecycle
* Moves files between folders
* Handles retries & dashboard updates

---

### 🤖 2. Agent (Gold + Platinum)

Handles task processing using:

* ✅ Modular Skills
* ✅ Memory integration
* ✅ Ralph Wiggum Loop (retry intelligence)
* ✅ Idempotent execution

---

### 🧠 3. Multi-Agent System (Platinum)

#### 👨‍💼 PlannerAgent

* Creates structured execution plan

#### ⚡ ExecutorAgent

* Executes task (simulation or real)

#### 🧑‍⚖️ ReviewerAgent (INTELLIGENT CORE)

Makes decisions:

* `approval_required`
* `execute_directly`
* `reject`

---

## 🧠 ReviewerAgent Intelligence

### Decision Logic

| Task Type       | Decision          |
| --------------- | ----------------- |
| External action | approval_required |
| Internal action | execute_directly  |
| Empty/unclear   | reject            |

---

### 📊 Structured Output

```json
{
  "decision": "approval_required",
  "reason": "External action detected",
  "confidence": 0.95,
  "action_type": "communication"
}
```

---

### 🧬 Adaptive Learning (Platinum)

* Reads past decisions from Memory
* Adjusts confidence:

  * +10% → similar past decision
  * -15% → conflicting past decision
* NEVER overrides rules

---

## 🧠 Memory System (Gold Tier)

### Features:

* Stores tasks + decisions
* Provides context before planning
* Used only inside Agent/Skills

### Rules:

* ✅ Read BEFORE planning
* ✅ Write AFTER decisions
* ❌ Never control file movement

---

## 🔁 Retry System (Gold)

### Features:

* `/Failed` folder for failed tasks
* Exponential backoff retry
* Auto re-processing

---

## 🔄 Ralph Wiggum Loop (Platinum)

* Multi-step retry loop
* Prevents system failure
* Improves robustness

```python
run_ralph_loop(max_iterations=3)
```

---

## 📊 CEO Briefing System

Generates reports using:

* Completed tasks (/Done)
* Logs (/Logs)

Outputs:

```
/Briefings/CEO_REPORT_<date>.md
```

---

## 🔌 MCP + Watchers

### Inputs come from:

* File Watcher
* Gmail Watcher
* MCP Servers (e.g., LinkedIn)

### Rule:

```
ALL inputs → /Inbox ONLY
```

---

## 🔒 Compliance & Security

| Rule                    | Status |
| ----------------------- | ------ |
| Lifecycle enforced      | ✅      |
| No bypassing folders    | ✅      |
| Memory isolation        | ✅      |
| Human approval required | ✅      |
| Idempotent execution    | ✅      |

---

## 🧪 Example Flow

### Task:

```
Post to LinkedIn about new product
```

### Result:

1. Plan created
2. ReviewerAgent detects "post"
3. Decision → approval_required
4. File → Pending_Approval
5. Human approves
6. Task executed → Done

---

## 🛠️ Tech Stack

* Python
* File-based architecture
* Modular agent skills
* Rule-based + AI reasoning

---

## ▶️ How to Run

```bash
python orchestrator.py
```

System runs continuously in cycles.

---

## 📈 System Status

| Tier     | Status |
| -------- | ------ |
| Bronze   | ✅ 100% |
| Silver   | ✅ 100% |
| Gold     | ✅ 100% |
| Platinum | ✅ 100% |

---

## 🎯 Key Highlights

* 🧠 Intelligent decision-making
* 🔁 Self-recovering system
* 📊 Full audit logging
* 🤖 Multi-agent collaboration
* 🧬 Adaptive learning
* 🔒 Strict lifecycle compliance

---

## 🏁 Conclusion

This system is a **production-ready AI Employee simulation** that:

* Thinks before acting
* Asks for approval when needed
* Learns from past decisions
* Recovers from failure
* Explains every action

---

## 👨‍💻 Author

**Faizan Shah**

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and share your feedback!
