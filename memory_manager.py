"""
Memory Manager - Gold Tier

Features:
- Store tasks
- Store decisions
- Recall past similar tasks
- Lightweight (no external vector DB yet)

Future Upgrade:
- Add embeddings (OpenAI / FAISS)
"""

from pathlib import Path
from datetime import datetime
import json

VAULT = Path("AI_Employee_Vault")
MEMORY = VAULT / "Memory"

TASK_MEMORY = MEMORY / "tasks.json"
DECISION_MEMORY = MEMORY / "decisions.json"


# =========================
# SETUP
# =========================

def ensure_memory():
    MEMORY.mkdir(exist_ok=True)

    if not TASK_MEMORY.exists():
        TASK_MEMORY.write_text("[]", encoding="utf-8")

    if not DECISION_MEMORY.exists():
        DECISION_MEMORY.write_text("[]", encoding="utf-8")


# =========================
# LOAD / SAVE
# =========================

def load_json(file_path):
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except:
        return []


def save_json(file_path, data):
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# =========================
# SAVE TASK
# =========================

def save_task(task_name: str, content: str):
    ensure_memory()

    tasks = load_json(TASK_MEMORY)

    tasks.append({
        "task": task_name,
        "content": content[:1000],  # limit size
        "timestamp": datetime.now().isoformat()
    })

    save_json(TASK_MEMORY, tasks)

    print(f"[Memory] Task saved: {task_name}")


# =========================
# SAVE DECISION
# =========================

def save_decision(task_name: str, decision_type: str, decision: str):
    ensure_memory()

    decisions = load_json(DECISION_MEMORY)

    decisions.append({
        "task": task_name,
        "type": decision_type,
        "decision": decision,
        "timestamp": datetime.now().isoformat()
    })

    save_json(DECISION_MEMORY, decisions)

    print(f"[Memory] Decision saved: {task_name} → {decision_type}")


# =========================
# SIMPLE RECALL (KEYWORD MATCH)
# =========================

def recall_similar_tasks(query: str, limit: int = 3):
    """
    Find similar past tasks using keyword matching
    (Lightweight alternative to embeddings)
    """
    ensure_memory()

    tasks = load_json(TASK_MEMORY)

    query_words = query.lower().split()

    scored = []

    for t in tasks:
        content = t["content"].lower()

        score = sum(1 for word in query_words if word in content)

        if score > 0:
            scored.append((score, t))

    # sort by relevance
    scored.sort(key=lambda x: x[0], reverse=True)

    return [item[1] for item in scored[:limit]]


# =========================
# GET DECISIONS FOR TASK
# =========================

def get_task_decisions(task_name: str):
    ensure_memory()

    decisions = load_json(DECISION_MEMORY)

    return [d for d in decisions if d["task"] == task_name]


def get_similar_decisions(task_content):
    memory_file = "memory.json"

    if not os.path.exists(memory_file):
        return None

    with open(memory_file, "r") as f:
        data = json.load(f)

    for item in reversed(data):  # recent first
        if any(word in task_content.lower() for word in item["task"].lower().split()):
            return item

    return None

# =========================
# SMART CONTEXT BUILDER (GOLD CORE)
# =========================

def build_context(query: str) -> str:
    """
    Build memory context for AI using past tasks
    """
    similar = recall_similar_tasks(query)

    if not similar:
        return ""

    context = "\n\n### Past Similar Tasks:\n"

    for task in similar:
        context += f"""
- Task: {task['task']}
- Content: {task['content'][:200]}
- Time: {task['timestamp']}
"""

    return context


# =========================
# GET SIMILAR DECISIONS (GOLD)
# =========================

def get_similar_decisions(query: str, limit: int = 3):
    """
    Find similar past decisions using keyword matching
    Returns the most relevant past decision for approval override
    """
    ensure_memory()

    decisions = load_json(DECISION_MEMORY)

    query_words = query.lower().split()

    scored = []

    for d in decisions:
        content = (d.get("task", "") + " " + d.get("decision", "")).lower()

        score = sum(1 for word in query_words if word in content)

        if score > 0:
            scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)

    if scored:
        best = scored[0][1]
        return {
            "task": best.get("task", ""),
            "type": best.get("type", ""),
            "decision": best.get("decision", ""),
            "requires_approval": "approval" in best.get("decision", "").lower() or "pending" in best.get("decision", "").lower()
        }

    return {}


# =========================
# TEST
# =========================

if __name__ == "__main__":
    ensure_memory()

    save_task("test_task", "Send email to client about payment")
    save_decision("test_task", "approval_check", "requires approval")

    print("\nRecall Test:")
    results = recall_similar_tasks("email client")

    for r in results:
        print(r)