"""Generic resource fetcher for skills, commands, and agents."""

import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import frontmatter
import httpx

from agent_skills_upd.exceptions import (
    SkillUpdError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)


class ResourceType(Enum):
    """Type of resource to fetch."""

    SKILL = "skill"
    COMMAND = "command"
    AGENT = "agent"


@dataclass
class ResourceConfig:
    """Configuration for a resource type."""

    resource_type: ResourceType
    source_subdir: str  # e.g., ".claude/skills", ".claude/commands"
    dest_subdir: str  # e.g., "skills", "commands"
    is_directory: bool  # True for skills, False for commands/agents
    file_extension: str | None  # None for skills, ".md" for commands/agents


RESOURCE_CONFIGS: dict[ResourceType, ResourceConfig] = {
    ResourceType.SKILL: ResourceConfig(
        resource_type=ResourceType.SKILL,
        source_subdir=".claude/skills",
        dest_subdir="skills",
        is_directory=True,
        file_extension=None,
    ),
    ResourceType.COMMAND: ResourceConfig(
        resource_type=ResourceType.COMMAND,
        source_subdir=".claude/commands",
        dest_subdir="commands",
        is_directory=False,
        file_extension=".md",
    ),
    ResourceType.AGENT: ResourceConfig(
        resource_type=ResourceType.AGENT,
        source_subdir=".claude/agents",
        dest_subdir="agents",
        is_directory=False,
        file_extension=".md",
    ),
}

# Pattern-based search for different repository structures
RESOURCE_SEARCH_PATTERNS = {
    ResourceType.SKILL: [
        ".claude/skills/{name}/",  # Current (first for backward compat)
        "{name}/",  # Repo root skill directory
        "skills/{name}/",  # Anthropics pattern
        "skill/{name}/",  # opencode pattern
        "skills/.curated/{name}/",  # OpenAI pattern
        "skills/.experimental/{name}/",  # OpenAI pattern
    ],
    ResourceType.COMMAND: [
        ".claude/commands/{name}.md",  # Current
        "commands/{name}.md",
        "command/{name}.md",  # opencode pattern
    ],
    ResourceType.AGENT: [
        ".claude/agents/{name}.md",  # Current
        "agents/{name}.md",
        "agent/{name}.md",  # opencode pattern
    ],
}

# Name of the repository to fetch resources from
REPO_NAME = "agent-resources"


def find_root_skill_file(repo_dir: Path) -> Path | None:
    """Find a root-level SKILL.md file case-insensitively."""
    for path in sorted(repo_dir.iterdir(), key=lambda entry: entry.name.lower()):
        if path.is_file() and path.name.lower() == "skill.md":
            return path
    return None


def parse_frontmatter_name(skill_file: Path) -> tuple[str | None, str | None]:
    """Parse the skill name from frontmatter."""
    content = skill_file.read_text(encoding="utf-8")
    try:
        post = frontmatter.loads(content)
    except Exception:
        return None, "Root SKILL.md frontmatter is invalid."

    name = post.metadata.get("name") if post.metadata else None
    name_value = str(name).strip() if name is not None else ""
    if not name_value:
        return None, "Root SKILL.md frontmatter missing name."

    return name_value, None


def validate_repository_structure(repo_dir: Path) -> dict:
    """Simple validation that provides useful feedback."""
    patterns_found = []
    for pattern in [
        ".claude/skills",
        "skills",
        "skill",
        ".claude/commands",
        "commands",
        "command",
        ".claude/agents",
        "agents",
        "agent",
    ]:
        if (repo_dir / pattern).exists():
            patterns_found.append(pattern)

    suggestions = []
    if not patterns_found:
        suggestions.append("Repository doesn't match common agent-resources patterns.")
        suggestions.append("Expected: .claude/skills/, skills/, or skill/ directories.")

    return {"patterns_found": patterns_found, "suggestions": suggestions}


def find_resource_in_repo(
    repo_dir: Path, resource_type: ResourceType, name: str
) -> Path | None:
    """Simple pattern-based search - no caching, no complexity."""
    config = RESOURCE_CONFIGS[resource_type]

    for pattern in RESOURCE_SEARCH_PATTERNS[resource_type]:
        search_path = pattern.format(name=name)
        if config.file_extension and not search_path.endswith(config.file_extension):
            search_path += config.file_extension

        resource_path = repo_dir / search_path
        if resource_path.exists():
            return resource_path

    return None


