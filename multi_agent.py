"""
Multi-Agent System - Platinum Tier
Implements intelligent decision-making with specialized agents:
- PlannerAgent: Creates detailed action plans
- ReviewerAgent: Makes intelligent decisions (approval_required, execute_directly, reject)
- ExecutorAgent: Executes approved actions

Per hackathon document:
"High-level reasoning, autonomy, and flexibility"
"Think of it as hiring a senior employee who figures out how to solve the problems"
"""
from pathlib import Path
from datetime import datetime
from qwen_agent import ask_qwen
import json

VAULT = Path("AI_Employee_Vault")
PLANS = VAULT / "Plans"


class PlannerAgent:
    """
    PlannerAgent: Analyzes tasks and creates detailed action plans
    Uses AI reasoning to break down tasks into actionable steps
    """

    def plan(self, task_content: str, task_file: str = "") -> dict:
        """
        Create a detailed action plan from task content

        Returns:
            dict with plan content and metadata
        """
        prompt = f"""
Analyze this task and create a detailed action plan:

{task_content}

Create a plan with:
1. Clear objective
2. Step-by-step actions with checkboxes
3. Identify any external actions needed (emails, posts, payments)
4. Specify if approval is required for any steps

Format as markdown with checkboxes:
- [ ] Step 1
- [ ] Step 2
"""

        try:
            plan_content = ask_qwen(prompt, f"Task file: {task_file}")

            # Save plan to Plans folder
            PLANS.mkdir(exist_ok=True)
            timestamp = datetime.now().isoformat()
            plan_file = PLANS / f"PLAN_{Path(task_file).stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"

            if "---" not in plan_content[:50]:
                plan_content = f"""---
type: plan
status: pending
created: {timestamp}
source_task: {task_file}
---

{plan_content}"""

            plan_file.write_text(plan_content, encoding="utf-8")

            return {
                "status": "success",
                "plan_content": plan_content,
                "plan_file": str(plan_file)
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


class ReviewerAgent:
    """
    ReviewerAgent: Makes intelligent decisions using rule-based + AI analysis
    with adaptive learning from memory.

    Returns structured decision:
    {
        "decision": "approval_required | execute_directly | reject",
        "reason": "why this decision was made",
        "confidence": float (0-1)
    }

    Decision logic follows hackathon document security rules:
    - External communications ALWAYS require approval
    - Payments ALWAYS require approval
    - Internal analysis tasks can execute directly
    - Unclear tasks are rejected with explanation
    - Memory adjusts confidence for edge cases (adaptive learning)
    """

    # Keywords that ALWAYS require approval (external actions)
    APPROVAL_KEYWORDS = [
        "post", "email", "linkedin", "publish", "payment",
        "send", "transfer", "upload", "share", "message",
        "delete", "remove", "modify database", "credentials",
        "api request", "http", "webhook"
    ]

    # Keywords that can execute directly (internal actions)
    EXECUTE_KEYWORDS = [
        "analyze", "read", "process", "summarize", "review",
        "check", "report", "generate", "calculate", "extract",
        "organize", "categorize", "sort", "count", "list"
    ]

    # Confidence score mapping
    CONFIDENCE_MAP = {
        "high": 0.95,
        "medium": 0.75,
        "low": 0.50
    }

    def review(self, task_content: str, plan_content: str = "") -> dict:
        """
        Review task and plan, return structured decision

        Returns:
            {
                "decision": "approval_required" | "execute_directly" | "reject",
                "reason": "explanation",
                "confidence": 0.0-1.0
            }
        """
        full_content = (task_content + " " + plan_content).lower()
        decision = self._make_decision(task_content, full_content)

        # Convert string confidence to float
        raw_confidence = decision.get("confidence", "low")
        if isinstance(raw_confidence, str):
            confidence = self.CONFIDENCE_MAP.get(raw_confidence.lower(), 0.50)
        elif isinstance(raw_confidence, (int, float)):
            confidence = float(raw_confidence)
        else:
            confidence = 0.50

        # ADAPTIVE LEARNING: Adjust based on past similar decisions
        confidence, reason = self._adapt_from_memory(
            task_content, decision["decision"], confidence, decision["reason"]
        )

        return {
            "decision": decision["decision"],
            "reason": reason,
            "confidence": confidence,
            "action_type": decision.get("action_type", "unknown")
        }

    def _make_decision(self, task_content: str, full_content: str) -> dict:
        """
        Core decision logic with rule-based + AI analysis
        """
        # RULE 1: Check for empty or unclear tasks
        if not task_content or len(task_content.strip()) < 10:
            return {
                "decision": "reject",
                "reason": "Task is unclear or empty - insufficient information to process",
                "confidence": "high",
                "action_type": "unclear"
            }

        # RULE 2: Check for external actions (ALWAYS require approval per document)
        for keyword in self.APPROVAL_KEYWORDS:
            if keyword in full_content:
                return {
                    "decision": "approval_required",
                    "reason": f"External action detected ('{keyword}') - requires human approval per Company Handbook",
                    "confidence": "high",
                    "action_type": "external_action"
                }

        # RULE 3: Check for safe internal actions
        for keyword in self.EXECUTE_KEYWORDS:
            if keyword in full_content:
                return {
                    "decision": "execute_directly",
                    "reason": f"Internal action detected ('{keyword}') - safe to execute directly",
                    "confidence": "high",
                    "action_type": "internal_action"
                }

        # RULE 4: Use AI for ambiguous cases
        try:
            ai_decision = self._ai_decision(task_content, full_content)
            return ai_decision
        except Exception:
            # Fallback: default to approval for safety
            return {
                "decision": "approval_required",
                "reason": "Unclear action type - defaulting to approval for safety",
                "confidence": "low",
                "action_type": "unknown"
            }

    def _adapt_from_memory(self, task_content: str, decision: str, confidence: float, reason: str) -> tuple:
        """
        Adaptive learning: Adjust decision confidence based on past similar decisions.

        This does NOT override rules - only adjusts confidence for edge cases.
        - If similar tasks were approved frequently → increase confidence for execute_directly
        - If similar tasks were rejected frequently → increase confidence for reject
        - If similar tasks required approval → increase confidence for approval_required

        Args:
            task_content: Current task content
            decision: Current rule-based decision
            confidence: Current confidence (0-1)
            reason: Current reason

        Returns:
            (adjusted_confidence, adjusted_reason)
        """
        try:
            from memory_manager import get_similar_decisions
            similar = get_similar_decisions(task_content)

            if not similar:
                return confidence, reason

            # Get past decision details
            past_decision = similar.get("decision", "")
            past_type = similar.get("type", "")

            # Adjust confidence based on consistency with past decisions
            if past_decision:
                # Check if current decision matches past pattern
                decision_matches = self._decisions_match(decision, past_decision, past_type)

                if decision_matches:
                    # Past decisions support current decision → increase confidence
                    if confidence < 0.95:
                        adjusted_confidence = min(confidence + 0.10, 0.99)
                        adjusted_reason = f"{reason} (Memory: similar task had same decision, confidence increased)"
                        print(f"[ReviewerAgent] Adaptive learning: +10% confidence (memory support)")
                        return adjusted_confidence, adjusted_reason
                else:
                    # Past decisions differ → reduce confidence (edge case)
                    if confidence > 0.60:
                        adjusted_confidence = max(confidence - 0.15, 0.50)
                        adjusted_reason = f"{reason} (Memory: similar task had different decision, confidence reduced)"
                        print(f"[ReviewerAgent] Adaptive learning: -15% confidence (memory conflict)")
                        return adjusted_confidence, adjusted_reason

        except Exception as e:
            # Memory is optional - continue without adaptation
            print(f"[ReviewerAdapter] Memory adaptation skipped: {e}")

        return confidence, reason

    def _decisions_match(self, current_decision: str, past_decision: str, past_type: str) -> bool:
        """
        Check if current decision is consistent with past decision.
        """
        # Map past decision types to current decision types
        if past_type == "approval_check":
            if "requires_approval=True" in past_decision:
                return current_decision == "approval_required"
            elif "requires_approval=False" in past_decision:
                return current_decision == "execute_directly"
        elif past_type == "status":
            if "pending_approval" in past_decision:
                return current_decision == "approval_required"
            elif "rejected" in past_decision:
                return current_decision == "reject"
            elif "executed" in past_decision:
                return current_decision == "execute_directly"

        # Default: consider them matching if similar keywords appear
        return current_decision.lower() in past_decision.lower() or past_decision.lower() in current_decision.lower()

    def _ai_decision(self, task_content: str, full_content: str) -> dict:
        """
        Use AI reasoning for ambiguous cases
        """
        prompt = f"""
Analyze this task and determine if it requires human approval.

Task:
{task_content}

Decision Rules:
- Return "approval_required" if task involves external actions (emails, posts, payments, API calls)
- Return "execute_directly" if task is internal (analysis, reading, processing, summarizing)
- Return "reject" if task is unclear or impossible to process

Respond in JSON format:
{{
    "decision": "approval_required" | "execute_directly" | "reject",
    "reason": "explanation of decision",
    "confidence": 0.0 to 1.0 (how sure you are),
    "action_type": "external_action" | "internal_action" | "unclear"
}}
"""

        try:
            result = ask_qwen(prompt)

            # Parse JSON from response
            start = result.find('{')
            end = result.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(result[start:end])
                return {
                    "decision": data.get("decision", "approval_required"),
                    "reason": data.get("reason", "AI analysis complete"),
                    "confidence": data.get("confidence", "medium"),
                    "action_type": data.get("action_type", "unknown")
                }
        except Exception:
            pass

        # Fallback
        return {
            "decision": "approval_required",
            "reason": "AI analysis failed - defaulting to approval for safety",
            "confidence": "low",
            "action_type": "unknown"
        }


class ExecutorAgent:
    """
    ExecutorAgent: Executes approved actions
    For Bronze/Silver: logs execution (simulation)
    For Gold+: can integrate with MCP servers for real actions
    """

    def execute(self, task_file: Path, plan_content: str, decision: dict) -> dict:
        """
        Execute an approved action

        Returns:
            dict with execution result
        """
        action_type = decision.get("action_type", "unknown")

        try:
            # Log execution
            print(f"[ExecutorAgent] Executing: {task_file.name}")
            print(f"[ExecutorAgent] Action type: {action_type}")
            print(f"[ExecutorAgent] Decision: {decision.get('decision', 'unknown')}")

            # For Bronze/Silver: Simulation
            # For Gold+: Would call MCP servers here

            return {
                "status": "success",
                "message": f"Executed: {task_file.name}",
                "action_type": action_type
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


# =========================
# MULTI-AGENT ORCHESTRATOR
# =========================

def run_multi_agent(task_file: Path) -> tuple:
    """
    Run the complete multi-agent pipeline

    Returns:
        tuple: (plan_file, decision_result)
    """
    # Initialize agents
    planner = PlannerAgent()
    reviewer = ReviewerAgent()

    # Read task content
    try:
        task_content = task_file.read_text(encoding="utf-8")
    except Exception:
        task_content = task_file.read_text(encoding="latin-1")

    print(f"[MultiAgent] Running PlannerAgent for: {task_file.name}")

    # Step 1: PlannerAgent creates plan
    plan_result = planner.plan(task_content, str(task_file))

    if plan_result["status"] != "success":
        raise Exception(f"Planning failed: {plan_result.get('message', 'Unknown')}")

    plan_file = Path(plan_result["plan_file"])
    plan_content = plan_result["plan_content"]

    print(f"[MultiAgent] Plan created: {plan_file.name}")
    print(f"[MultiAgent] Running ReviewerAgent...")

    # Step 2: ReviewerAgent makes decision
    decision = reviewer.review(task_content, plan_content)

    print(f"[MultiAgent] Decision: {decision['decision']}")
    print(f"[MultiAgent] Reason: {decision['reason']}")

    return plan_file, decision


if __name__ == "__main__":
    # Test multi-agent system
    print("="*60)
    print("  Multi-Agent System Test")
    print("="*60)

    # Test ReviewerAgent decision logic
    reviewer = ReviewerAgent()

    test_cases = [
        ("Post to LinkedIn about new product", "External action"),
        ("Analyze business goals and suggest improvements", "Internal action"),
        ("Send email to client with invoice", "External action"),
        ("", "Empty task"),
        ("Summarize last week's completed tasks", "Internal action"),
        ("Make payment to vendor for services", "External action"),
    ]

    print("\nReviewerAgent Test Cases:")
    print("-" * 60)

    for task, expected in test_cases:
        result = reviewer.review(task)
        print(f"\nTask: '{task[:50]}...'")
        print(f"Expected: {expected}")
        print(f"Decision: {result['decision']}")
        print(f"Reason: {result['reason']}")
        print(f"Confidence: {result['confidence']}")
