# Releasing

Use semantic versioning once published releases begin. Before `1.0.0`, treat
breaking changes as a minor-version change and compatible additions as a patch
or minor-version change according to their user impact.

For each release:

1. Choose the version and commit range.
2. Run content validation, tests, and Cursor-rule generation.
3. Use the `release-notes` skill to draft user-facing notes.
4. Call out installation changes, removed or renamed skills, migration steps,
   compatibility implications, and known limitations.
5. Commit release metadata, tag the verified commit, and publish the release.

Do not claim support for a tool, version, or workflow that the compatibility
matrix and CI have not verified.
