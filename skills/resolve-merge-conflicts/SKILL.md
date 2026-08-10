---
name: resolve-merge-conflicts
description: "Resolve Git merge or rebase conflicts by recovering each side's intent, preserving compatible behavior, validating the result, and documenting unavoidable trade-offs."
---

# Resolve merge conflicts

1. Inspect the current merge or rebase state, conflicting files, and relevant history.
2. Recover the intent behind both sides from commits, tests, surrounding code, and available specifications.
3. Resolve each conflict by preserving both intents where compatible. Where they conflict, choose the behavior aligned with the stated integration goal and record the trade-off.
4. Do not add unrelated behavior while resolving conflicts. Ask for direction when neither intent is justified by evidence.
5. Run the project checks most likely to catch integration breakage, then complete the merge or rebase only when they pass or limitations are explicit.
6. Summarize conflicts resolved, decisions made, checks run, and remaining risks.
