import { dag, Directory, object, func } from "@dagger.io/dagger";
import YAML from "yaml";

const TRIVY =
  "aquasec/trivy@sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f";
const PYTHON =
  "python@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419";
const NODE =
  "node@sha256:4660b1ca8b28d6d1906fd644abe34b2ed81d15434d26d845ef0aced307cf4b6f";
const TOFU =
  "ghcr.io/opentofu/opentofu@sha256:ba827d1af675c3f522eb78e2b8098cc87daefb9ceb9d3c4b69d0a1bb6d272463";
const DIGEST = /^[a-z0-9][a-z0-9./:_-]*@sha256:[0-9a-f]{64}$/;
const CATEGORIES = new Set(["infrastructure", "software", "research"]);

type Project = {
  version: number;
  name: string;
  category: string;
  lifecycle: string;
  ci: {
    image: string;
    commands: string[];
    formatCommand?: string;
    trivySkipDirs?: string[];
    trivyBaseline?: string;
  };
};

@object()
export class WorkstreamCi {
  private async project(source: Directory, category: string): Promise<Project> {
    const document = YAML.parse(
      await source.file("project.yaml").contents(),
    ) as { workstream?: Project } & Project;
    const project = document.workstream ?? document;
    if (
      project.version !== 1 ||
      !project.name ||
      !CATEGORIES.has(project.category) ||
      project.category !== category ||
      !project.ci ||
      !DIGEST.test(project.ci.image) ||
      !Array.isArray(project.ci.commands) ||
      project.ci.commands.some(
        (command) => typeof command !== "string" || !command.trim(),
      ) ||
      (project.ci.formatCommand !== undefined &&
        (typeof project.ci.formatCommand !== "string" ||
          !project.ci.formatCommand.trim())) ||
      (project.ci.trivySkipDirs !== undefined &&
        (!Array.isArray(project.ci.trivySkipDirs) ||
          project.ci.trivySkipDirs.some((path) => typeof path !== "string"))) ||
      (project.ci.trivyBaseline !== undefined &&
        typeof project.ci.trivyBaseline !== "string")
    ) {
      throw new Error(
        "project.yaml does not satisfy the canonical workstream CI contract",
      );
    }
    return project;
  }

  private async trivy(
    source: Directory,
    skipDirs: string[] = [],
    baselinePath?: string,
  ): Promise<void> {
    const safePath = (path: string) =>
      /^[A-Za-z0-9._/-]+$/.test(path) &&
      !path.startsWith("/") &&
      !path.split("/").includes("..");
    if (skipDirs.some((path) => !safePath(path))) {
      throw new Error(
        "Trivy skip directories must be safe repository-relative paths",
      );
    }
    if (baselinePath && !safePath(baselinePath)) {
      throw new Error(
        "Trivy baseline must be a safe repository-relative JSON path",
      );
    }
    const skipArgs = [".git", ".terraform", ...skipDirs].flatMap((path) => [
      "--skip-dirs",
      path,
    ]);
    const base = dag
      .container()
      .from(TRIVY)
      .withEntrypoint([])
      .withDirectory("/src", source)
      .withWorkdir("/src")
      .withMountedCache(
        "/root/.cache/trivy",
        dag.cacheVolume("workstream-trivy"),
      );
    const assessed = base.withExec([
      "trivy",
      "fs",
      "--scanners",
      "vuln,misconfig",
      "--severity",
      "HIGH,CRITICAL",
      "--ignore-unfixed",
      "--exit-code",
      "0",
      "--format",
      "json",
      "--output",
      "/tmp/trivy-assessment.json",
      ...skipArgs,
      "/src",
    ]);
    const report = JSON.parse(
      await assessed.file("/tmp/trivy-assessment.json").contents(),
    ) as {
      Results?: Array<{
        Target?: string;
        Vulnerabilities?: Array<{
          VulnerabilityID?: string;
          PkgName?: string;
          InstalledVersion?: string;
        }>;
        Misconfigurations?: Array<{ ID?: string; AVDID?: string }>;
      }>;
    };
    const findings = (report.Results ?? [])
      .flatMap((result) => [
        ...(result.Vulnerabilities ?? []).map((finding) => ({
          kind: "vulnerability",
          target: result.Target ?? "",
          id: finding.VulnerabilityID ?? "",
          package: finding.PkgName ?? "",
          installedVersion: finding.InstalledVersion ?? "",
        })),
        ...(result.Misconfigurations ?? []).map((finding) => ({
          kind: "misconfiguration",
          target: result.Target ?? "",
          id: finding.AVDID ?? finding.ID ?? "",
          package: "",
          installedVersion: "",
        })),
      ])
      .sort((left, right) =>
        JSON.stringify(left).localeCompare(JSON.stringify(right)),
      );
    let accepted: typeof findings = [];
    if (baselinePath) {
      const baseline = JSON.parse(
        await source.file(baselinePath).contents(),
      ) as {
        version?: number;
        findings?: typeof findings;
      };
      if (
        baseline.version !== 1 ||
        !Array.isArray(baseline.findings) ||
        baseline.findings.some(
          (finding) =>
            !finding ||
            !["vulnerability", "misconfiguration"].includes(finding.kind) ||
            typeof finding.target !== "string" ||
            typeof finding.id !== "string" ||
            typeof finding.package !== "string" ||
            typeof finding.installedVersion !== "string",
        )
      ) {
        throw new Error("invalid Trivy security baseline");
      }
      accepted = baseline.findings
        .map((finding) => ({
          kind: finding.kind,
          target: finding.target,
          id: finding.id,
          package: finding.package,
          installedVersion: finding.installedVersion,
        }))
        .sort((left, right) =>
          JSON.stringify(left).localeCompare(JSON.stringify(right)),
        );
    }
    if (JSON.stringify(findings) !== JSON.stringify(accepted)) {
      throw new Error(
        "HIGH/CRITICAL findings differ from the reviewed Trivy baseline",
      );
    }
    await base
      .withExec([
        "trivy",
        "fs",
        "--scanners",
        "secret",
        "--severity",
        "HIGH,CRITICAL",
        "--exit-code",
        "1",
        ...skipArgs,
        "/src",
      ])
      .sync();
  }

