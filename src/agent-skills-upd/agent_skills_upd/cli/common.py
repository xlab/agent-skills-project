"""Shared CLI utilities for skill-upd, command-upd, and agent-upd."""

import random
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

import typer
import yaml
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

console = Console()

# Default environment configurations
DEFAULT_ENVIRONMENTS = {
    "claude": {
        "skill_dir": ".claude/skills",
        "command_dir": ".claude/commands",
        "agent_dir": ".claude/agents",
        "global_skill_dir": ".claude/skills",
    },
    "opencode": {
        "skill_dir": ".opencode/skill",
        "command_dir": ".opencode/command",
        "agent_dir": ".opencode/agent",
        "global_skill_dir": ".config/opencode/skill",
        "global_command_dir": ".config/opencode/command",
        "global_agent_dir": ".config/opencode/agent",
    },
    "codex": {
        "skill_dir": ".codex/skills",
        "command_dir": ".codex/commands",
        "agent_dir": ".codex/agents",
    },
    # https://ampcode.com/news/agent-skills
    "amp": {
        "skill_dir": ".agents/skills",
        "global_skill_dir": ".config/agents/skills",
    },
    # ampcode is an alias to amp
    "ampcode": {
        "skill_dir": ".agents/skills",
        "global_skill_dir": ".config/agents/skills",
    },
    # https://docs.clawd.bot/tools/skills#skills
    "clawdbot": {
        "skill_dir": "skills",
        "global_skill_dir": ".config/clawdbot/skills",
    },
    # clawdis is the old name of clawdbot
    "clawdis": {
        "skill_dir": "skills",
        "global_skill_dir": ".config/clawdbot/skills",
    },
    # clawd is an alias to clawdbot
    "clawd": {
        "skill_dir": "skills",
        "global_skill_dir": ".config/clawdbot/skills",
    }
}


def get_environment_config(environment: str | None = None) -> dict:
    """Simple config loading - no caching, no complexity."""
    config_path = Path.home() / ".agent-resources-config.yaml"

    # Load user config if exists
    user_config: dict = {}
    if config_path.exists():
        with config_path.open("r") as file_handle:
            user_config = yaml.safe_load(file_handle) or {}

    # Merge with defaults - simple and straightforward
    environments = {**DEFAULT_ENVIRONMENTS, **user_config.get("environments", {})}

    # Default to claude if no environment specified
    env_name = environment or "claude"

    if env_name not in environments:
        raise typer.BadParameter(
            f"Unknown environment: '{env_name}'. Available: {', '.join(environments.keys())}"
        )

    return environments[env_name]


def parse_resource_ref(ref: str) -> tuple[str, str, str]:
    """
    Parse '<username>/<name>' into components, with optional host.

    Args:
        ref: Resource reference in format 'username/name', 'host/username/name',
             or a full URL like 'https://host/username/name(.git)'

    Returns:
        Tuple of (host, username, name)

    Raises:
        typer.BadParameter: If the format is invalid
    """
    ref = ref.strip()
    if not ref:
        raise typer.BadParameter("Resource reference cannot be empty.")

    host = "github.com"
    path = ref

    if "://" in ref:
        parsed = urlparse(ref)
        if not parsed.netloc:
            raise typer.BadParameter(
                f"Invalid format: '{ref}'. Expected: <username>/<name> or URL."
            )
        host = parsed.netloc
        path = parsed.path.lstrip("/")

    parts = [part for part in path.split("/") if part]
    if len(parts) == 3 and host == "github.com" and "." in parts[0]:
        host, username, name = parts
    elif len(parts) == 2:
        username, name = parts
    else:
        raise typer.BadParameter(
            f"Invalid format: '{ref}'. Expected: <username>/<name> or <host>/<username>/<name>"
        )

    if name.endswith(".git"):
        name = name[: -len(".git")]
    if not username or not name:
        raise typer.BadParameter(
            f"Invalid format: '{ref}'. Expected: <username>/<name> or <host>/<username>/<name>"
        )
    return host, username, name


def get_destination(
    resource_subdir: str,
    global_install: bool,
    custom_dest: str | None = None,
    environment: str | None = None,
) -> Path:
    """
    Get the destination directory for a resource.

    Args:
        resource_subdir: The subdirectory name (e.g., "skills", "commands", "agents")
        global_install: If True, install to home directory, else to current directory
        custom_dest: Optional custom destination path
        environment: Optional environment name (claude, opencode, codex)

    Returns:
        Path to the destination directory
    """
    if custom_dest:
        return Path(custom_dest).expanduser()

    # Get environment configuration
    env_config = get_environment_config(environment)

    # Build config key based on resource type and global flag
    prefix = "global_" if global_install else ""
    key = f"{prefix}{resource_subdir.rstrip('s')}_dir"  # "skills" -> "skill_dir"

    # Get the directory, fallback to non-global if global key doesn't exist
    env_dir = env_config.get(key, env_config[key.replace("global_", "")])

    # Determine base path
    base = Path.home() if global_install else Path.cwd()

    return base / env_dir


@contextmanager
def fetch_spinner():
    """Show spinner during fetch operation."""
    with Live(Spinner("dots", text="Fetching..."), console=console, transient=True):
        yield


def print_success_message(resource_type: str, host: str, name: str, username: str) -> None:
    """Print branded success message with rotating CTA."""
    console.print(f"✅ Added {resource_type} '{name}' via 🧩 agent-skills-upd", style="dim")

    host_visible = host + "/"
    if host == "github.com":
        host_visible = ""

    ctas = [
        f"💡 Create your own {resource_type} library on GitHub: uvx create-agent-skill-repo --github",
        "⭐ Star project: github.com/xlab/agent-skills-project",
        "🔭 Explore more skills: https://upd.dev/skills",
        f"📢 Share: uvx upd-{resource_type} {host_visible}{username}/{name}",
    ]
    console.print(random.choice(ctas), style="dim")
