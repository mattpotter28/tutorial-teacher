"""GitHub repository fetcher for Tutorial Teacher."""

import base64
import os
import re
from urllib.parse import urlparse

import requests


class RepoFetchError(Exception):
    """Error fetching repository contents."""
    pass


# Directories to skip
SKIP_DIRS = {
    'node_modules', '__pycache__', '.git', '.svn', '.hg',
    'dist', 'build', 'target', 'vendor', 'venv', '.venv',
    'env', '.env', 'coverage', '.coverage', '.pytest_cache',
    '.mypy_cache', '.tox', 'eggs', '*.egg-info', '.idea', '.vscode',
}

# File extensions to include
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.rb',
    '.java', '.kt', '.swift', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.php', '.vue', '.svelte', '.html', '.css', '.scss',
    '.json', '.yaml', '.yml', '.toml', '.md', '.rst', '.txt',
}

# Priority files to always include if present
PRIORITY_FILES = {
    'README.md', 'README.rst', 'README.txt', 'README',
    'package.json', 'pyproject.toml', 'setup.py', 'Cargo.toml',
    'go.mod', 'Gemfile', 'requirements.txt', 'Makefile',
    'main.py', 'app.py', 'index.js', 'index.ts', 'main.go',
}

# Max file size to fetch (50KB)
MAX_FILE_SIZE = 50 * 1024

# Max number of files to fetch content for
MAX_FILES = 50


def extract_repo_info(url: str) -> tuple[str, str]:
    """
    Extract owner and repo name from GitHub URL.

    Supports:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/branch
    - git@github.com:owner/repo.git
    """
    # Handle SSH URLs
    if url.startswith('git@github.com:'):
        path = url.replace('git@github.com:', '').replace('.git', '')
        parts = path.split('/')
        if len(parts) >= 2:
            return parts[0], parts[1]

    # Handle HTTPS URLs
    parsed = urlparse(url)

    if parsed.netloc not in ('github.com', 'www.github.com'):
        raise RepoFetchError(f"Not a GitHub URL: {url}")

    # Remove leading slash and .git suffix
    path = parsed.path.strip('/').replace('.git', '')

    # Split path and take first two parts (owner/repo)
    parts = path.split('/')
    if len(parts) < 2:
        raise RepoFetchError(f"Invalid GitHub repo URL: {url}")

    return parts[0], parts[1]


def _get_headers() -> dict:
    """Get headers for GitHub API requests."""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'tutorial-teacher',
    }

    token = os.environ.get('GITHUB_TOKEN')
    # Skip placeholder values
    if token and not token.startswith('your-'):
        headers['Authorization'] = f'token {token}'

    return headers


def _should_include_path(path: str) -> bool:
    """Check if a file path should be included."""
    parts = path.split('/')

    # Skip if any directory component is in skip list
    for part in parts[:-1]:  # All but the filename
        if part in SKIP_DIRS or part.startswith('.'):
            return False

    # Get filename and extension
    filename = parts[-1]
    _, ext = os.path.splitext(filename)

    # Include priority files
    if filename in PRIORITY_FILES:
        return True

    # Include files with allowed extensions
    if ext.lower() in CODE_EXTENSIONS:
        return True

    return False


def _fetch_tree(owner: str, repo: str, headers: dict) -> list[dict]:
    """Fetch the repository file tree."""
    url = f'https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1'

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 404:
        raise RepoFetchError(f"Repository not found: {owner}/{repo}")
    elif response.status_code == 401:
        raise RepoFetchError("Authentication required. Set GITHUB_TOKEN for private repos.")
    elif response.status_code == 403:
        # Check if it's rate limiting
        remaining = response.headers.get('X-RateLimit-Remaining', '')
        if remaining == '0':
            raise RepoFetchError(
                "GitHub rate limit exceeded. Set GITHUB_TOKEN in .env for higher limits."
            )
        raise RepoFetchError("Access denied. Check your GITHUB_TOKEN permissions.")
    elif response.status_code != 200:
        raise RepoFetchError(f"GitHub API error: {response.status_code}")

    data = response.json()
    return data.get('tree', [])


def _fetch_file_content(owner: str, repo: str, path: str, headers: dict) -> str | None:
    """Fetch content of a single file."""
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path}'

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        return None

    data = response.json()

    # Check size
    size = data.get('size', 0)
    if size > MAX_FILE_SIZE:
        return None

    # Decode content
    content = data.get('content', '')
    encoding = data.get('encoding', '')

    if encoding == 'base64':
        try:
            return base64.b64decode(content).decode('utf-8')
        except (UnicodeDecodeError, ValueError):
            return None

    return content


def fetch_repo_context(repo_url: str) -> str:
    """
    Fetch repository context for Claude.

    Returns a formatted string containing:
    - Repository structure (file tree)
    - Contents of key files

    Args:
        repo_url: GitHub repository URL

    Returns:
        Formatted string for inclusion in Claude's context

    Raises:
        RepoFetchError: If repository cannot be fetched
    """
    owner, repo = extract_repo_info(repo_url)
    headers = _get_headers()

    # Fetch file tree
    tree = _fetch_tree(owner, repo, headers)

    # Filter to relevant files
    files = []
    for item in tree:
        if item['type'] != 'blob':
            continue
        path = item['path']
        if _should_include_path(path):
            files.append({
                'path': path,
                'size': item.get('size', 0),
            })

    # Sort: priority files first, then by path
    def sort_key(f):
        filename = f['path'].split('/')[-1]
        is_priority = filename in PRIORITY_FILES
        return (not is_priority, f['path'])

    files.sort(key=sort_key)

    # Build output
    lines = [f"Repository: {owner}/{repo}", ""]

    # File tree
    lines.append("## File Structure")
    lines.append("```")
    for f in files:
        lines.append(f"  {f['path']}")
    lines.append("```")
    lines.append("")

    # Fetch content for top files
    lines.append("## Key Files")
    files_fetched = 0

    for f in files:
        if files_fetched >= MAX_FILES:
            break

        # Skip large files
        if f['size'] > MAX_FILE_SIZE:
            continue

        content = _fetch_file_content(owner, repo, f['path'], headers)
        if content is None:
            continue

        files_fetched += 1
        lines.append(f"\n### {f['path']}")
        lines.append("```")
        lines.append(content.rstrip())
        lines.append("```")

    return '\n'.join(lines)