  private async native(
    source: Directory,
    project: Project,
    commitSha: string,
  ): Promise<void> {
    if (project.ci.commands.length === 0) return;
    if (commitSha && !/^[0-9a-f]{40}$/.test(commitSha))
      throw new Error("commit SHA must be an exact lowercase Git revision");
    let container = dag
      .container()
      .from(project.ci.image)
      .withEntrypoint([])
      .withDirectory("/src", source)
      .withWorkdir("/src")
      .withEnvVariable("CI", "true")
      .withMountedCache(
        "/root/.cache",
        dag.cacheVolume(`workstream-${project.category}-cache`),
      );
    if (commitSha) {
      container = container
        .withoutFile("/src/.git")
        .withNewFile("/src/.git/HEAD", `${commitSha}\n`, { permissions: 0o444 })
        .withEnvVariable("CI_COMMIT_SHA", commitSha);
    }
    for (const command of project.ci.commands) {
      container = container.withExec(["sh", "-euc", command]);
    }
    if (project.ci.formatCommand) {
      container = container.withExec(["sh", "-euc", project.ci.formatCommand]);
    }
    await container.sync();
  }

  private async infrastructure(source: Directory): Promise<void> {
    const entries = new Set(await source.entries());
    const jobs: Promise<unknown>[] = [];
    if (entries.has("ansible")) {
      jobs.push(
        dag
          .container()
          .from(PYTHON)
          .withDirectory("/src", source)
          .withWorkdir("/src")
          .withExec([
            "python",
            "-m",
            "pip",
            "install",
            "ansible-core==2.19.1",
            "PyYAML==6.0.2",
          ])
          .withExec([
            "sh",
            "-euc",
            'set -- ansible/playbooks/*.yml; [ -e "$1" ] || exit 0; for playbook do ansible-playbook --syntax-check "$playbook" >/dev/null; done',
          ])
          .sync(),
      );
    }
    if (entries.has("opentofu")) {
      jobs.push(
        dag
          .container()
          .from(TOFU)
          .withEntrypoint([])
          .withDirectory("/src", source)
          .withWorkdir("/src")
          .withExec(["tofu", "fmt", "-check", "-recursive", "/src/opentofu"])
          .sync(),
      );
    }
    await Promise.all(jobs);
  }

  @func()
  async platform(source: Directory): Promise<string> {
    await Promise.all([
      this.trivy(source),
      dag
        .container()
        .from(PYTHON)
        .withDirectory("/src", source)
        .withWorkdir("/src")
        .withExec([
          "sh",
          "-euc",
          "apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*",
        ])
        .withExec(["python", "-m", "pip", "install", "PyYAML==6.0.2"])
        .withExec(["python", "-m", "unittest", "discover", "-s", "tests"])
        .sync(),
      dag
        .container()
        .from(NODE)
        .withDirectory("/src", source)
        .withWorkdir("/src")
        .withExec([
          "corepack",
          "yarn",
          "--cwd",
          ".github/actions/workstream-ci/dagger",
          "install",
          "--frozen-lockfile",
        ])
        .withExec([
          ".github/actions/workstream-ci/dagger/node_modules/.bin/prettier",
          "--check",
          ".github/workflows/*.yml",
          ".github/actions/workstream-ci/action.yml",
          ".github/actions/workstream-ci/dagger/dagger.json",
          ".github/actions/workstream-ci/dagger/package.json",
          ".github/actions/workstream-ci/dagger/tsconfig.json",
          ".github/actions/workstream-ci/dagger/src/index.ts",
          "workstreams/pi-extension/index.ts",
          "workstreams/**/*.{json,yml}",
          "renovate.json",
        ])
        .sync(),
    ]);
    return "account workstream platform validation passed";
  }

  @func()
  async validate(
    source: Directory,
    category: string,
    commitSha = "",
  ): Promise<string> {
    if (!CATEGORIES.has(category))
      throw new Error(`unsupported workstream category: ${category}`);
    const project = await this.project(source, category);
    const jobs: Promise<unknown>[] = [
      this.trivy(
        source,
        project.ci.trivySkipDirs ?? [],
        project.ci.trivyBaseline,
      ),
      this.native(source, project, commitSha),
    ];
    if (category === "infrastructure") jobs.push(this.infrastructure(source));
    await Promise.all(jobs);
    return `${project.name}: canonical ${category} validation passed`;
  }
}
