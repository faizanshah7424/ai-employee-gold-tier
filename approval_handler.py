"""
Approval Handler - Bronze Level Implementation
Processes approved files and executes actions
Handles lifecycle: Pending_Approval → Approved → Done

FIXES APPLIED:
1. Safe file reading with UTF-8/latin-1 fallback
2. All file writes use encoding="utf-8"
3. Proper error handling for corrupted files
"""
from pathlib import Path
from datetime import datetime
import re

VAULT = Path("AI_Employee_Vault")

# Folder paths
PENDING_APPROVAL = VAULT / "Pending_Approval"
APPROVED = VAULT / "Approved"
REJECTED = VAULT / "Rejected"
DONE = VAULT / "Done"
LOGS = VAULT / "Logs"
PLANS = VAULT / "Plans"
NEEDS_ACTION = VAULT / "Needs_Action"


def safe_read(file_path: Path) -> str:
    """
    Safely read file content with encoding fallback.
    Try UTF-8 first, fallback to latin-1 if decoding fails.
    
    Args:
        file_path: Path to file to read
        
    Returns:
        File content as string
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def safe_write(file_path: Path, content: str):
    """
    Safely write file content with UTF-8 encoding.
    
    Args:
        file_path: Path to file to write
        content: Content to write
    """
    file_path.write_text(content, encoding="utf-8")


def ensure_folders():
    """Ensure all required folders exist"""
    for folder in [PENDING_APPROVAL, APPROVED, REJECTED, DONE, LOGS]:
        folder.mkdir(exist_ok=True)


def log_action(action_type: str, details: str, status: str = "completed"):
    """Log an action to the Logs folder"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOGS / f"{today}.md"

    timestamp = datetime.now().isoformat()
    log_entry = f"""
## [{timestamp}] {action_type}
- **Status:** {status}
- **Details:** {details}

"""

    if log_file.exists():
        content = safe_read(log_file)
    else:
        content = f"# Activity Log - {today}\n\n"

    content += log_entry
    safe_write(log_file, content)


def parse_approval_file(file_path: Path) -> dict:
    """
    Parse an approval file to extract metadata and proposed actions

    Args:
        file_path: Path to the approval file

    Returns:
        dict with approval file metadata
    """
    # FIX ISSUE 1: Use safe_read for UTF-8/latin-1 fallback
    content = safe_read(file_path)

    # Extract frontmatter
    frontmatter = {}
    if content.startswith("---"):
        match = re.search(r'---\n(.*?)\n---', content, re.DOTALL)
        if match:
            fm_text = match.group(1)
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()

    return {
        'type': frontmatter.get('type', 'approval_request'),
        'action_type': frontmatter.get('action_type', 'unknown'),
        'source_task': frontmatter.get('source_task', ''),
        'created': frontmatter.get('created', ''),
        'status': frontmatter.get('status', 'pending'),
        'reason': frontmatter.get('reason', ''),
        'content': content,
        'file_path': file_path
    }


def execute_action(approval_data: dict) -> bool:
    """
    Execute the approved action

    For Bronze level, this is a simulation that logs the intended action.
    In a full implementation, this would call MCP servers or other action handlers.

    Args:
        approval_data: Parsed approval file data

    Returns:
        True if action executed successfully
    """
    action_type = approval_data.get('action_type', 'unknown')
    source_task = approval_data.get('source_task', 'unknown')

    print(f"[ApprovalHandler] Executing action: {action_type} for {source_task}")

    # Bronze level: Log the action execution
    log_action(
        action_type=f"execute_{action_type}",
        details=f"Executed approved action for {source_task}. Action type: {action_type}",
        status="completed"
    )

    print(f"[ApprovalHandler] Action '{action_type}' logged as executed (Bronze level simulation)")

    return True

    if action_type == "linkedin_post":
        import requests
        requests.post("http://localhost:5001/execute-post", json={
            "file": approval_file.name
    })


def move_to_done(file_path: Path, prefix: str = ""):
    """
    Move a file to the Done folder with timestamp

    Args:
        file_path: Path to the file to move
        prefix: Optional prefix for the new filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{prefix}{file_path.stem}_DONE_{timestamp}.md"
    dest = DONE / new_name

    try:
        file_path.rename(dest)
        print(f"[ApprovalHandler] Moved to Done: {new_name}")
    except Exception as e:
        print(f"[ApprovalHandler] Error moving file: {e}")
        # If rename fails (cross-device), copy and delete
        try:
            safe_write(dest, safe_read(file_path))
        except:
            safe_write(dest, file_path.read_text(errors="replace"))
        file_path.unlink()


def process_approved_file(approved_file: Path) -> bool:
    """
    Process a single approved file

    Args:
        approved_file: Path to the approved file

    Returns:
        True if processed successfully
    """
    print(f"[ApprovalHandler] Processing approved file: {approved_file.name}")

    try:
        # Parse the approval file using safe_read
        approval_data = parse_approval_file(approved_file)

        # Execute the action
        if execute_action(approval_data):
            # Move approval file to Done
            move_to_done(approved_file, "APPROVAL_")

            # Find and move related plan file to Done
            source_task = approval_data.get('source_task', '')
            if source_task:
                # Remove .md extension for matching
                task_stem = source_task.replace('.md', '')

                # Look for matching plan file
                for plan_file in PLANS.glob(f"PLAN_{task_stem}*.md"):
                    move_to_done(plan_file, "PLAN_")

                # Look for original task file and move to Done
                for task_file in NEEDS_ACTION.glob(source_task):
                    move_to_done(task_file, "TASK_")

            log_action(
                action_type="approval_processed",
                details=f"Completed processing for {approved_file.name}",
                status="done"
            )

            return True
        else:
            print(f"[ApprovalHandler] Failed to execute action for {approved_file.name}")
            return False

    except Exception as e:
        print(f"[ApprovalHandler] Error processing {approved_file.name}: {e}")
        log_action(
            action_type="error",
            details=f"Failed to process {approved_file.name}: {str(e)}",
            status="error"
        )
        return False


def run():
    """
    Main function to process all approved files

    Checks the Approved folder and processes any files found there.
    This is called by the orchestrator in a loop.
    """
    ensure_folders()

    approved_files = list(APPROVED.glob("*.md"))

    if not approved_files:
        print("[ApprovalHandler] No approved files to process")
        return 0

    processed = 0
    for file in approved_files:
        if process_approved_file(file):
            processed += 1

    print(f"[ApprovalHandler] Processed {processed}/{len(approved_files)} approved files")
    return processed


def check_rejected():
    """
    Check and process rejected files

    Moves rejected files to Rejected folder and logs the rejection.
    This should be called periodically to clean up rejected items.
    """
    rejected_files = list(REJECTED.glob("*.md"))

    for file in rejected_files:
        print(f"[ApprovalHandler] Rejected file: {file.name}")
        log_action(
            action_type="rejected",
            details=f"Human rejected: {file.name}",
            status="rejected"
        )

        # Move to Done with REJECTED prefix for record keeping
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"REJECTED_{file.stem}_{timestamp}.md"
        dest = DONE / new_name
        try:
            file.rename(dest)
        except:
            try:
                safe_write(dest, safe_read(file))
            except:
                safe_write(dest, file.read_text(errors="replace"))
            file.unlink()


if __name__ == "__main__":
    # Test run
    count = run()
    check_rejected()
    print(f"[ApprovalHandler] Completed. Processed {count} approved files.")
