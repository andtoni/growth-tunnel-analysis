export type Finding = {
  kind: "vulnerability" | "misconfiguration";
  target: string;
  id: string;
  package: string;
  installedVersion: string;
};

// A finding is the same finding while the same advisory affects the same
// package in the same file. The installed version is not part of its identity:
// an update that moves a package to another still-affected version adds nothing.
export function findingKey(finding: Finding): string {
  return JSON.stringify([
    finding.kind,
    finding.target,
    finding.id,
    finding.package,
  ]);
}

export function unacceptedFindings(
  found: Finding[],
  allowed: Set<string>,
): string[] {
  return [
    ...new Set(found.map(findingKey).filter((key) => !allowed.has(key))),
  ].sort();
}
