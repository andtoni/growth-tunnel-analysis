#!/usr/bin/env python3
"""Sort one pull request into a lane from its diff.

The lane table is `lanes.json`, generated from `lanes.yml` beside this file.
Everything read from the pull request is data: no file of the proposed
revision is executed or used as configuration. Standard library only, because
this runs directly on the runner.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any

HERE = pathlib.Path(__file__).resolve().parent
ORDER = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4}
REPOSITORY_KEYS = {
    "platformPaths",
    "statefulPaths",
    "recordPaths",
    "codePaths",
    "standardPaths",
    "dataPaths",
    "raiseLabels",
}
MAX_FILES = 3000  # the GitHub files API stops here; a larger change is Platform


def load_table(path: pathlib.Path = HERE / "lanes.json") -> dict[str, Any]:
    table = json.loads(path.read_text())
    if table.get("version") != 1:
        raise SystemExit("unsupported lane table")
    return table


def glob(pattern: str) -> re.Pattern[str]:
    """The same glob dialect as the Dagger module: `**/`, `**`, `*`, `?`."""
    output, index = "^", 0
    while index < len(pattern):
        character = pattern[index]
        if character == "*":
            if pattern[index + 1 : index + 2] == "*":
                index += 1
                if pattern[index + 1 : index + 2] == "/":
                    index += 1
                    output += "(?:.*/)?"
                else:
                    output += ".*"
            else:
                output += "[^/]*"
        elif character == "?":
            output += "[^/]"
        else:
            output += re.escape(character)
        index += 1
    return re.compile(output + "$")


def matches(path: str, patterns: list[str]) -> bool:
    return any(glob(pattern).match(path) for pattern in patterns)


def repository_config(raw: str) -> dict[str, Any]:
    """Validate the caller's repository-specific lane inputs."""
    config = json.loads(raw) if raw.strip() else {}
    if not isinstance(config, dict) or set(config) - REPOSITORY_KEYS:
        raise SystemExit(f"invalid lane-config keys: {sorted(set(config) - REPOSITORY_KEYS)}")
    for key, value in config.items():
        if key == "raiseLabels":
            valid = isinstance(value, dict) and all(
                isinstance(name, str) and lane in (3, 4) for name, lane in value.items()
            )
        else:
            valid = isinstance(value, list) and all(
                isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9._/*?-]+", item) for item in value
            )
        if not valid:
            raise SystemExit(f"invalid lane-config value for {key}")
    return config


def file_lane(path: str, table: dict[str, Any], config: dict[str, Any], bot: bool) -> tuple[str, str]:
    """Return the lane one changed file reaches and the class that put it there.

    A repository's own classes are consulted before the shared table, so a
    repository can say that one of its paths is, say, code although the shared
    table would call it platform. Two things no repository input can lower:
    the protected files that define CI and policy themselves, and the shared
    stateful patterns (migrations and schema are stateful in every repository).
    """
    classes = table["classes"]
    if matches(path, classes["protected"]):
        return "4", "protected platform"
    if matches(path, config.get("platformPaths", [])):
        return "4", "repository platform"
    if matches(path, config.get("statefulPaths", [])):
        return "3", "repository stateful"
    if matches(path, classes["stateful"]):
        return "3", "stateful"
    if bot and matches(path, config.get("standardPaths", [])):
        return "1", "repository standard path"
    # A bot's dependency file is Standard wherever the repository keeps its code,
    # but not where the shared table says platform (an Ansible compose file).
    dependency = matches(path, classes["dependency"])
    if bot and dependency and not matches(path, classes["platform"]):
        return "1", "dependency file"
    if matches(path, config.get("recordPaths", [])):
        return "0", "repository record"
    if matches(path, config.get("codePaths", [])):
        return "2", "repository code"
    if matches(path, classes["platform"]):
        return "4", "platform"
    # A manifest, lockfile or Dockerfile is never a record, wherever it lives.
    if not dependency and matches(path, classes["record"]):
        return "0", "record"
    if matches(path, classes["code"]):
        return "2", "code"
    return "4", "unrecognised"


MAJOR_TITLE = re.compile(r"(\bto v?\d+( \[security\])?$)|(\(major\))", re.IGNORECASE)


def classify(change: dict[str, Any], table: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Classify a change described by plain data.

    change: author, commitAuthors, title, labels, emergencyBy, owner, files
    (each {path, previous?, lines}), truncated.
    """
    reasons: list[str] = []
    bot = change["author"] in table["bots"] and all(
        author == change["author"] for author in change["commitAuthors"]
    )
    if change["author"] in table["bots"] and not bot:
        reasons.append("a commit is not the bot's: treated as a human change")
    lane = "0"

    def raise_to(candidate: str, reason: str) -> None:
        nonlocal lane
        if ORDER[candidate] > ORDER[lane]:
            lane = candidate
            reasons.append(f"lane {candidate}: {reason}")

    if change.get("truncated") or not change["files"]:
        raise_to("4", "the changed-file list is empty or incomplete")
    by_class: dict[str, list[str]] = {}
    for item in change["files"]:
        for path in filter(None, (item["path"], item.get("previous"))):
            reached, why = file_lane(path, table, config, bot)
            by_class.setdefault(f"{reached}:{why}", []).append(path)
    for key in sorted(by_class, key=lambda key: -ORDER[key[0]]):
        reached, why = key.split(":", 1)
        sample = ", ".join(by_class[key][:3]) + (" ..." if len(by_class[key]) > 3 else "")
        raise_to(reached, f"{why} ({sample})")
    data_lines = sum(
        item["lines"] for item in change["files"] if matches(item["path"], config.get("dataPaths", []))
    )
    if data_lines > table["dataLinesLimit"]:
        raise_to("3", f"{data_lines} changed lines under data paths (limit {table['dataLinesLimit']})")
    if bot and MAJOR_TITLE.search(change["title"].strip()):
        raise_to("3", "major update")
    raises = {**table["labels"]["raise"], **config.get("raiseLabels", {})}
    for label in sorted(change["labels"]):
        if label in raises:
            raise_to(str(raises[label]), f"label {label}")
    if not bot and lane == "1":
        lane = "2"
    if bot and lane == "2":
        # The reviewer refuses bot authors, so a bot change to code has no review to wait for.
        raise_to("4", "a bot change outside dependency files")
    underlying = lane
    emergency = table["labels"]["emergency"] in change["labels"]
    if emergency and change.get("emergencyBy") == change["owner"]:
        lane = "E"
        reasons.append(f"emergency label set by {change['owner']}; lane {underlying} checks run after merge")
    elif emergency:
        reasons.append(
            f"emergency label ignored: set by {change.get('emergencyBy') or 'unknown'}, not {change['owner']}"
        )
    review = "none" if bot or lane in ("0", "1", "E") else ("deep" if lane in ("3", "4") else "standard")
    return {
        "lane": lane,
        "underlying": underlying,
        "name": table["lanes"][lane]["name"],
        "bot": bot,
        "review": review,
        "reasons": reasons,
    }


def unreadable(table: dict[str, Any], why: str) -> dict[str, Any]:
    return {
        "lane": "4",
        "underlying": "4",
        "name": table["lanes"]["4"]["name"],
        "bot": False,
        "review": "deep",
        "reasons": [f"lane 4: the pull request could not be read ({why})"],
    }


class GitHub:
    def __init__(self, token: str, api: str = "https://api.github.com") -> None:
        self.token, self.api = token, api

    def request(self, method: str, path: str, body: Any = None) -> Any:
        request = urllib.request.Request(
            f"{self.api}{path}",
            method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
        return json.loads(payload) if payload else None

    def pages(self, path: str, limit: int = MAX_FILES) -> list[Any]:
        items: list[Any] = []
        page = 1
        while len(items) < limit:
            batch = self.request("GET", f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
            items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return items


def describe(github: GitHub, repository: str, number: int, emergency: str = "emergency") -> dict[str, Any]:
    """Read the facts the classifier uses, fresh from the API."""
    pull = github.request("GET", f"/repos/{repository}/pulls/{number}")
    files = github.pages(f"/repos/{repository}/pulls/{number}/files")
    commits = github.pages(f"/repos/{repository}/pulls/{number}/commits", 250)
    labels = [label["name"] for label in pull["labels"]]
    emergency_by = None
    if emergency in labels:
        events = github.pages(f"/repos/{repository}/issues/{number}/events", 1000)
        for event in events:
            if event.get("event") == "labeled" and event.get("label", {}).get("name") == emergency:
                emergency_by = (event.get("actor") or {}).get("login")
    return {
        "author": pull["user"]["login"],
        "commitAuthors": [(commit.get("author") or {}).get("login") or "" for commit in commits],
        "title": pull["title"],
        "labels": labels,
        "emergencyBy": emergency_by,
        "owner": repository.split("/")[0],
        "files": [
            {
                "path": item["filename"],
                "previous": item.get("previous_filename"),
                "lines": item.get("additions", 0) + item.get("deletions", 0),
            }
            for item in files
        ],
        "truncated": len(files) >= MAX_FILES or pull.get("changed_files", 0) != len(files),
    }


def apply_label(github: GitHub, repository: str, number: int, labels: list[str], lane: str) -> None:
    """Record the lane on the pull request as exactly one `lane-*` label."""
    wanted = f"lane-{lane}"
    for label in labels:
        if label.startswith("lane-") and label != wanted:
            try:
                github.request("DELETE", f"/repos/{repository}/issues/{number}/labels/{label}")
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
    if wanted not in labels:
        github.request("POST", f"/repos/{repository}/issues/{number}/labels", {"labels": [wanted]})


def emit(result: dict[str, Any]) -> None:
    outputs = {"lane": result["lane"], "underlying": result["underlying"], "review": result["review"]}
    with open(os.environ["GITHUB_OUTPUT"], "a") as handle:
        for key, value in outputs.items():
            handle.write(f"{key}={value}\n")
    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a") as handle:
        handle.write(f"### Lane {result['lane']} ({result['name']})\n\n")
        handle.write(f"Review: {result['review']}.\n\n")
        for reason in result["reasons"]:
            handle.write(f"- {reason}\n")
    print(json.dumps(result, indent=2))


def main() -> int:
    table = load_table()
    config = repository_config(os.environ.get("LANE_CONFIG", ""))
    event = json.loads(pathlib.Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    pull = event.get("pull_request")
    if not pull:
        # Weekly assurance and manual dispatch: every lane at full stage.
        emit(
            {"lane": "full", "underlying": "full", "name": "Full assurance", "bot": False,
             "review": "none", "reasons": ["not a pull request: full stage"]},
        )
        return 0
    repository = os.environ["GITHUB_REPOSITORY"]
    github = GitHub(os.environ["GH_TOKEN"], os.environ.get("GITHUB_API_URL", "https://api.github.com"))
    try:
        change = describe(github, repository, pull["number"], table["labels"]["emergency"])
        result = classify(change, table, config)
    except (urllib.error.URLError, KeyError, TypeError, ValueError) as error:
        # Fail closed: a change that cannot be read gets every check and the deep review.
        change = None
        result = unreadable(table, f"{type(error).__name__}: {error}")
    if change is not None and os.environ.get("LANE_LABEL", "true") == "true":
        try:
            apply_label(github, repository, pull["number"], change["labels"], result["lane"])
        except urllib.error.URLError as error:
            result["reasons"].append(f"the lane label could not be written ({error})")
    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