def fetch_resource(
    username: str,
    name: str | None,
    dest: Path,
    resource_type: ResourceType,
    overwrite: bool = True,
    host: str = "github.com",
    repo: str = REPO_NAME,
) -> Path:
    """
    Fetch a resource from a user's agent-resources repo and copy it to dest.

    Args:
        username: GitHub (or alternative Git host) username
        name: Name of the resource to fetch (optional for root-level skills)
        dest: Destination directory (e.g., .claude/skills/, .claude/commands/)
        resource_type: Type of resource (SKILL, COMMAND, or AGENT)
        overwrite: Whether to overwrite existing resource
        host: Repository host (default: github.com)

    Returns:
        Path to the installed resource

    Raises:
        RepoNotFoundError: If the agent-resources repo doesn't exist
        ResourceNotFoundError: If the resource doesn't exist in the repo
        ResourceExistsError: If resource exists locally and overwrite=False
    """
    config = RESOURCE_CONFIGS[resource_type]

    resource_dest = None
    if name is not None:
        # Determine destination path
        if config.is_directory:
            resource_dest = dest / name
        else:
            resource_dest = dest / f"{name}{config.file_extension}"

        # Check if resource already exists locally
        if resource_dest.exists() and not overwrite:
            raise ResourceExistsError(
                f"{resource_type.value.capitalize()} '{name}' already exists at {resource_dest}\n"
                f"Use --overwrite to replace it."
            )

    # Download tarball
    tarball_url = f"https://{host}/{username}/{repo}/archive/refs/heads/main.tar.gz"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        tarball_path = tmp_path / "repo.tar.gz"

        # Download
        try:
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                response = client.get(tarball_url)
                if response.status_code == 404:
                    raise RepoNotFoundError(
                        f"Repository '{username}/{repo}' not found on {host}."
                    )
                response.raise_for_status()

                tarball_path.write_bytes(response.content)
        except httpx.HTTPStatusError as e:
            raise SkillUpdError(f"Failed to download repository: {e}")
        except httpx.RequestError as e:
            raise SkillUpdError(f"Network error: {e}")

        # Extract
        extract_path = tmp_path / "extracted"
        with tarfile.open(tarball_path, "r:gz") as tar:
            try:
                tar.extractall(extract_path, filter="data")
            except TypeError:
                tar.extractall(extract_path)

        # Find the resource in extracted content using pattern-based search
        # Tarball extracts to: <repo>-main/<patterns>
        repo_dir = extract_path / f"{repo}-main"

        resource_source = (
            find_resource_in_repo(repo_dir, resource_type, name) if name else None
        )
        root_skill_message = None
        root_skill_name = None
        if (
            resource_source is None
            and resource_type == ResourceType.SKILL
            and repo != REPO_NAME
        ):
            root_skill_file = find_root_skill_file(repo_dir)
            if root_skill_file is None:
                root_skill_message = (
                    "Root SKILL.md not found (case-insensitive) in repo root."
                )
            else:
                root_skill_name, root_skill_error = parse_frontmatter_name(
                    root_skill_file
                )
                if root_skill_error:
                    root_skill_message = root_skill_error
                else:
                    if name is None:
                        name = root_skill_name
                        resource_source = root_skill_file.parent
                    elif root_skill_name != name:
                        root_skill_message = (
                            "Root SKILL.md frontmatter name "
                            f"'{root_skill_name}' does not match requested '{name}'."
                        )
                    else:
                        resource_source = root_skill_file.parent

        if resource_source is None or not resource_source.exists():
            display_name = name or "<unspecified>"
            patterns_name = name or "<skill-name>"
            patterns_tried = [
                p.format(name=patterns_name)
                for p in RESOURCE_SEARCH_PATTERNS[resource_type]
            ]
            patterns_list = "\n".join([f"- {pattern}" for pattern in patterns_tried])

            validation = validate_repository_structure(repo_dir)

            error_msg = (
                f"{resource_type.value.capitalize()} '{display_name}' not found in {username}/{repo}.\n"
                f"Tried these locations:\n{patterns_list}\n"
            )

            if validation["suggestions"]:
                error_msg += "\nRepository structure issues:\n"
                error_msg += "\n".join([f"- {msg}" for msg in validation["suggestions"]])
                error_msg += "\n"
            elif validation["patterns_found"]:
                error_msg += (
                    f"\nFound directories: {', '.join(validation['patterns_found'])}\n"
                )

            if root_skill_message:
                error_msg += "\nManual repo override check:\n"
                error_msg += f"- {root_skill_message}\n"

            error_msg += (
                "\nQuick fixes:\n"
                "- Double-check the resource name\n"
                "- Try --repo REPO_NAME if using a different repository\n"
                "- Try --dest PATH for custom installation location\n"
                f"- Visit https://{host}/{username}/{repo} to verify the resource exists"
            )

            raise ResourceNotFoundError(error_msg)

        if resource_dest is None:
            if name is None:
                raise SkillUpdError("Skill name could not be determined.")
            if config.is_directory:
                resource_dest = dest / name
            else:
                resource_dest = dest / f"{name}{config.file_extension}"

            if resource_dest.exists() and not overwrite:
                raise ResourceExistsError(
                    f"{resource_type.value.capitalize()} '{name}' already exists at {resource_dest}\n"
                    f"Use --overwrite to replace it."
                )

        # Remove existing if overwriting
        if resource_dest.exists():
            if config.is_directory:
                shutil.rmtree(resource_dest)
            else:
                resource_dest.unlink()

        # Ensure destination parent exists
        dest.mkdir(parents=True, exist_ok=True)

        # Copy resource to destination
        if config.is_directory:
            shutil.copytree(str(resource_source), str(resource_dest))
        else:
            shutil.copy2(str(resource_source), str(resource_dest))

    return resource_dest
