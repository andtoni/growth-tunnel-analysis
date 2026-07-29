import { dag, Directory, func, object } from "@dagger.io/dagger";
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
const SHA = /^[0-9a-f]{40}$/;
const CATEGORIES = new Set(["infrastructure", "software", "research"]);
const STAGES = new Set(["pull-request", "full"]);

type Lane = {
  name: string;
  image: string;
  paths: string[];
  setupCommands: string[];
  pullRequestCommands: string[];
  fullCommands: string[];
};
type Project = {
  version: number;
  name: string;
  category: string;
  lifecycle: string;
  ci: {
    lanes: Lane[];
    fullOnPaths?: string[];
    noNativePaths?: string[];
    trivySkipDirs?: string[];
    trivyBaseline?: string;
  };
};

type Finding = {
  kind: "vulnerability" | "misconfiguration";
  target: string;
  id: string;
  package: string;
  installedVersion: string;
};

function strings(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.every((item) => typeof item === "string" && item.trim())
  );
}

function safeRelativePath(path: string): boolean {
  return (
    /^[A-Za-z0-9._/-]+$/.test(path) &&
    !path.startsWith("/") &&
    !path.split("/").includes("..")
  );
}

function safeGlob(pattern: string): boolean {
  return (
    /^[A-Za-z0-9._/*?-]+$/.test(pattern) &&
    !pattern.startsWith("/") &&
    !pattern.split("/").includes("..")
  );
}

function glob(pattern: string): RegExp {
  let output = "^";
  for (let index = 0; index < pattern.length; index += 1) {
    const character = pattern[index];
    if (character === "*") {
      if (pattern[index + 1] === "*") {
        index += 1;
        if (pattern[index + 1] === "/") {
          index += 1;
          output += "(?:.*/)?";
        } else {
          output += ".*";
        }
      } else {
        output += "[^/]*";
      }
    } else if (character === "?") {
      output += "[^/]";
    } else {
      output += character.replace(/[|\\{}()[\]^$+?.]/g, "\\$&");
    }
  }
  return new RegExp(`${output}$`);
}

function matches(paths: string[], patterns: string[]): boolean {
  return paths.some((path) =>
    patterns.some((pattern) => glob(pattern).test(path)),
  );
}

function changedFiles(encoded: string): string[] {
  if (!encoded) return [];
  const decoded = Buffer.from(encoded, "base64").toString("utf8");
  if (Buffer.from(decoded, "utf8").toString("base64") !== encoded) {
    throw new Error("changed files must be canonical base64-encoded UTF-8");
  }
  const files = decoded.split("\0");
  if (files.at(-1) === "") files.pop();
  if (!files.length || files.some((path) => !path)) {
    throw new Error("changed files must be a non-empty NUL-delimited list");
  }
  return files;
}

@object()
export class WorkstreamCi {
  private async project(
    contract: Directory,
    category: string,
  ): Promise<Project> {
    const document = YAML.parse(
      await contract.file("project.yaml").contents(),
    ) as {
      workstream?: Project;
    } & Project;
    const project = document.workstream ?? document;
    const ci = project?.ci;
    if (
      project?.version !== 1 ||
      !project.name ||
      !/^[a-z0-9][a-z0-9-]*$/.test(project.name) ||
      !CATEGORIES.has(project.category) ||
      project.category !== category ||
      !ci ||
      !Array.isArray(ci.lanes) ||
      !ci.lanes.length ||
      new Set(ci.lanes.map((lane) => lane?.name)).size !== ci.lanes.length ||
      ci.lanes.some(
        (lane) =>
          !lane ||
          !/^[a-z][a-z0-9-]*$/.test(lane.name) ||
          !DIGEST.test(lane.image) ||
          !strings(lane.paths) ||
          !lane.paths.length ||
          !strings(lane.setupCommands) ||
          !strings(lane.pullRequestCommands) ||
          !strings(lane.fullCommands) ||
          lane.paths.some((path) => !safeGlob(path)),
      ) ||
      (ci.fullOnPaths !== undefined &&
        (!strings(ci.fullOnPaths) ||
          ci.fullOnPaths.some((path) => !safeGlob(path)))) ||
      (ci.noNativePaths !== undefined &&
        (!strings(ci.noNativePaths) ||
          ci.noNativePaths.some((path) => !safeGlob(path)))) ||
      (ci.trivySkipDirs !== undefined &&
        (!strings(ci.trivySkipDirs) ||
          ci.trivySkipDirs.some((path) => !safeRelativePath(path)))) ||
      (ci.trivyBaseline !== undefined &&
        (typeof ci.trivyBaseline !== "string" ||
          !safeRelativePath(ci.trivyBaseline)))
    ) {
      throw new Error(
        "project.yaml does not satisfy the canonical staged CI contract",
      );
    }
    return project;
  }

