"""
Agent - Platinum Tier Implementation

Multi-Agent System:
- PlannerAgent: Creates detailed action plans
- ReviewerAgent: Intelligent decision-making (approval_required, execute_directly, reject)
- ExecutorAgent: Executes approved actions

Lifecycle:
Inbox → Needs_Action → Plans → Pending_Approval → Approved → Done

Platinum Features:
- Multi-agent architecture
- Intelligent decision-making
- Memory Manager Integration
- Ralph Wiggum Loop for autonomous retry
- Retry + Failure handling with /Failed folder
- Idempotent execution (no duplicate processing)
"""
from pathlib import Path
from datetime import datetime
from skills import get_skill
from memory_manager import save_task, save_decision, get_task_decisions
from ralph_wiggum import run_ralph_loop
from retry_handler import move_to_failed
from multi_agent import run_multi_agent, ReviewerAgent

VAULT = Path("AI_Employee_Vault")

# Folders
NEEDS_ACTION = VAULT / "Needs_Action"
PLANS = VAULT / "Plans"
PENDING_APPROVAL = VAULT / "Pending_Approval"
APPROVED = VAULT / "Approved"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"
FAILED = VAULT / "Failed"
REJECTED = VAULT / "Rejected"


# =========================
# SAFE FILE OPERATIONS
# =========================

