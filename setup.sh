#!/usr/bin/env bash
# setup.sh — A2A Notebook Agent: one-command setup
#
# Spawns a codespace-native agent. You watch it work through Codespaces TUI.
#
# Usage:
#   curl -sL https://rawgit.../SuperInstance/A2A-native-notebookLM/main/setup.sh | bash -s <repo>
#   bash setup.sh SuperInstance/pincher

set -euo pipefail

REPO="${1:-}"
if [ -z "$REPO" ]; then
  if git rev-parse --git-dir 2>/dev/null; then
    REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*:\(.*\)\.git/\1/')
  fi
fi
if [ -z "$REPO" ]; then
  echo "Usage: bash setup.sh <owner/repo>"
  echo "  Or run from inside a git repo"
  exit 1
fi

NAME="nb-$(basename "$REPO" | tr '[:upper:]' '[:lower:]')-$(date +%s | tail -c 7)"
BRANCH="notebook-$(date +%s)"

echo "═══════════════════════════════════════"
echo "  📓 A2A Notebook Agent — $REPO"
echo ""
echo "  Monitor:"
echo "    gh codespace ssh $NAME       # Live logs"
echo "    gh codespace port 8080 $NAME # Web dashboard"
echo "═══════════════════════════════════════"

# 1. Create codespace
echo "→ Creating codespace... ($NAME)"
CODESPACE=$(gh codespace create --repo "$REPO" --branch "$BRANCH" \
  --machine basicLinux32gb --idle-timeout 30m --wait-timeout 600 \
  --display-name "$NAME" 2>&1 | tail -1)
echo "   Codespace: $CODESPACE"

# 2. Wait for boot
echo "→ Waiting for boot..."
gh codespace wait --codespace "$CODESPACE" --timeout 600 >/dev/null 2>&1

# 3. Copy agent scripts into codespace via base64
echo "→ Deploying agent..."

# Read agent scripts, base64 encode, pipe into codespace
AGENT_B64=$(base64 < /home/ubuntu/.openclaw/workspace/A2A-native-notebookLM/.devcontainer/agent-entrypoint.sh)
DASHBOARD_B64=$(base64 < /home/ubuntu/.openclaw/workspace/A2A-native-notebookLM/.devcontainer/dashboard.py)

gh codespace ssh --codespace "$CODESPACE" -- bash -c "
mkdir -p /tmp/agent
echo '$AGENT_B64' | base64 -d > /tmp/agent/agent.sh
echo '$DASHBOARD_B64' | base64 -d > /tmp/agent/dashboard.py
chmod +x /tmp/agent/agent.sh
echo 'Agent deployed'
" 2>/dev/null

echo "   Agent deployed"

echo ""
echo "   ┌────────────────────────────────────────────┐"
echo "   │  📓 Agent starting!                        │"
echo "   │  gh codespace ssh $NAME    │"
echo "   │  gh codespace port 8080 $NAME│"
echo "   └────────────────────────────────────────────┘"
echo ""

# 4. Launch agent + dashboard
gh codespace ssh --codespace "$CODESPACE" -- bash -c "
cd /workspaces/$(basename "$REPO")
python3 /tmp/agent/dashboard.py &
DASH_PID=\$!
bash /tmp/agent/agent.sh '$(basename "$REPO")'
EXIT=\$?
kill \$DASH_PID 2>/dev/null
echo '═══ Agent done (exit: \$EXIT) ═══'
exit \$EXIT
" 2>/dev/null

EXIT_CODE=$?

# 5. Cleanup
echo "→ Cleaning up codespace..."
gh codespace delete --codespace "$CODESPACE" --force >/dev/null 2>&1 || true
echo "→ Done (exit: $EXIT_CODE)"
exit $EXIT_CODE
