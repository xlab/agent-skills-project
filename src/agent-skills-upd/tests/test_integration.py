"""Integration tests that simulate real-world usage."""

import sys
import tempfile
import tarfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path for non-installed testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_skills_upd.cli.common import get_destination
from agent_skills_upd.exceptions import ResourceNotFoundError
from agent_skills_upd.fetcher import ResourceType, fetch_resource


def create_mock_repo_tarball(tmp_path: Path, repo_name: str, structure: str) -> bytes:
    """Create a mock GitHub tarball with specified structure."""
    repo_dir = tmp_path / f"{repo_name}-main"

    if structure == "claude":
        skill_dir = repo_dir / ".claude" / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill (Claude structure)")

        cmd_dir = repo_dir / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "test-cmd.md").write_text("# Test Command (Claude structure)")

    elif structure == "anthropic":
        skill_dir = repo_dir / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill (Anthropic structure)")

        cmd_dir = repo_dir / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "test-cmd.md").write_text("# Test Command (Anthropic structure)")

    elif structure == "opencode":
        skill_dir = repo_dir / "skill" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test Skill (OpenCode structure)")

        cmd_dir = repo_dir / "command"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "test-cmd.md").write_text("# Test Command (OpenCode structure)")

    tarball_path = tmp_path / "repo.tar.gz"
    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(repo_dir, arcname=f"{repo_name}-main")

    return tarball_path.read_bytes()


def test_backward_compatibility_claude_structure():
    """Test backward compatibility with .claude/skills structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        dest_path = tmp_path / "destination"

        tarball_bytes = create_mock_repo_tarball(
            tmp_path / "source", "agent-resources", "claude"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = tarball_bytes

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = fetch_resource(
                "testuser",
                "test-skill",
                dest_path,
                ResourceType.SKILL,
                overwrite=False,
                repo="agent-resources",
            )

            assert result.exists()
            assert result.name == "test-skill"
            assert (result / "SKILL.md").exists()
            content = (result / "SKILL.md").read_text()
            assert "Claude structure" in content


def test_anthropic_pattern_detection():
    """Test pattern detection for Anthropic-style repos (skills/)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        dest_path = tmp_path / "destination"

        tarball_bytes = create_mock_repo_tarball(
            tmp_path / "source", "skills", "anthropic"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = tarball_bytes

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = fetch_resource(
                "anthropic",
                "test-skill",
                dest_path,
                ResourceType.SKILL,
                overwrite=False,
                repo="skills",
            )

            assert result.exists()
            assert result.name == "test-skill"
            content = (result / "SKILL.md").read_text()
            assert "Anthropic structure" in content


def test_opencode_pattern_detection():
    """Test pattern detection for OpenCode-style repos (skill/)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        dest_path = tmp_path / "destination"

        tarball_bytes = create_mock_repo_tarball(
            tmp_path / "source", "codingagents", "opencode"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = tarball_bytes

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = fetch_resource(
                "opencode",
                "test-skill",
                dest_path,
                ResourceType.SKILL,
                overwrite=False,
                repo="codingagents",
            )

            assert result.exists()
            assert result.name == "test-skill"
            content = (result / "SKILL.md").read_text()
            assert "OpenCode structure" in content


def test_custom_destination():
    """Test custom destination path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        custom_dest = tmp_path / "my-custom" / "location"

        tarball_bytes = create_mock_repo_tarball(
            tmp_path / "source", "agent-resources", "claude"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = tarball_bytes

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            result = fetch_resource(
                "testuser",
                "test-skill",
                custom_dest,
                ResourceType.SKILL,
                overwrite=False,
                repo="agent-resources",
            )

            assert result.exists()
            assert str(custom_dest) in str(result)
            assert result.name == "test-skill"


def test_enhanced_error_messages():
    """Test that error messages show all attempted patterns."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        dest_path = tmp_path / "destination"

        repo_dir = tmp_path / "source" / "agent-resources-main"
        repo_dir.mkdir(parents=True)

        tarball_path = tmp_path / "repo.tar.gz"
        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(repo_dir, arcname="agent-resources-main")

        tarball_bytes = tarball_path.read_bytes()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = tarball_bytes

        with patch("httpx.Client") as mock_client:
            mock_client.return_value.__enter__.return_value.get.return_value = mock_response

            try:
                fetch_resource(
                    "testuser",
                    "nonexistent",
                    dest_path,
                    ResourceType.SKILL,
                    overwrite=False,
                    repo="agent-resources",
                )
                assert False, "Should have raised ResourceNotFoundError"
            except ResourceNotFoundError as exc:
                error_msg = str(exc)
                assert "Tried these locations:" in error_msg
                assert ".claude/skills/nonexistent" in error_msg
                assert "skills/nonexistent" in error_msg
                assert "skill/nonexistent" in error_msg
                assert "Quick fixes:" in error_msg
                assert "--repo" in error_msg
                assert "--dest" in error_msg


def test_amp_environment_destinations():
    """Test destination resolution for Amp environments."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        home_dir = tmp_path / "home"
        cwd_dir = tmp_path / "project"
        home_dir.mkdir()
        cwd_dir.mkdir()

        with (
            patch("agent_skills_upd.cli.common.Path.home", return_value=home_dir),
            patch("agent_skills_upd.cli.common.Path.cwd", return_value=cwd_dir),
        ):
            for env_name in ("amp", "ampcode"):
                dest = get_destination("skills", False, environment=env_name)
                assert dest == cwd_dir / ".agents/skills"

                dest = get_destination("skills", True, environment=env_name)
                assert dest == home_dir / ".config/agents/skills"


def test_clawdbot_environment_destinations():
    """Test destination resolution for ClawdBot environments."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        home_dir = tmp_path / "home"
        cwd_dir = tmp_path / "project"
        home_dir.mkdir()
        cwd_dir.mkdir()

        with (
            patch("agent_skills_upd.cli.common.Path.home", return_value=home_dir),
            patch("agent_skills_upd.cli.common.Path.cwd", return_value=cwd_dir),
        ):
            for env_name in ("clawdbot", "clawdis", "clawd"):
                dest = get_destination("skills", False, environment=env_name)
                assert dest == cwd_dir / "skills"

                dest = get_destination("skills", True, environment=env_name)
                assert dest == home_dir / ".config/clawdbot/skills"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
