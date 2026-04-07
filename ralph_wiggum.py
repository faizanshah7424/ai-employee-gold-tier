"""
Ralph Wiggum Loop - Gold Tier
Implements autonomous multi-step task completion

Per hackathon document:
"Ralph Wiggum loop for autonomous multi-step task completion"

How it works:
1. Agent processes a task
2. If task not complete (not in /Done), agent loops
3. Loop continues until task reaches /Done or max iterations
4. Stop hook checks completion status
"""
from pathlib import Path
from datetime import datetime
import time

VAULT = Path("AI_Employee_Vault")
DONE = VAULT / "Done"
NEEDS_ACTION = VAULT / "Needs_Action"
LOGS = VAULT / "Logs"


def safe_read(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def safe_write(file_path: Path, content: str):
    file_path.write_text(content, encoding="utf-8")


def is_task_complete(task_stem: str) -> bool:
    """
    Check if a task has been completed (moved to /Done)
    Uses file movement detection (Gold tier completion strategy)
    """
    done_files = list(DONE.glob(f"*{task_stem}*.md"))
    return len(done_files) > 0


def run_ralph_loop(agent_func, task_file: Path, max_iterations: int = 5) -> bool:
    """
    Ralph Wiggum Loop: Keep processing until task is complete

    Args:
        agent_func: Function to call for processing (should return True/False)
        task_file: The task file to process
        max_iterations: Maximum number of loop iterations

    Returns:
        True if task completed successfully, False if failed
    """
    task_stem = task_file.stem
    iteration = 0
    last_error = ""

    print(f"[Ralph Loop] Starting loop for: {task_file.name}")
    print(f"[Ralph Loop] Max iterations: {max_iterations}")

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[Ralph Loop] === Iteration {iteration}/{max_iterations} ===")

        try:
            # Process the task
            success = agent_func(task_file)

            # Check if task is complete (moved to Done)
            if is_task_complete(task_stem):
                print(f"[Ralph Loop] ✅ Task complete after {iteration} iteration(s)")
                log_loop_result(task_file.name, "completed", iteration)
                return True

            if success:
                print(f"[Ralph Loop] Processing successful, checking completion...")
                # Task processed but not yet in Done - might need approval
                # Check if approval was created (waiting for human)
                approval_files = list((VAULT / "Pending_Approval").glob(f"*{task_stem}*.md"))
                if approval_files:
                    print(f"[Ralph Loop] ⏳ Waiting for human approval")
                    log_loop_result(task_file.name, "awaiting_approval", iteration)
                    return True  # Not an error - waiting for human

            else:
                print(f"[Ralph Loop] ❌ Processing failed, retrying...")
                last_error = "Processing returned False"

        except Exception as e:
            last_error = str(e)
            print(f"[Ralph Loop] ❌ Error: {e}")

        # Wait before next iteration
        if iteration < max_iterations:
            print(f"[Ralph Loop] Retrying in 2 seconds...")
            time.sleep(2)

    # Max iterations reached
    print(f"\n[Ralph Loop] ⚠️ Max iterations ({max_iterations}) reached")
    print(f"[Ralph Loop] Last error: {last_error}")

    # Move to Failed
    log_loop_result(task_file.name, "max_iterations_reached", iteration, last_error)
    return False


def log_loop_result(task_name: str, status: str, iterations: int, error: str = ""):
    """Log Ralph Loop results"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS / f"{today}.md"

    timestamp = datetime.now().isoformat()
    entry = f"""
## [{timestamp}] Ralph Loop - {task_name}
- **Status:** {status}
- **Iterations:** {iterations}
- **Error:** {error}

"""

    if log_file.exists():
        content = safe_read(log_file)
    else:
        content = f"# Activity Log - {today}\n\n"

    content += entry
    safe_write(log_file, content)


if __name__ == "__main__":
    print("Ralph Wiggum Loop - Gold Tier")
    print("=" * 40)
    print("\nThis module provides the loop mechanism for")
    print("autonomous multi-step task completion.")
    print("\nUsage:")
    print("  from ralph_wiggum import run_ralph_loop")
    print("  success = run_ralph_loop(process_task, task_file)")
