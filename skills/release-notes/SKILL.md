---
name: release-notes
description: "Create accurate user-facing release notes or changelog entries from a commit range, tags, issues, and repository history, including breaking changes, migrations, and known limitations."
---

# Release notes

1. Establish the release version and commit or tag range. State assumptions when either is unavailable.
2. Read commit messages, linked issues, affected documentation, and migration notes. Verify claims against the diff when possible.
3. Group changes by user impact: added, changed, fixed, deprecated, removed, security, and infrastructure where relevant.
4. Call out breaking changes, required migrations, upgrade steps, and known limitations prominently.
5. Write concise, factual notes without inventing benefits, compatibility, or performance claims.
6. Include verification status and a draft-versus-final label when the release has not yet shipped.