  private async trivy(source: Directory, project: Project): Promise<void> {
    const skipArgs = [
      ".git",
      ".terraform",
      ...(project.ci.trivySkipDirs ?? []),
    ].flatMap((path) => ["--skip-dirs", path]);
    const cache = dag.cacheVolume(`workstream-${project.name}-trivy`);
    const base = dag
      .container()
      .from(TRIVY)
      .withEntrypoint([])
      .withDirectory("/src", source)
      .withWorkdir("/src")
      .withMountedCache("/root/.cache/trivy", cache);
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
    const findings: Finding[] = (report.Results ?? [])
      .flatMap((result) => [
        ...(result.Vulnerabilities ?? []).map((finding) => ({
          kind: "vulnerability" as const,
          target: result.Target ?? "",
          id: finding.VulnerabilityID ?? "",
          package: finding.PkgName ?? "",
          installedVersion: finding.InstalledVersion ?? "",
        })),
        ...(result.Misconfigurations ?? []).map((finding) => ({
          kind: "misconfiguration" as const,
          target: result.Target ?? "",
          id: finding.AVDID ?? finding.ID ?? "",
          package: "",
          installedVersion: "",
        })),
      ])
      .sort((left, right) =>
        JSON.stringify(left).localeCompare(JSON.stringify(right)),
      );
    let accepted: Finding[] = [];
    if (project.ci.trivyBaseline) {
      const baseline = JSON.parse(
        await source.file(project.ci.trivyBaseline).contents(),
      ) as { version?: number; findings?: Finding[] };
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

  private async lane(
    source: Directory,
    project: Project,
    lane: Lane,
    stage: string,
    commitSha: string,
    files: string[],
  ): Promise<void> {
    const commands = [
      ...lane.setupCommands,
      ...lane.pullRequestCommands,
      ...(stage === "full" ? lane.fullCommands : []),
    ];
    if (!commands.length) return;
    let container = dag
      .container()
      .from(lane.image)
      .withEntrypoint([])
      .withDirectory("/src", source)
      .withWorkdir("/src")
      .withEnvVariable("CI", "true")
      .withEnvVariable("CI_STAGE", stage)
      .withEnvVariable("CI_COMMIT_SHA", commitSha)
      .withNewFile("/tmp/changed-files.json", JSON.stringify(files), {
        permissions: 0o444,
      })
      .withEnvVariable("CI_CHANGED_FILES_FILE", "/tmp/changed-files.json")
      .withMountedCache(
        "/root/.cache",
        dag.cacheVolume(`workstream-${project.name}-${lane.name}`),
      );
    for (const command of commands) {
      container = container.withExec(["sh", "-euc", command]);
    }
    await container.sync();
  }

  private async infrastructure(
    source: Directory,
    stage: string,
    files: string[],
    forceAll: boolean,
  ): Promise<void> {
    const entries = new Set(await source.entries());
    const full = stage === "full" || forceAll;
    const jobs: Promise<unknown>[] = [];
    if (entries.has("ansible") && (full || matches(files, ["ansible/**"]))) {
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
            'for playbook in ansible/playbooks/*.yml ansible/playbooks/*.yaml; do [ -e "$playbook" ] || continue; ansible-playbook --syntax-check "$playbook" >/dev/null; done',
          ])
          .sync(),
      );
    }
    if (entries.has("opentofu") && (full || matches(files, ["opentofu/**"]))) {
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
    const canonicalSource = dag.directory().withNewFile(
      "project.yaml",
      `workstream:
  version: 1
  name: canonical-canary
  category: software
  lifecycle: active
  ci:
    lanes:
      - name: application
        image: ${NODE}
        paths: ["**"]
        setupCommands: []
        pullRequestCommands: []
        fullCommands: []
`,
    );
    await Promise.all([
      this.validate(
        canonicalSource,
        canonicalSource,
        "software",
        "full",
        "a".repeat(40),
      ),
      this.trivy(source, {
        version: 1,
        name: "platform",
        category: "software",
        lifecycle: "active",
        ci: {
          lanes: [
            {
              name: "platform",
              image: NODE,
              paths: ["**"],
              setupCommands: [],
              pullRequestCommands: [],
              fullCommands: [],
            },
          ],
        },
      }),
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
    contract: Directory,
    category: string,
    stage: string,
    commitSha: string,
    changedFilesB64 = "",
  ): Promise<string> {
    if (
      !CATEGORIES.has(category) ||
      !STAGES.has(stage) ||
      !SHA.test(commitSha)
    ) {
      throw new Error("invalid category, stage, or commit SHA");
    }
    const project = await this.project(contract, category);
    if (stage === "pull-request") {
      const proposed = await this.project(source, category);
      if (proposed.name !== project.name) {
        throw new Error(
          "proposed project identity differs from the trusted contract",
        );
      }
    }
    const files = stage === "full" ? [] : changedFiles(changedFilesB64);
    const all =
      stage === "full" || matches(files, project.ci.fullOnPaths ?? []);
    const noNative =
      !all &&
      files.length > 0 &&
      matches(files, project.ci.noNativePaths ?? []) &&
      files.every((path) => matches([path], project.ci.noNativePaths ?? []));
    const affected = project.ci.lanes.filter((lane) =>
      matches(files, lane.paths),
    );
    const lanes = all
      ? project.ci.lanes
      : noNative
        ? []
        : affected.length
          ? affected
          : project.ci.lanes;
    const effectiveStage = all ? "full" : stage;
    const jobs: Promise<unknown>[] = [
      this.trivy(source, project),
      ...lanes.map((lane) =>
        this.lane(source, project, lane, effectiveStage, commitSha, files),
      ),
    ];
    if (category === "infrastructure") {
      jobs.push(this.infrastructure(source, effectiveStage, files, all));
    }
    await Promise.all(jobs);
    return `${project.name}: ${stage} ${category} validation passed`;
  }
}
