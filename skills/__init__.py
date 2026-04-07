"""
Agent Skills - Gold Level Implementation
Modular skill-based architecture for AI Employee

Per hackathon document:
"All AI functionality should be implemented as Agent Skills"
https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
"""
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

VAULT = Path("AI_Employee_Vault")


class AgentSkill(ABC):
    """Base class for all Agent Skills"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """Execute the skill and return result"""
        pass

    def log_execution(self, result: dict):
        """Log skill execution to Logs folder"""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = VAULT / "Logs" / f"{today}.md"

        timestamp = datetime.now().isoformat()
        log_entry = f"""
## [{timestamp}] Skill: {self.name}
- **Result:** {result.get('status', 'unknown')}
- **Details:** {result.get('message', '')}

"""

        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
        else:
            content = f"# Activity Log - {today}\n\n"

        content += log_entry
        log_file.write_text(content, encoding="utf-8")


class CreatePlanSkill(AgentSkill):
    """Skill: Create action plan from task"""

    def __init__(self):
        super().__init__(
            name="create_plan",
            description="Analyze task and create structured action plan with checkboxes"
        )

    def execute(self, task_content: str, task_file: str = "") -> dict:
        """Create a plan from task content"""
        try:
            from qwen_agent import ask_qwen

            # GOLD: Load memory context BEFORE planning
            try:
                from memory_manager import build_context
                memory_context = build_context(task_content)
            except Exception:
                memory_context = ""

            prompt = f"""
Analyze this task and create a detailed action plan:

{task_content}
{memory_context}

Create a plan with:
1. Clear objective
2. Step-by-step actions with checkboxes
3. Indicate if approval is required
4. Specify which files need to be created

Format as markdown with checkboxes like:
- [ ] Step 1
- [ ] Step 2
"""

            plan_content = ask_qwen(prompt, f"Task file: {task_file}")

            plans_dir = VAULT / "Plans"
            plans_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().isoformat()
            plan_file = plans_dir / f"PLAN_{Path(task_file).stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"

            if "---" not in plan_content[:50]:
                plan_content = f"""---
type: plan
status: pending
created: {timestamp}
source_task: {task_file}
---

{plan_content}"""

            plan_file.write_text(plan_content, encoding="utf-8")

            result = {
                "status": "success",
                "message": f"Plan created: {plan_file.name}",
                "plan_file": str(plan_file)
            }

            self.log_execution(result)
            return result

        except Exception as e:
            result = {
                "status": "error",
                "message": str(e)
            }
            self.log_execution(result)
            return result


class AnalyzeForApprovalSkill(AgentSkill):
    """Skill: Analyze if task requires approval"""

    def __init__(self):
        super().__init__(
            name="analyze_for_approval",
            description="Determine if task requires human approval based on Company Handbook"
        )

    def execute(self, task_content: str, plan_content: str) -> dict:
        """Analyze if approval is needed"""
        try:
            from qwen_agent import ask_qwen

            # GOLD: Load memory context for similar past decisions
            try:
                from memory_manager import get_similar_decisions
                past_decisions = get_similar_decisions(task_content)
            except Exception:
                past_decisions = []

            prompt = f"""
Analyze if this task/plan requires human approval:

Task:
{task_content}

Plan:
{plan_content}

Check against Company Handbook rules. Flag for approval if:
- Payment involved (especially > $100)
- Sending communications (email, messages)
- File operations outside vault
- Any irreversible action

