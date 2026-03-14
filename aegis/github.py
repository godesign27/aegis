"""GitHub API client for Aegis comparison mode.

Fetches repository file trees and content to establish the baseline
against which AI-generated code is diffed.

Design: all methods are async and use httpx. The client is designed to
be injected where needed rather than used as a global singleton.
"""
from __future__ import annotations

import base64
import logging
from urllib.parse import urlparse

import httpx

from aegis.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


# ---------------------------------------------------------------------------
# URL parser
# ---------------------------------------------------------------------------


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (owner, repo) from a GitHub URL.

    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch
    """
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(path_parts) < 2:
        raise ValueError(f"Cannot parse owner/repo from GitHub URL: {url}")
    owner = path_parts[0]
    repo = path_parts[1].removesuffix(".git")
    return owner, repo


# ---------------------------------------------------------------------------
# GitHub client
# ---------------------------------------------------------------------------


class GitHubClient:
    """Async GitHub API client for fetching repo content."""

    def __init__(self, token: str | None = None):
        self.token = token or settings.github_token
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self._headers["Authorization"] = f"Bearer {self.token}"

    async def fetch_tree(
        self, owner: str, repo: str, branch: str = "main", recursive: bool = True
    ) -> list[dict]:
        """Fetch the full file tree for a repo branch.

        Returns a list of tree entry dicts:
        [{"path": "src/components/Button.tsx", "type": "blob", "sha": "...", "size": 1234}]
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
        params = {"recursive": "1"} if recursive else {}

        async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        tree = data.get("tree", [])
        # Return only blob entries (actual files), not tree entries (dirs)
        return [entry for entry in tree if entry.get("type") == "blob"]

    async def fetch_file(
        self, owner: str, repo: str, path: str, branch: str = "main"
    ) -> str:
        """Fetch the decoded content of a single file.

        Returns the file content as a string.
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": branch}

        async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return data.get("content", "")

    async def fetch_repo_files(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        extensions: tuple[str, ...] = (".tsx", ".ts", ".jsx", ".js", ".css", ".json"),
        max_files: int = 100,
    ) -> dict[str, str]:
        """Fetch all relevant source files from a repo.

        Returns a dict of {filepath: content}.
        Filters to only the provided extensions and caps at max_files to avoid
        runaway API usage.
        """
        tree = await self.fetch_tree(owner, repo, branch)

        # Filter to relevant file types
        relevant = [
            entry for entry in tree
            if any(entry["path"].endswith(ext) for ext in extensions)
        ][:max_files]

        logger.info(
            f"Fetching {len(relevant)} files from {owner}/{repo}@{branch}"
        )

        results: dict[str, str] = {}
        for entry in relevant:
            try:
                content = await self.fetch_file(owner, repo, entry["path"], branch)
                results[entry["path"]] = content
            except Exception as e:
                logger.warning(f"Could not fetch {entry['path']}: {e}")

        return results


# ---------------------------------------------------------------------------
# Diff utilities
# ---------------------------------------------------------------------------


def compute_diff_summary(
    baseline: dict[str, str],
    generated: dict[str, str],
) -> dict:
    """Compute a structural diff between the baseline repo and AI-generated files.

    Returns a dict compatible with DiffSummary fields.
    """
    baseline_paths = set(baseline.keys())
    generated_paths = set(generated.keys())

    files_added = sorted(generated_paths - baseline_paths)
    files_removed = sorted(baseline_paths - generated_paths)
    common = baseline_paths & generated_paths
    files_modified = sorted(
        path for path in common if baseline[path] != generated[path]
    )
    files_unchanged = len(common) - len(files_modified)

    return {
        "files_added": files_added,
        "files_modified": files_modified,
        "files_removed": files_removed,
        "files_unchanged": files_unchanged,
    }


def get_changed_files(
    baseline: dict[str, str],
    generated: dict[str, str],
) -> dict[str, str]:
    """Return only the files that were added or modified by the AI.

    These are the files the agent should audit (not unchanged files).
    """
    baseline_paths = set(baseline.keys())
    generated_paths = set(generated.keys())

    changed: dict[str, str] = {}

    # Added files (new in AI output)
    for path in generated_paths - baseline_paths:
        changed[path] = generated[path]

    # Modified files (exist in both but content differs)
    for path in baseline_paths & generated_paths:
        if baseline[path] != generated[path]:
            changed[path] = generated[path]

    return changed
