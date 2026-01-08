"""CLI tests for upd-skill behaviors."""

from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agent_skills_upd.cli.skill import app
from agent_skills_upd.fetcher import ClawdhubFetchResult, ResourceType


def test_clawd_slug_uses_upd_dev_prefix():
    """Slug + clawd env should map to upd.dev/clawdhub with repo override."""
    runner = CliRunner()

    with (
        patch("agent_skills_upd.cli.skill.fetch_resource") as mock_fetch,
        patch("agent_skills_upd.cli.skill.fetch_spinner", return_value=nullcontext()),
        patch("agent_skills_upd.cli.skill.print_success_message") as mock_print,
    ):
        mock_fetch.return_value = Path("weather")

        result = runner.invoke(app, ["steipete-weather", "--env", "clawd"])

        assert result.exit_code == 0
        args, kwargs = mock_fetch.call_args
        assert args[0] == "clawdhub"
        assert args[1] is None
        assert args[3] == ResourceType.SKILL
        assert kwargs["host"] == "upd.dev"
        assert kwargs["repo"] == "steipete-weather"

        print_args = mock_print.call_args[0]
        print_kwargs = mock_print.call_args[1]
        assert print_args[0] == "skill"
        assert print_args[1] == "upd.dev"
        assert print_args[2] == "weather"
        assert print_args[3] == "clawdhub"
        assert print_kwargs["share_name"] == "steipete-weather"


def test_clawdhub_format_uses_api_fetch():
    """clawdhub.com/<skill> should use the Clawdhub API flow."""
    runner = CliRunner()
    dest_path = Path.cwd() / ".claude" / "skills"

    with (
        patch("agent_skills_upd.cli.skill.fetch_clawdhub_skill") as mock_fetch,
        patch("agent_skills_upd.cli.skill.fetch_spinner", return_value=nullcontext()),
    ):
        mock_fetch.return_value = ClawdhubFetchResult(
            path=Path("weather"),
            old_version=None,
            new_version="1.2.3",
            was_existing=False,
        )

        result = runner.invoke(app, ["clawdhub.com/weather"])

        assert result.exit_code == 0
        assert "Installed version 1.2.3" in result.stdout
        args, kwargs = mock_fetch.call_args
        assert args[0] == "weather"
        assert args[1] == dest_path
        assert args[2] is True
        assert kwargs == {}


def test_overwrite_flag_accepts_false():
    """--overwrite=false should disable overwriting."""
    runner = CliRunner()

    with (
        patch("agent_skills_upd.cli.skill.fetch_clawdhub_skill") as mock_fetch,
        patch("agent_skills_upd.cli.skill.fetch_spinner", return_value=nullcontext()),
    ):
        mock_fetch.return_value = ClawdhubFetchResult(
            path=Path("weather"),
            old_version=None,
            new_version="1.2.3",
            was_existing=False,
        )

        result = runner.invoke(
            app,
            ["clawdhub.com/weather", "--overwrite=false"],
        )

        assert result.exit_code == 0
        args, kwargs = mock_fetch.call_args
        assert args[2] is False
        assert kwargs == {}
