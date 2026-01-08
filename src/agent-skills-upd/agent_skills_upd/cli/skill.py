"""CLI for skill-upd command."""

from typing import Annotated
from urllib.parse import urlparse

import typer

from agent_skills_upd.cli.common import (
    fetch_spinner,
    get_destination,
    parse_resource_ref,
    print_success_message,
)
from agent_skills_upd.exceptions import (
    SkillUpdError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from agent_skills_upd.fetcher import (
    CLAWDHUB_HOST,
    ResourceType,
    fetch_clawdhub_skill,
    fetch_resource,
)

app = typer.Typer(
    add_completion=False,
    help="Update Claude Code skills from GitHub to your project.",
)


def parse_clawdhub_skill_ref(ref: str) -> str | None:
    """Parse clawdhub.com/<skill-name> or https://clawdhub.com/<skill-name>."""
    ref = ref.strip()
    if not ref:
        raise typer.BadParameter("Skill reference cannot be empty.")

    if ref.startswith("http://") or ref.startswith("https://"):
        parsed = urlparse(ref)
        if parsed.netloc != CLAWDHUB_HOST:
            return None
        slug = parsed.path.strip("/")
    elif ref.startswith(f"{CLAWDHUB_HOST}/"):
        slug = ref[len(f"{CLAWDHUB_HOST}/") :].strip("/")
    else:
        return None

    if not slug or "/" in slug:
        raise typer.BadParameter(
            f"Invalid format: '{ref}'. Expected: {CLAWDHUB_HOST}/<skill-name>"
        )
    return slug


def parse_overwrite_flag(value: str) -> bool:
    """Parse overwrite flag values like true/false."""
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise typer.BadParameter(
        f"Invalid value for --overwrite: '{value}'. Use true or false."
    )


@app.command()
def add(
    skill_ref: Annotated[
        str,
        typer.Argument(
            help=(
                "Skill to update in format: <username>/<skill-name> or "
                "<host>/<username>/<skill-name> or clawdhub.com/<skill-name>"
            ),
            metavar="USERNAME/SKILL-NAME",
        ),
    ],
    overwrite: Annotated[
        str,
        typer.Option(
            "--overwrite",
            help="Overwrite existing skill if it exists (use --overwrite=false to disable).",
            metavar="BOOL",
        ),
    ] = "true",
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/.",
        ),
    ] = False,
    repo: Annotated[
        str,
        typer.Option(
            "--repo",
            help="Repository name to fetch from (default: agent-resources).",
        ),
    ] = "agent-resources",
    dest: Annotated[
        str,
        typer.Option(
            "--dest",
            help="Custom destination path.",
        ),
    ] = "",
    environment: Annotated[
        str,
        typer.Option(
            "--env",
            help="Target environment (claude, opencode, codex, amp, clawdbot).",
        ),
    ] = "",
) -> None:
    """
    Update a skill from a GitHub user's agent-resources repository.

    The skill will be copied to .claude/skills/<skill-name>/ in the current
    directory (or ~/.claude/skills/ with --global).

    Example:
        skill-upd kasperjunge/analyze-paper
        skill-upd kasperjunge/analyze-paper --global
    """
    try:
        overwrite_value = parse_overwrite_flag(overwrite)
        clawd_envs = {"clawd", "clawdbot", "clawdis"}
        clawdhub_slug = parse_clawdhub_skill_ref(skill_ref)
        if clawdhub_slug:
            host = CLAWDHUB_HOST
            username = ""
            skill_name = clawdhub_slug
            use_clawdhub = True
        elif environment in clawd_envs and "/" not in skill_ref:
            host = "upd.dev"
            username = "clawdhub"
            skill_name = None
            repo = skill_ref
            use_clawdhub = False
        else:
            host, username, skill_name = parse_resource_ref(skill_ref)
            use_clawdhub = False
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    dest_path = get_destination(
        "skills",
        global_install,
        dest if dest else None,
        environment if environment else None,
    )
    scope = "user" if global_install else "project"

    try:
        with fetch_spinner():
            if use_clawdhub:
                clawdhub_result = fetch_clawdhub_skill(
                    skill_name,
                    dest_path,
                    overwrite_value,
                )
            else:
                skill_path = fetch_resource(
                    username,
                    skill_name,
                    dest_path,
                    ResourceType.SKILL,
                    overwrite_value,
                    host=host,
                    repo=repo,
                )
        if use_clawdhub:
            if clawdhub_result.was_existing:
                old_version = clawdhub_result.old_version or "unknown"
                typer.echo(
                    f"🔄 Updated from {old_version} -> {clawdhub_result.new_version}"
                )
            else:
                typer.echo(f"✅ Installed version {clawdhub_result.new_version}")
        else:
            skill_name = skill_path.name
            print_success_message(
                "skill", host, skill_name, username, share_name=repo
            )
    except RepoNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ResourceNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ResourceExistsError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except SkillUpdError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
