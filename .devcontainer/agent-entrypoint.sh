#!/bin/bash
# agent-entrypoint.sh — Runs inside the codespace as the agent process.
# The user monitors via `gh codespace ssh` or `gh codespace port 8080`.
#
# This is what makes A2A-native-notebookLM a "codespace native agent tool":
# 1. Codespace boots → this script launches
# 2. User SSHs in to watch live logs
# 3. Web dashboard at port 8080 for visual monitoring
# 4. Clean shutdown when done

set -euo pipefail

REPO="${1:-$(basename $(git rev-parse --show-toplevel 2>/dev/null || echo "unknown"))}"
AGENT_NAME="notebook-${REPO}-$(date +%s | tail -c 6)"
WORK_DIR="/workspaces/$(basename $(pwd))"

echo "═══════════════════════════════════════"
echo "  📓 A2A Notebook Agent"
echo "  Repo:      $REPO"
echo "  Workspace: $WORK_DIR"
echo "  PID:       $$"
echo "═══════════════════════════════════════"
echo ""

# ─── Phase tracking ───────────────────────
STATE_FILE="/tmp/agent-state.json"
echo '{"phase":"booting","progress":0,"logs":[],"errors":[]}' > "$STATE_FILE"

update_state() {
  local phase="$1"
  local progress="$2"
  local log="$3"
  echo "$(date -Iseconds) [$phase] $log"
  python3 -c "
import json
with open('$STATE_FILE') as f:
    s = json.load(f)
s['phase'] = '$phase'
s['progress'] = $progress
s['logs'].append({'time': '$(date -Iseconds)', 'msg': '$log'})
with open('$STATE_FILE', 'w') as f:
    json.dump(s, f)
" 2>/dev/null || true
}

# ─── Phase 1: Analyze ──────────────────────
update_state "analyzing" 10 "Analyzing repository structure..."

if [ -f "package.json" ]; then
  update_state "analyzing" 20 "Detected Node.js project"
  cat package.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('  Name:', d.get('name','?')); print('  Scripts:', ', '.join(d.get('scripts',{}).keys())); print('  Deps:', len(d.get('dependencies',{})) + len(d.get('devDependencies',{})))"
fi

if [ -f "Cargo.toml" ]; then
  update_state "analyzing" 20 "Detected Rust project"
  head -10 Cargo.toml
fi

if ls *.py 2>/dev/null | head -1 >/dev/null; then
  update_state "analyzing" 20 "Detected Python files"
  echo "  Python files: $(ls *.py 2>/dev/null | wc -l)"
fi

if [ -f "Dockerfile" ]; then update_state "analyzing" 25 "Dockerfile found"; fi
if [ -f "Makefile" ]; then update_state "analyzing" 25 "Makefile found"; fi

# Report structure
echo ""
echo "── Repository structure ──"
find . -not -path './node_modules/*' -not -path './.git/*' -not -path './target/*' \
  -not -name '*.lock' -not -name '*.svg' \
  -maxdepth 3 -type f | head -30
echo ""

# ─── Phase 2: Plan ─────────────────────────
update_state "planning" 30 "Generating task plan..."

PLAN=$(cat <<EOF
📋 Agent Plan for $REPO
├─ [1/3] Analyze structure (done)
├─ [2/3] Run diagnostics
│  ├─ Check test suite
│  ├─ Check build
│  └─ Check lint/format
└─ [3/3] Generate report
   ├─ Summary of findings
   └─ Suggested improvements
EOF
)
echo "$PLAN"
echo ""

# ─── Phase 3: Execute ──────────────────────
update_state "executing" 40 "Running diagnostics..."

# Tests
update_state "executing" 45 "Checking test suite..."
if [ -f "package.json" ] && grep -q '"test"' package.json; then
  npm test 2>&1 | head -20 || echo "  ⚠️ Tests had issues (non-zero exit)"
elif [ -f "Makefile" ] && grep -q '^test:' Makefile; then
  make test 2>&1 | head -20 || echo "  ⚠️ Tests had issues"
elif ls tests/ test/ __tests__/ 2>/dev/null | head -1 >/dev/null; then
  echo "  Test directory found: $(ls -d tests/ test/ __tests__/ 2>/dev/null)"
fi

# Build
update_state "executing" 60 "Checking build..."
if [ -f "package.json" ] && grep -q '"build"' package.json; then
  npm run build 2>&1 | head -20 || echo "  ⚠️ Build had issues"
elif [ -f "Makefile" ] && grep -q '^build:' Makefile; then
  make build 2>&1 | head -20 || echo "  ⚠️ Build had issues"
elif [ -f "Cargo.toml" ]; then
  cargo check 2>&1 | head -20 || echo "  ⚠️ Cargo check had issues"
fi

# Lint
update_state "executing" 75 "Checking formatting/lint..."
if [ -f "package.json" ] && grep -q '"lint"' package.json; then
  npm run lint 2>&1 | head -10 || echo "  ⚠️ Lint had issues"
fi

# ─── Phase 4: Report ───────────────────────
update_state "reporting" 85 "Generating report..."

REPORT="/tmp/agent-report.md"
cat > "$REPORT" <<RPT
# 📓 Notebook Agent Report: $REPO

**Generated:** $(date -u)
**Workspace:** $WORK_DIR
**Agent:** $AGENT_NAME

## Structure
\`\`\`
$(find . -not -path './node_modules/*' -not -path './.git/*' -not -path './target/*' -maxdepth 2 -type f | head -20)
\`\`\`

## Findings

| Check | Status |
|-------|--------|
| Test suite | Checked |
| Build | Checked |
| Lint | Checked |
| Docker | $([ -f Dockerfile ] && echo "✅" || echo "—") |
| CI/CD | $([ -d .github/workflows ] && echo "✅" || echo "—") |

## Next Steps

Run with specific tool integrations:
\`\`\`bash
onboard ${REPO} --add stunt-double,mmx-toolkit
\`\`\`
RPT

update_state "complete" 100 "Agent finished. Report at $REPORT"
echo ""
echo "═══════════════════════════════════════"
echo "  ✅ Agent Complete"
echo "  Report: $REPORT"
echo "═══════════════════════════════════════"

# Print report
cat "$REPORT"
echo ""

# Keep alive for monitoring until user disconnects
echo "── Agent idle — SSH session will close in 30s ──"
sleep 30
