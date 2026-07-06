SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

.PHONY: help status check verify-env

help:
	@printf '%s\n' \
		'Targets:' \
		'  make status      Show current state and Git status' \
		'  make check       Verify project metadata, critical files, and Git hygiene' \
		'  make verify-env  Run pipeline environment check with optional dependencies'

status:
	@sed -n '1,180p' STATE.md
	@printf '\nGit status:\n'
	@git status --short --branch

check:
	uv run python scripts/check_project.py

verify-env:
	uv run --extra pipeline python verify_environment.py
