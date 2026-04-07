"""
Qwen Agent - Bronze Level Implementation
Provides AI reasoning using Qwen/OpenRouter with proper context from Company Handbook and Business Goals
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

VAULT = Path("AI_Employee_Vault")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def load_context():
    """Load Company Handbook and Business Goals for context"""
    handbook = ""
    business_goals = ""
    
    handbook_path = VAULT / "Company_Handbook.md"
    if handbook_path.exists():
        handbook = handbook_path.read_text()
    
    goals_path = VAULT / "Business_Goals.md"
    if goals_path.exists():
        business_goals = goals_path.read_text()
    
    return handbook, business_goals


def ask_qwen(prompt: str, task_context: str = "") -> str:
    """
    Send a prompt to Qwen with proper context from Company Handbook and Business Goals
    
    Args:
        prompt: The main task prompt
        task_context: Additional context about the specific task
    
    Returns:
        Qwen's response
    """
    handbook, business_goals = load_context()
    
    system_prompt = f"""You are an AI Employee working for a small business. You are part of a Bronze-level Personal AI Employee system.

## Your Role
- Analyze tasks and create detailed action plans
- Follow the Company Handbook rules strictly
- Align actions with Business Goals
- Always request approval for sensitive actions (payments, communications, file deletions)
- Think step-by-step and be thorough

## Company Handbook (Rules of Engagement)
{handbook if handbook else "No handbook defined yet."}

## Business Goals
{business_goals if business_goals else "No business goals defined yet."}

## Bronze Level Constraints
- You can read and write to the Obsidian vault
- You create plans in /Plans folder
- You request approval for sensitive actions via /Pending_Approval folder
- You log all actions to /Logs folder
- You update the Dashboard.md after completing tasks

## Response Format
When creating plans, use this format:
```markdown
---
type: plan
status: pending
requires_approval: true/false
created: YYYY-MM-DDTHH:MM:SS
---

# Plan: [Task Name]

## Objective
[Clear statement of what needs to be accomplished]

## Steps
- [ ] Step 1
- [ ] Step 2
...

## Approval Required
[If approval is needed, explain what and why]

## Files to Create
- /Pending_Approval/[filename].md (if approval needed)
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{task_context}\n\n{prompt}" if task_context else prompt}
    ]
    
    try:
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-7b-instruct",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = f"Error calling Qwen API: {e}"
        print(f"[QwenAgent] {error_msg}")
        return error_msg


def create_plan(task_file: Path, content: str) -> Path:
    """
    Create a plan file based on task content
    
    Args:
        task_file: The original task file path
        content: The task content to analyze
    
    Returns:
        Path to the created plan file
    """
    prompt = f"""
Analyze this task and create a detailed action plan:

{content}

Create a plan with:
1. Clear objective
2. Step-by-step actions with checkboxes
3. Indicate if approval is required (for payments, communications, sensitive actions)
4. Specify which files need to be created
"""
    
    result = ask_qwen(prompt, f"Task file: {task_file.name}")
    
    plans_dir = VAULT / "Plans"
    plans_dir.mkdir(exist_ok=True)
    
    plan_file = plans_dir / f"PLAN_{task_file.stem}.md"
    
    # Add frontmatter if not present
    if "---" not in result[:50]:
        result = f"""---
type: plan
status: pending
created: {__import__('datetime').datetime.now().isoformat()}
source_task: {task_file.name}
---

{result}"""
    
    plan_file.write_text(result)
    print(f"[QwenAgent] Plan created: {plan_file.name}")
    return plan_file


def analyze_for_approval(plan_content: str, task_content: str) -> dict:
    """
    Analyze if a task requires approval and what type
    
    Returns:
        dict with 'requires_approval', 'reason', 'action_type'
    """
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
    
    result = ask_qwen(prompt)
    
    # Try to parse JSON from response
    import json
    try:
        # Find JSON in response
        start = result.find('{')
        end = result.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(result[start:end])
    except:
        pass
    
    # Default response if parsing fails
    return {
        "requires_approval": True,
        "reason": "Default: requiring approval for safety",
        "action_type": "other",
        "risk_level": "medium"
    }


if __name__ == "__main__":
    # Test the agent
    test_content = """
---
type: file_drop
original_name: test.txt
---

Please analyze this file and determine what actions are needed.
"""
    result = create_plan(Path("test.md"), test_content)
    print(f"Test plan created at: {result}")
