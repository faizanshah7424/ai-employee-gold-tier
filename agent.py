"""
Agent - Gold Tier Implementation

Lifecycle:
Inbox → Needs_Action → Plans → Pending_Approval → Approved → Done

Gold Features:
- Memory Manager Integration
- Decision Tracking
- Ralph Wiggum Loop for autonomous retry
- Retry + Failure handling with /Failed folder
- Idempotent execution (no duplicate processing)
"""
from pathlib import Path
from datetime import datetime
from skills import get_skill
from memory_manager import save_task, save_decision, get_task_decisions
from ralph_wiggum import run_ralph_loop
from retry_handler import move_to_failed, with_retry

VAULT = Path("AI_Employee_Vault")

# Folders
NEEDS_ACTION = VAULT / "Needs_Action"
PLANS = VAULT / "Plans"
PENDING_APPROVAL = VAULT / "Pending_Approval"
APPROVED = VAULT / "Approved"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"
FAILED = VAULT / "Failed"


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
    for folder in [NEEDS_ACTION, PLANS, PENDING_APPROVAL, APPROVED, DONE, LOGS, FAILED]:
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
        # Cross-device or locked - copy and delete
        try:
            safe_write(dest, safe_read(file_path))
            file_path.unlink()
            print(f"[Agent] Copied to Done: {new_name}")
        except Exception as e2:
            print(f"[Agent] Error moving to Done: {e2}")


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
    This is the actual work function
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

    content = safe_read(task_file)

    # GOLD: Store raw task in memory
    save_task(task_file.name, content)

    # Check memory for past decisions
    past = get_task_decisions(task_file.name)

    # =========================
    # SKILL 1: CREATE PLAN
    # =========================
    plan_skill = get_skill("create_plan")
    plan_result = plan_skill.execute(content, str(task_file))

    if plan_result["status"] != "success":
        raise Exception(f"Plan creation failed: {plan_result.get('message', 'Unknown')}")

    plan_file = Path(plan_result["plan_file"])
    plan_content = safe_read(plan_file)

    # =========================
    # SKILL 2: ANALYZE APPROVAL
    # =========================
    analyze = get_skill("analyze_for_approval")
    approval_info = analyze.execute(content, plan_content)

    requires_approval = approval_info.get("requires_approval", True)
    action_type = approval_info.get("action_type", "general")

    # =========================
    # DECISION MEMORY (GOLD)
    # =========================
    save_decision(
        task_file.name,
        "approval_check",
        f"requires_approval={requires_approval}"
    )

    # =========================
    # APPROVAL FLOW
    # =========================
    if requires_approval:
        approval_skill = get_skill("create_approval_request")

        result = approval_skill.execute(
            str(task_file),
            plan_content,
            approval_info.get("reason", "Approval required"),
            action_type
        )

        if result["status"] == "success":
            print(f"[Agent] Waiting for approval")

            log_action(
                "task_pending",
                f"{task_file.name} waiting for approval",
                "pending_approval"
            )

            # GOLD: Save decision
            save_decision(task_file.name, "status", "pending_approval")
    else:
        execute_direct_action(task_file, plan_content, action_type)

        log_action(
            "task_complete",
            f"{task_file.name} executed directly",
            "completed"
        )

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
