#!/usr/bin/env bash

set -euo pipefail

REMOTE_URL="${1:-}"

if [[ -z "$REMOTE_URL" ]]; then
  echo "Usage: $0 <github-repository-url>"
  exit 1
fi

if [[ ! -d .git ]]; then
  git init
fi

if [[ ! -f .gitignore ]]; then
  cat > .gitignore <<'EOF'
.DS_Store
node_modules/
dist/
build/
*.log
EOF
fi

if ! git config user.name >/dev/null; then
  git config user.name "${GIT_AUTO_USER_NAME:-Auto Commit Bot}"
fi

if ! git config user.email >/dev/null; then
  git config user.email "${GIT_AUTO_USER_EMAIL:-auto-commit-bot@local}"
fi

git add .

if git diff --cached --quiet; then
  echo "No staged changes to commit."
else
  mapfile -t STAGED_FILES < <(git diff --cached --name-only)
  FILE_COUNT="${#STAGED_FILES[@]}"
  PREVIEW_LIMIT=3
  PREVIEW_FILES=("${STAGED_FILES[@]:0:$PREVIEW_LIMIT}")
  PREVIEW="$(IFS=', '; echo "${PREVIEW_FILES[*]}")"

  if (( FILE_COUNT > PREVIEW_LIMIT )); then
    COMMIT_MESSAGE="chore: update ${FILE_COUNT} files (${PREVIEW}, ...)"
  else
    COMMIT_MESSAGE="chore: update ${FILE_COUNT} files (${PREVIEW})"
  fi

  git commit -m "$COMMIT_MESSAGE"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

git branch -M main
git push -u origin main

echo "Done: pushed to origin/main"