Respond in JSON format:
{{
    "requires_approval": true/false,
    "reason": "why approval is needed or not",
    "action_type": "payment|communication|file_operation|analysis|other",
    "risk_level": "low|medium|high"
}}
"""

            result_text = ask_qwen(prompt)

            import json
            try:
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                if start >= 0 and end > start:
                    approval_info = json.loads(result_text[start:end])
                else:
                    approval_info = {
                        "requires_approval": True,
                        "reason": "Default: requiring approval for safety",
                        "action_type": "other",
                        "risk_level": "medium"
                    }
            except Exception:
                approval_info = {
                    "requires_approval": True,
                    "reason": "Default: requiring approval for safety",
                    "action_type": "other",
                    "risk_level": "medium"
                }

            # GOLD: Memory-based override
            if past_decisions and past_decisions.get("requires_approval"):
                approval_info["requires_approval"] = True
                approval_info["reason"] += " (Memory indicates similar tasks required approval)"

            result = {
                "status": "success",
                "message": "Approval analysis complete",
                **approval_info
            }

            self.log_execution(result)
            return result

        except Exception as e:
            result = {
                "status": "error",
                "message": str(e),
                "requires_approval": True,
                "reason": "Error in analysis - defaulting to approval required"
            }
            self.log_execution(result)
            return result


class CreateApprovalRequestSkill(AgentSkill):
    """Skill: Create approval request file"""

    def __init__(self):
        super().__init__(
            name="create_approval_request",
            description="Create approval request file in Pending_Approval folder"
        )

    def execute(self, task_file: str, plan_content: str, reason: str, action_type: str) -> dict:
        """Create approval request"""
        try:
            timestamp = datetime.now()
            pending_approval_dir = VAULT / "Pending_Approval"
            pending_approval_dir.mkdir(exist_ok=True)

            approval_file = pending_approval_dir / f"APPROVAL_{Path(task_file).stem}_{timestamp.strftime('%Y%m%d%H%M%S')}.md"

            content = f"""---
type: approval_request
action_type: {action_type}
source_task: {Path(task_file).name}
created: {timestamp.isoformat()}
expires: {timestamp.replace(day=timestamp.day + 1).isoformat()}
status: pending
reason: {reason}
---

# Approval Required

**Action Type:** {action_type}
**Source Task:** {Path(task_file).name}
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

            result = {
                "status": "success",
                "message": f"Approval request created: {approval_file.name}",
                "approval_file": str(approval_file)
            }

            self.log_execution(result)
            return result

        except Exception as e:
            result = {
                "status": "error",
                "message": str(e)
            }
            self.log_execution(result)
            return result


class UpdateDashboardSkill(AgentSkill):
    """Skill: Update Dashboard.md"""

    def __init__(self):
        super().__init__(
            name="update_dashboard",
            description="Update Dashboard.md with current system status"
        )

    def execute(self, action: str = "", details: str = "") -> dict:
        """Update dashboard"""
        try:
            dashboard = VAULT / "Dashboard.md"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            pending_count = len(list((VAULT / "Needs_Action").glob("*.md")))
            approval_count = len(list((VAULT / "Pending_Approval").glob("*.md")))
            done_count = len(list((VAULT / "Done").glob("*.md")))

            content = f"""# Dashboard

*Last updated: {timestamp}*

## Summary
- **Pending Tasks:** {pending_count}
- **Awaiting Approval:** {approval_count}
- **Completed Today:** {done_count}

## Pending Tasks
"""

            pending_tasks = list((VAULT / "Needs_Action").glob("*.md"))[:10]
            if pending_tasks:
                for task in pending_tasks:
                    content += f"- [ ] {task.name}\n"
            else:
                content += "- None\n"

            content += "\n## Awaiting Approval\n"
            approval_tasks = list((VAULT / "Pending_Approval").glob("*.md"))[:10]
            if approval_tasks:
                for task in approval_tasks:
                    content += f"- [WAITING] {task.name}\n"
            else:
                content += "- None\n"

            content += f"""
## Recent Activity
- [{timestamp}] {action}: {details}

---
*Generated by AI Employee v0.3 - Gold Level*
"""

            dashboard.write_text(content, encoding="utf-8")

            result = {
                "status": "success",
                "message": "Dashboard updated",
                "pending_count": pending_count,
                "approval_count": approval_count
            }

            self.log_execution(result)
            return result

        except Exception as e:
            result = {
                "status": "error",
                "message": str(e)
            }
            self.log_execution(result)
            return result


# Skill Registry
SKILL_REGISTRY = {
    "create_plan": CreatePlanSkill,
    "analyze_for_approval": AnalyzeForApprovalSkill,
    "create_approval_request": CreateApprovalRequestSkill,
    "update_dashboard": UpdateDashboardSkill
}


def get_skill(skill_name: str) -> AgentSkill:
    """Get a skill instance by name"""
    if skill_name in SKILL_REGISTRY:
        return SKILL_REGISTRY[skill_name]()
    else:
        raise ValueError(f"Unknown skill: {skill_name}")


def list_skills() -> list:
    """List all available skills"""
    return [
        {"name": name, "description": skill().description}
        for name, skill in SKILL_REGISTRY.items()
    ]


if __name__ == "__main__":
    print("Available Skills:")
    for skill_info in list_skills():
        print(f"  - {skill_info['name']}: {skill_info['description']}")
