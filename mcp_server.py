from flask import Flask, request, jsonify
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

VAULT = Path("AI_Employee_Vault")


# ==============================
# HEALTH CHECK
# ==============================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "MCP Server Running"})


# ==============================
# CREATE TASK (MAIN FEATURE)
# ==============================
@app.route("/create-task", methods=["POST"])
def create_task():
    data = request.json

    title = data.get("title", "No Title")
    content = data.get("content", "")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file = VAULT / "Inbox" / f"MCP_TASK_{timestamp}.md"

    task_content = f"""---
type: mcp_task
source: api
title: {title}
status: new
created: {timestamp}
---

{content}
"""

    file.write_text(task_content, encoding="utf-8")

    return jsonify({
        "status": "success",
        "file_created": file.name
    })


# ==============================
# GET SYSTEM STATUS
# ==============================
@app.route("/status", methods=["GET"])
def status():
    needs = list((VAULT / "Needs_Action").glob("*.md"))
    plans = list((VAULT / "Plans").glob("*.md"))
    approvals = list((VAULT / "Pending_Approval").glob("*.md"))
    done = list((VAULT / "Done").glob("*.md"))

    return jsonify({
        "needs_action": len(needs),
        "plans": len(plans),
        "pending_approval": len(approvals),
        "done": len(done)
    })


# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    app.run(port=5000, debug=True)

print(f"[MCP] Task created: {file.name}")    