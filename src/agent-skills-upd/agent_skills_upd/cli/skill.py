"""CLI for skill-upd command."""

from typing import Annotated

import typer

from agent_skills_upd.cli.common import fetch_spinner, get_destination, parse_resource_ref, print_success_message
from agent_skills_upd.exceptions import (
    SkillUpdError,
    RepoNotFoundError,
    ResourceExistsError,
    ResourceNotFoundError,
)
from agent_skills_upd.fetcher import ResourceType, fetch_resource

app = typer.Typer(
    add_completion=False,
    help="Update Claude Code skills from GitHub to your project.",
)


@app.command()
def add(
    skill_ref: Annotated[
        str,
        typer.Argument(
            help=(
                "Skill to update in format: <username>/<skill-name> or "
                "<host>/<username>/<skill-name>"
            ),
            metavar="USERNAME/SKILL-NAME",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing skill if it exists.",
        ),
    ] = False,
    global_install: Annotated[
        bool,
        typer.Option(
            "--global",
            "-g",
            help="Install to ~/.claude/ instead of ./.claude/",
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
        clawd_envs = {"clawd", "clawdbot", "clawdis"}
        if environment in clawd_envs and "/" not in skill_ref:
            host = "upd.dev"
            username = "clawdhub"
            skill_name = None
            repo = skill_ref
        else:
            host, username, skill_name = parse_resource_ref(skill_ref)
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
            skill_path = fetch_resource(
                username,
                skill_name,
                dest_path,
                ResourceType.SKILL,
                overwrite,
                host=host,
                repo=repo,
            )
        skill_name = skill_path.name
        print_success_message("skill", host, skill_name, username)
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
