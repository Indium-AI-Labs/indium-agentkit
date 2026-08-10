# Security policy

Treat every third-party skill, helper script, and reference as untrusted until
reviewed. Confirm its license, source, pinned revision, dependencies, network
behavior, file-system scope, and secret-handling behavior before redistribution.

Never commit credentials, private keys, access tokens, production data, or
unredacted logs. `scripts/validate_content.py` detects common credential shapes,
but it is not a complete secret scanner.

Keep review and verification agents read-only by default. Require explicit user
authorization before destructive operations, production access, dependency
changes, external messages, or publishing outside this repository's stated
policy.

To report a vulnerability, open a private GitHub security advisory for this
repository rather than filing a public issue.
