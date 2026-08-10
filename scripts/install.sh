#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
SKILLS_DIR="${REPO_ROOT}/skills"
AGENTS_DIR="${REPO_ROOT}/agents"
TEMPLATE_AGENTS_FILE="${REPO_ROOT}/templates/AGENTS.md"
PROJECT_DIR=""

if [[ $# -gt 1 ]]; then
  printf 'error: expected at most one project directory argument\n' >&2
  exit 2
fi

if [[ $# -eq 1 ]]; then
  if [[ ! -d "$1" ]]; then
    printf 'error: project directory does not exist: %s\n' "$1" >&2
    exit 2
  fi
  PROJECT_DIR="$(cd -- "$1" && pwd -P)"
fi

link_path() {
  local source_path="$1"
  local link_path="$2"
  local parent_dir
  parent_dir="$(dirname "${link_path}")"
  mkdir -p "${parent_dir}"

  if [[ -L "${link_path}" ]]; then
    if [[ "$(readlink "${link_path}")" == "${source_path}" ]]; then
      printf 'unchanged: %s -> %s\n' "${link_path}" "${source_path}"
      return
    fi
    ln -sfn "${source_path}" "${link_path}"
    printf 'updated:   %s -> %s\n' "${link_path}" "${source_path}"
    return
  fi

  if [[ -e "${link_path}" ]]; then
    printf 'skipped:   %s exists and is not a symlink\n' "${link_path}"
    return
  fi

  ln -s "${source_path}" "${link_path}"
  printf 'linked:    %s -> %s\n' "${link_path}" "${source_path}"
}

ensure_collection_directory() {
  local source_dir="$1"
  local destination_dir="$2"
  local parent_dir
  parent_dir="$(dirname "${destination_dir}")"
  mkdir -p "${parent_dir}"

  if [[ -L "${destination_dir}" ]]; then
    if [[ "$(readlink "${destination_dir}")" == "${source_dir}" ]]; then
      rm "${destination_dir}"
      mkdir -p "${destination_dir}"
      printf 'migrated:  %s from directory link to per-item links\n' "${destination_dir}"
      return 0
    fi
    printf 'skipped:   %s is a symlink to another location\n' "${destination_dir}"
    return 1
  fi

  if [[ -e "${destination_dir}" && ! -d "${destination_dir}" ]]; then
    printf 'skipped:   %s exists and is not a directory\n' "${destination_dir}"
    return 1
  fi

  mkdir -p "${destination_dir}"
}

link_collection() {
  local source_dir="$1"
  local destination_dir="$2"
  local item_kind="$3"
  local item

  if ! ensure_collection_directory "${source_dir}" "${destination_dir}"; then
    return
  fi

  if [[ "${item_kind}" == "directory" ]]; then
    for item in "${source_dir}"/*; do
      [[ -d "${item}" ]] || continue
      link_path "${item}" "${destination_dir}/$(basename "${item}")"
    done
  else
    for item in "${source_dir}"/*.md; do
      [[ -f "${item}" ]] || continue
      link_path "${item}" "${destination_dir}/$(basename "${item}")"
    done
  fi
}

link_collection "${SKILLS_DIR}" "${HOME}/.claude/skills" directory
link_collection "${SKILLS_DIR}" "${HOME}/.codex/skills" directory
link_collection "${SKILLS_DIR}" "${HOME}/.gemini/skills" directory
link_collection "${SKILLS_DIR}" "${HOME}/.antigravity/skills" directory
link_collection "${AGENTS_DIR}" "${HOME}/.claude/agents" file

if [[ -n "${PROJECT_DIR}" ]]; then
  link_path "${TEMPLATE_AGENTS_FILE}" "${PROJECT_DIR}/AGENTS.md"
  link_path "${TEMPLATE_AGENTS_FILE}" "${PROJECT_DIR}/CLAUDE.md"
  link_collection "${SKILLS_DIR}" "${PROJECT_DIR}/.claude/skills" directory
  link_collection "${AGENTS_DIR}" "${PROJECT_DIR}/.claude/agents" file

  if ! command -v python3 >/dev/null 2>&1; then
    printf 'error: Python 3 is required to build Cursor rules\n' >&2
    exit 1
  fi

  python3 "${SCRIPT_DIR}/build_cursor_rules.py" \
    --skills-dir "${SKILLS_DIR}" \
    --out-dir "${PROJECT_DIR}/.cursor/rules"
fi