def safe_read(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def safe_write(file_path: Path, content: str):
    file_path.write_text(content, encoding="utf-8")


# =========================
# SETUP
# =========================

def ensure_folders():
    for folder in [NEEDS_ACTION, PLANS, PENDING_APPROVAL, APPROVED, DONE, LOGS, FAILED, REJECTED]:
        folder.mkdir(exist_ok=True)


# =========================
# LOGGING
# =========================

def log_action(action_type: str, details: str, status: str = "pending"):
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS / f"{today}.md"

    timestamp = datetime.now().isoformat()

    entry = f"""
## [{timestamp}] {action_type}
- **Status:** {status}
- **Details:** {details}

"""

    if log_file.exists():
        content = safe_read(log_file)
    else:
        content = f"# Activity Log - {today}\n\n"

    content += entry
    safe_write(log_file, content)


# =========================
# FILE MOVEMENT
# =========================

def move_to_done(file_path: Path, prefix: str = ""):
    """Move file to Done folder with timestamp"""
    if not file_path.exists():
        return  # Already moved

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{prefix}{file_path.stem}_DONE_{timestamp}.md"
    dest = DONE / new_name

    try:
        file_path.rename(dest)
        print(f"[Agent] Moved to Done: {new_name}")
    except Exception as e:
        try:
            safe_write(dest, safe_read(file_path))
            file_path.unlink()
            print(f"[Agent] Copied to Done: {new_name}")
        except Exception as e2:
            print(f"[Agent] Error moving to Done: {e2}")


def move_to_rejected(task_file: Path, reason: str):
    """Move task to Rejected folder with reason"""
    REJECTED.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rejected_file = REJECTED / f"REJECTED_{task_file.stem}_{timestamp}.md"

    content = f"""---
type: rejected
original_file: {task_file.name}
reason: {reason}
timestamp: {datetime.now().isoformat()}
status: rejected
---

# Rejected Task

**Original File:** {task_file.name}
**Reason:** {reason}
**Rejected At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Original Content

"""

    try:
        content += safe_read(task_file)
    except Exception:
        content += "Unable to read original content."

    content += f"""

---
*Rejected by ReviewerAgent*
"""

    rejected_file.write_text(content, encoding="utf-8")
    task_file.unlink()

    print(f"[Agent] Moved to Rejected: {rejected_file.name}")
    log_action("task_rejected", f"{task_file.name}: {reason}", "rejected")


# =========================
# APPROVAL CREATION
# =========================

def create_approval_request(task_file: Path, plan_content: str, reason: str, action_type: str) -> bool:
    """Create approval request file in Pending_Approval"""
    try:
        timestamp = datetime.now()
        approval_file = PENDING_APPROVAL / f"APPROVAL_{task_file.stem}_{timestamp.strftime('%Y%m%d%H%M%S')}.md"

        content = f"""---
type: approval_request
action_type: {action_type}
source_task: {task_file.name}
created: {timestamp.isoformat()}
expires: {timestamp.replace(day=timestamp.day + 1).isoformat()}
status: pending
reason: {reason}
---

# Approval Required

**Action Type:** {action_type}
**Source Task:** {task_file.name}
**Created:** {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
**Expires:** {timestamp.replace(day=timestamp.day + 1).strftime("%Y-%m-%d %H:%M:%S")}

## Reason for Approval
{reason}

## Proposed Plan
{plan_content}

---

## Instructions

**To Approve:** Move this file to the `/Approved` folder
**To Reject:** Move this file to the `/Rejected` folder

*Once approved, the orchestrator will execute the proposed actions.*
"""

        approval_file.write_text(content, encoding="utf-8")
        print(f"[Agent] Approval request created: {approval_file.name}")
        log_action("approval_request", f"Created for {task_file.name}", "pending")
        return True

    except Exception as e:
        print(f"[Agent] Error creating approval request: {e}")
        log_action("error", f"Failed to create approval: {e}", "error")
        return False


# =========================
# DIRECT EXECUTION
# =========================

def execute_direct_action(task_file: Path, plan_content: str, action_type: str):
    """Execute action directly without approval (low-risk tasks)"""
    print(f"[Agent] Executing: {task_file.name}")

    # Save to memory (Gold Feature)
    save_task(task_file.name, plan_content)
    save_decision(task_file.name, "executed_directly", action_type)

    log_action(
        f"direct_{action_type}",
        f"Executed without approval: {task_file.name}",
        "completed"
    )

    move_to_done(task_file, "TASK_")

    # Move related plans
    for plan in PLANS.glob(f"PLAN_{task_file.stem}*.md"):
        move_to_done(plan, "PLAN_")

    print(f"[Agent] Direct execution completed")


# =========================
# TASK PROCESSING (CORE)
# =========================

def _process_task_internal(task_file: Path) -> bool:
    """
    Internal task processing - called by Ralph Loop
    Uses multi-agent system with ReviewerAgent decision intelligence
    """
    print(f"[Agent] Processing: {task_file.name}")

    # Skip if already has approval request (idempotent)
    approval_exists = any(
        task_file.stem in f.name
        for f in PENDING_APPROVAL.glob("*.md")
    )
    if approval_exists:
        print(f"[Agent] Skipping - already has approval request")
        return True

    # Check if already in Done (idempotent)
    done_exists = any(
        task_file.stem in f.name
        for f in DONE.glob("*.md")
    )
    if done_exists:
        print(f"[Agent] Skipping - already completed")
        return True

    # Read task content
    try:
        content = safe_read(task_file)
    except Exception as e:
        print(f"[Agent] Error reading task: {e}")
        return False

    # Check if task is empty or too short
    if len(content.strip()) < 10:
        print(f"[Agent] Task too short, rejecting")
        move_to_rejected(task_file, "Task content too short to process")
        save_decision(task_file.name, "rejected", "content_too_short")
        return True  # Returning True because rejection is a valid outcome

    # GOLD: Store raw task in memory
    save_task(task_file.name, content)

    # Check memory for past decisions
    past = get_task_decisions(task_file.name)

    # =========================
    # MULTI-AGENT SYSTEM
    # =========================
    plan_file, decision = run_multi_agent(task_file)

    plan_content = safe_read(plan_file)

    # Read structured decision output
    reviewer_decision = decision.get("decision", "approval_required")
    reason = decision.get("reason", "Unknown reason")
    confidence = decision.get("confidence", 0.50)
    action_type = decision.get("action_type", "general")

    # Print structured decision for audit visibility
    print(f"\n{'='*60}")
    print(f"[Agent] ReviewerAgent Decision: {reviewer_decision}")
    print(f"[Agent] Reason: {reason}")
    print(f"[Agent] Confidence: {confidence:.2f}")
    print(f"{'='*60}\n")

    # =========================
    # DECISION MEMORY (GOLD)
    # =========================
    save_decision(
        task_file.name,
        "reviewer_decision",
        f"decision={reviewer_decision}, confidence={confidence:.2f}, reason={reason}"
    )

    # =========================
    # LOG DECISION WITH REASON (AUDIT TRAIL)
    # =========================
    log_action(
        "reviewer_decision",
        f"Task: {task_file.name} | Decision: {reviewer_decision} | Confidence: {confidence:.2f} | Reason: {reason}",
        reviewer_decision
    )

    # =========================
    # HANDLE DECISION
    # =========================
    if reviewer_decision == "approval_required":
        # Create approval request
        success = create_approval_request(task_file, plan_content, reason, action_type)

        if success:
            print(f"[Agent] Waiting for approval")
            save_decision(task_file.name, "status", "pending_approval")
        else:
            raise Exception("Failed to create approval request")

    elif reviewer_decision == "execute_directly":
        # Execute directly without approval
        execute_direct_action(task_file, plan_content, action_type)

    elif reviewer_decision == "reject":
        # Reject the task
        move_to_rejected(task_file, reason)
        save_decision(task_file.name, "status", "rejected")

    # =========================
    # SKILL 3: DASHBOARD
    # =========================
    dashboard = get_skill("update_dashboard")
    dashboard.execute("Task processed", task_file.name)

    return True


def process_task(task_file: Path) -> bool:
    """
    Main task processing with Ralph Wiggum Loop (Gold)
    Keeps retrying until task is complete or max iterations reached
    """
    try:
        success = run_ralph_loop(
            agent_func=_process_task_internal,
            task_file=task_file,
            max_iterations=3
        )

        if not success:
            # Ralph loop exhausted iterations - move to Failed
            move_to_failed(task_file, "Max Ralph Loop iterations reached", "task_processing")
            log_action("task_failed", f"{task_file.name} moved to /Failed", "failed")

        return success

    except Exception as e:
        # Critical error - move to Failed
        print(f"[Agent] Critical error: {e}")
        move_to_failed(task_file, str(e), "task_processing")
        log_action("critical_error", f"{task_file.name}: {str(e)}", "error")
        return False


# =========================
# PROCESS ALL TASKS
# =========================

def process_all_tasks():
    """Process all tasks in Needs_Action with idempotency"""
    ensure_folders()

    tasks = list(NEEDS_ACTION.glob("*.md"))

    if not tasks:
        print("[Agent] No tasks found")
        return 0

    processed = 0
    failed = 0

    for task in tasks:
        if task.name.startswith("META_"):
            continue

        if process_task(task):
            processed += 1
        else:
            failed += 1

    print(f"[Agent] Processed: {processed}, Failed: {failed}")
    return processed


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    ensure_folders()
    count = process_all_tasks()
    print(f"[Agent] Done. {count} tasks processed.")
