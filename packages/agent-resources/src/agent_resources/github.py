"""GitHub CLI integration for creating and pushing repositories."""

import subprocess
from pathlib import Path


def check_gh_cli() -> bool:
    """Check if GitHub CLI is available and authenticated.

    Returns True if gh CLI is installed and authenticated, False otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_github_username() -> str | None:
    """Get the authenticated GitHub username.

    Returns the username if authenticated, None otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def create_github_repo(path: Path, repo_name: str = "agent-resources") -> str | None:
    """Create a GitHub repository and push the local repo.

    Args:
        path: Path to the local git repository
        repo_name: Name for the GitHub repository (default: agent-resources)

    Returns:
        The GitHub repo URL if successful, None otherwise.
    """
    try:
        # Create repo on GitHub (public by default)
        result = subprocess.run(
            [
                "gh",
                "repo",
                "create",
                repo_name,
                "--public",
                "--source",
                str(path),
                "--push",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Extract URL from output or construct it
        username = get_github_username()
        if username:
            return f"https://github.com/{username}/{repo_name}"

        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def repo_exists(repo_name: str = "agent-resources") -> bool:
    """Check if a repository with the given name already exists.

    Returns True if the repo exists, False otherwise.
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "view", repo_name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
