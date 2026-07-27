# Decisions

## 2026-07-27 — Adopt the account workstream standard

**Decision:** Use the immutable `andtoni/.github` action for the shared Dagger, Trivy, and Zizmor admission gate; retain repository-native checks for project-specific validation; use hosted Semgrep Managed Scans, hosted Renovate, and native Codex Smart Review.

**Evidence:** The rollout pull request executes the shared and native checks against this repository, with HIGH/CRITICAL Trivy debt accepted only through an exact reviewed baseline where declared.

**Alternatives rejected:** Duplicated repository-local security workflows, self-hosted Semgrep or Renovate, blanket vulnerability bypasses, and custom Codex automation.

**Consequences:** New or changed security findings fail closed, shared action revisions remain immutable, native project checks remain authoritative for domain behavior, and GitHub protected-branch auto-merge may merge only after all required evidence passes.

## 2026-07-27 — Vendor the account CI action for the public repository

**Decision:** Keep `andtoni/.github` private and vendor its reviewed workstream action into this public repository. The workflow invokes the repository-local copy; the account repository remains the source authority for reviewed updates.

**Evidence:** GitHub does not permit a public repository workflow to execute an action from a private repository. Renovate PR runs failed during job setup before Dagger could start.

**Alternatives rejected:** Making account policy public, making this published research repository private, or removing the canonical admission gate.

**Consequences:** Public CI works without exposing private account policy. Updates to the vendored action require an explicit reviewed synchronization.
