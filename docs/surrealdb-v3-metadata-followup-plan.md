# SurrealDB v3 Metadata Refactor and Release Plan

## Purpose

Prepare a focused follow-up change set to:

1. Replace JSON roundtrip extraction in namespace and database metadata paths with typed extraction.
2. Keep dependency surface stable by avoiding a new direct surrealdb-types dependency.
3. Bump package version to 0.5.0 due SurrealDB v3 server requirement.
4. Document compatibility expectations clearly for users.

## Decisions

1. Do not add a direct surrealdb-types dependency in Cargo.toml.
2. Use surrealdb re-exports for typed extraction support.
3. Include version bump to 0.5.0 in the same implementation batch.

## Scope

In scope:

1. Metadata extraction logic in tools module.
2. Package version update.
3. User-facing compatibility docs.
4. Build and test validation.

Out of scope:

1. Behavioral changes to query, CRUD, relation, cloud tools, auth, or transport logic.
2. Feature flag redesign.
3. Release pipeline changes beyond version metadata.

## Implementation Steps

1. Update typed extraction data models in src/tools/mod.rs for namespace and database metadata parsing.
2. Replace serde_json to_string plus from_str roundtrip in list_namespaces with direct typed take extraction.
3. Replace serde_json to_string plus from_str roundtrip in list_databases with direct typed take extraction.
4. Keep response payload shape unchanged:
   - namespaces and count
   - databases and count
5. Preserve existing log messages and metrics keys for both metadata tools.
6. Bump package version in Cargo.toml from 0.4.0 to 0.5.0.
7. Add a compatibility note in README.md stating SurrealDB v3 requirement:
   - minimum supported server line: >= 3.0.0-alpha.1
   - upper bound intent: < 4.0.0
8. Keep release.toml unchanged unless release automation indicates a mismatch.

## Validation Plan

1. Run cargo check and ensure no new warnings or errors.
2. Run cargo test -q and confirm all tests pass.
3. Perform a manual smoke test:
   - connect to a SurrealDB v3 endpoint
   - run list_namespaces
   - run list_databases
   - verify output shape and field names are unchanged
4. Confirm Cargo.toml does not include a new direct surrealdb-types dependency.

## Risk Assessment

1. Low runtime risk: changes are isolated to low-frequency metadata operations.
2. Medium compatibility risk: typed extraction must match current response structure.
3. Low release risk: version bump and docs update are straightforward.

## Acceptance Criteria

1. Metadata extraction no longer uses JSON roundtrip in list_namespaces and list_databases.
2. Output schema remains backward-compatible for callers.
3. Build and tests are green.
4. Package version is 0.5.0.
5. README explicitly documents SurrealDB v3 requirement.

## Suggested Commit Strategy

1. Commit A: Metadata typed extraction refactor.
2. Commit B: Version bump and README compatibility update.
3. Optional squash for release branch if maintainers prefer a single change set.
