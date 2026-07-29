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
## 2026-07-29 — Adopt lifecycle-aware category CI

**Decision:** Replace the v1 PR-only compatibility workflow with affected native lanes on pull requests and full repository assurance on protected `main` and schedules. Use the immutable account action, a trusted base contract, an exact proposed-source checkout, one stable `required` context, and PR-only cancellation.

**Evidence:** The account contract was merged and released at `c4de6273cba817990dac477d2a5796f79d4e4d5e`. This repository's migration passed both pull-request and full-stage Dagger canaries before delivery.

**Alternatives rejected:** Keep PR-only assurance, rerun every native command for every path, retain duplicate CI workflows, or allow proposed workflow policy to control privileged PR execution.

**Consequences:** Documentation-only changes retain shared security checks; affected source changes run repository-owned commands; protected `main` receives the full suite. Credential-bearing publication, deployment, and private-image assurance remain separate trusted workflows and never execute proposed PR code. The temporary `pull_request` bridge and `allow-legacy-contract` input are removed immediately after this migration reaches `main`.
