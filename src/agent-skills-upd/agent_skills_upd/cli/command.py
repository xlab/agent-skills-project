"""CLI for command-upd command."""

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
    help="Update Claude Code slash commands from GitHub to your project.",
)


@app.command()
def add(
    command_ref: Annotated[
        str,
        typer.Argument(
            help=(
                "Command to update in format: <username>/<command-name> or "
                "<host>/<username>/<command-name>"
            ),
            metavar="USERNAME/COMMAND-NAME",
        ),
    ],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite existing command if it exists.",
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
            help="Target environment (claude, opencode, codex).",
        ),
    ] = "",
) -> None:
    """
    Update a slash command from a GitHub user's agent-resources repository.

    The command will be copied to .claude/commands/<command-name>.md in the
    current directory (or ~/.claude/commands/ with --global).

    Example:
        command-upd kasperjunge/commit
        command-upd kasperjunge/review-pr --global
    """
    try:
        host, username, command_name = parse_resource_ref(command_ref)
    except typer.BadParameter as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    dest_path = get_destination(
        "commands",
        global_install,
        dest if dest else None,
        environment if environment else None,
    )
    scope = "user" if global_install else "project"

    try:
        with fetch_spinner():
            command_path = fetch_resource(
                username,
                command_name,
                dest_path,
                ResourceType.COMMAND,
                overwrite,
                host=host,
                repo=repo,
            )
        print_success_message("command", host, command_name, username)
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
