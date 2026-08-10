---
name: verify-and-ship
description: "Verify a completed repository change, run declared tests and lint, inspect the diff for generated artifacts or secrets, and commit and publish only when repository policy or the user authorizes it. Use before finishing or shipping work."
---

# Verify and ship

1. Read the repository `AGENTS.md` and use its declared test and lint commands. Do not invent passing checks.
2. Inspect `git status`, the scoped diff, and `git diff --check`. Confirm generated artifacts, temporary files, credentials, and unrelated edits are absent.
3. Run the focused tests first, then relevant broader tests, lint, build, or validation commands. Record failures and anything not run.
4. Re-inspect the final diff. Confirm documentation, generated outputs, and compatibility requirements are satisfied.
5. Commit only scoped files with an accurate message when the user or repository policy authorizes a commit.
6. Push only when the user or repository policy authorizes it. For indium-agentkit, push completed scoped work directly to `origin/main`.
7. Report the commit, destination, checks run, and remaining limitations.
