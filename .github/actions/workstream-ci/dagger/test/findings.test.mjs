import assert from "node:assert/strict";
import test from "node:test";
import { findingKey, unacceptedFindings } from "../src/findings.ts";

const finding = (overrides = {}) => ({
  kind: "vulnerability",
  target: "uv.lock",
  id: "CVE-2026-0001",
  package: "example",
  installedVersion: "1.0.0",
  ...overrides,
});
const allowed = (...findings) => new Set(findings.map(findingKey));

test("a finding already on the base revision is not new", () => {
  assert.deepEqual(unacceptedFindings([finding()], allowed(finding())), []);
});

test("an advisory absent from the base revision is new", () => {
  const added = finding({ id: "CVE-2026-0002" });
  assert.deepEqual(unacceptedFindings([finding(), added], allowed(finding())), [
    findingKey(added),
  ]);
});

test("moving a package to another affected version adds no finding", () => {
  assert.deepEqual(
    unacceptedFindings(
      [finding({ installedVersion: "1.0.1" })],
      allowed(finding()),
    ),
    [],
  );
});

test("the same advisory in another file or package is new", () => {
  for (const moved of [
    finding({ target: "other/uv.lock" }),
    finding({ package: "other" }),
    finding({ kind: "misconfiguration" }),
  ]) {
    assert.deepEqual(unacceptedFindings([moved], allowed(finding())), [
      findingKey(moved),
    ]);
  }
});

test("a fixed finding and an empty tree pass", () => {
  assert.deepEqual(unacceptedFindings([], allowed(finding())), []);
  assert.deepEqual(unacceptedFindings([], allowed()), []);
});

test("each new finding is reported once, in a stable order", () => {
  const second = finding({ id: "CVE-2026-0003" });
  const first = finding({ id: "CVE-2026-0002" });
  assert.deepEqual(unacceptedFindings([second, first, second], allowed()), [
    findingKey(first),
    findingKey(second),
  ]);
});
