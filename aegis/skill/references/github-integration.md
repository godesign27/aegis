# GitHub Integration

Instructions for fetching and processing GitHub repositories as the source of
truth baseline in comparison mode.

---

## Fetching the Baseline

### Via GitHub REST API (recommended for API-first deployment)

```python
import httpx

def fetch_repo_tree(owner: str, repo: str, branch: str = "main", token: str = None):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Fetch recursive file tree
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    resp = httpx.get(url, headers=headers)
    resp.raise_for_status()
    tree = resp.json()["tree"]

    # Filter to relevant file types only
    ui_extensions = {".tsx", ".ts", ".jsx", ".js", ".css", ".scss", ".json"}
    return [
        f for f in tree
        if f["type"] == "blob"
        and any(f["path"].endswith(ext) for ext in ui_extensions)
    ]

def fetch_file_content(owner: str, repo: str, path: str, branch: str = "main", token: str = None):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    resp = httpx.get(url, headers=headers)
    resp.raise_for_status()

    import base64
    content = resp.json()["content"]
    return base64.b64decode(content).decode("utf-8")
```

### Rate limits
- Unauthenticated: 60 requests/hour — only viable for very small repos
- Authenticated: 5,000 requests/hour — required for production use
- For large repos (>500 UI files), use the GitHub archive download endpoint instead
  of individual file fetches

### What to fetch
Always fetch these files from the baseline if they exist:
- `package.json` — installed dependencies and versions
- `tailwind.config.js` or `tailwind.config.ts` — token definitions
- `src/styles/globals.css` or equivalent — CSS custom properties
- All `.tsx`/`.jsx` files in `src/components/` — component inventory
- All `.ts`/`.js` files in `src/` root — utility and config files

Do not fetch:
- `node_modules/` (excluded by tree recursion)
- Build output directories (`dist/`, `build/`, `.next/`)
- Test fixtures unless the audit specifically includes test files
- Binary assets, images, fonts

---

## Performing the Diff

### File-level classification
Classify every file in the AI-generated project relative to the baseline:

```
ADDED    - file exists in AI output, not in baseline
MODIFIED - file exists in both, content differs
REMOVED  - file exists in baseline, not in AI output
UNCHANGED - file exists in both, content identical
```

Only ADDED and MODIFIED files are in scope for the audit.
REMOVED files should be flagged as INFO-level drift observations.

### Block-level diff (for MODIFIED files)
For each MODIFIED file, extract only the changed blocks using a unified diff:

```python
import difflib

def get_changed_blocks(original: str, modified: str, context_lines: int = 3):
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        lineterm='',
        n=context_lines
    ))
    return "".join(diff)
```

Pass only the changed blocks to the validation engine, not the entire modified file.
This prevents false positives from flagging pre-existing violations in the source repo.

### package.json diff
Always diff package.json separately and extract:
- Added dependencies (new in AI output)
- Removed dependencies (in baseline, not in AI output)
- Changed versions (same package, different version)

Report added dependencies as INFO unless they appear on the hallucination watchlist,
in which case report as CRITICAL or HIGH per the tool profile.

---

## Source URL Parsing

The API accepts `repo_url` in these formats:
- `https://github.com/owner/repo`
- `https://github.com/owner/repo/tree/branch-name`
- `github:owner/repo`
- `owner/repo` (shorthand, assumes github.com)

Parse the URL to extract `owner`, `repo`, and optionally `branch`.
Default branch is `main`; fall back to `master` if `main` returns 404.

```python
import re
from urllib.parse import urlparse

def parse_repo_url(url: str) -> dict:
    # Handle shorthand: owner/repo
    if re.match(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$', url):
        owner, repo = url.split('/')
        return {"owner": owner, "repo": repo, "branch": "main"}

    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')

    result = {"owner": parts[0], "repo": parts[1], "branch": "main"}

    # Handle /tree/branch-name in path
    if len(parts) >= 4 and parts[2] == "tree":
        result["branch"] = parts[3]

    return result
```

---

## Caching

For production deployments, cache the baseline repo tree to avoid redundant
API calls for the same repo + branch combination.

Cache key: `{owner}/{repo}@{branch}:{commit_sha}`
TTL: 1 hour (repos can be updated)

The commit SHA for the branch tip is available from:
`GET /repos/{owner}/{repo}/commits/{branch}` → `.sha`

Include the commit SHA in the audit report's `diff_summary.baseline_commit` field
for full traceability.
