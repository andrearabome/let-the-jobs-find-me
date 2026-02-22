#!/bin/bash

# Simple script to add, commit, and push changes to GitHub

git add .

if [ -z "$1" ]; then
    COMMIT_MESSAGE="Update $(date '+%Y-%m-%d %H:%M:%S')"
else
    COMMIT_MESSAGE="$1"
fi

git commit -m "$COMMIT_MESSAGE"
git push

echo "✓ Changes pushed to GitHub!"
