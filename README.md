<div align="center">

# 🧩 agent-skills-project

## Just Update Your Skills

**Share and install Claude Code / Codex / OpenCode / Amp / ClawdBot skills with a single command.**

*Like pip or npm, but for your agent resources.*

[![PyPI](https://img.shields.io/pypi/v/agent-skills-upd?color=blue)](https://pypi.org/project/agent-skills-upd/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Try It](#-try-it-now) • [Install](#-install-any-resource) • [Create Your Own](#-create-your-own) • [Community](#-community-resources)

</div>

---

## ⚡ Try It Now

No installation needed. Just run:

```bash
uvx upd-skill kasperjunge/hello-world
```

**That's it.** The skill is now available in Claude Code.

Using another agent? Not a problem:

```bash
uvx upd-skill snarktank/amp-skills/pdf --env amp
```

**That's it.** The skill is now available in Amp.

---

## 📦 Install Any Resource

```bash
uvx upd-skill <username>/<skill-name>               # Skills from GitHub
uvx upd-skill <username>/<repo-name>/<skill-name>   # Skills from GitHub
uvx upd-skill upd.dev/<username>/<skill-name>       # Skills from Upd.dev
```

To install slash commands or subagents for Claude Code:

```bash
uvx upd-command <username>/<command-name>   # Slash commands
uvx upd-agent <username>/<agent-name>       # Sub-agents
```

### Examples for Codex, OpenCode, or different repo names

```bash
# Install from different repository structures
uvx upd-skill username/skill-name --repo different-repo

# Install from different Git host
uvx upd-skill upd.dev/username/skill-name --repo different-repo # Skills from Upd.dev

# Install to different environments
uvx upd-skill username/skill-name --env opencode   # e.g. OpenCode
uvx upd-skill username/skill-name --env codex      # e.g. Codex

# Custom installation path
uvx upd-skill username/skill-name --dest ./my-path/

# Global installation
uvx upd-skill username/skill-name --global
```

**Supports multiple repository structures:**

- `.claude/skills/` (standard)
- `skills/` (Anthropic style)
- `skill/` (OpenCode style)

---

## 🤖 Supports Your Favorite Agent

- Default agent is Claude Code
- For Codex use flag `--env codex`
- For OpenCode use flag `--env opencode`
- For Amp use flag `--env amp`
- For ClawdBot use flag `--env clawd`

---

## 🚀 Create Your Own

Ready to share your own skills? Create your personal toolkit in 30 seconds:

```bash
uvx create-agent-skill-repo --github
```

**Done.** You now have a GitHub repo that anyone can install from.

> Requires [GitHub CLI](https://cli.github.com/). Run without `--github` to set up manually.

### What You Get

- A ready-to-use `agent-resources` repo on your GitHub
- Example skill, command, and agent to learn from
- Instant shareability — tell others:

```bash
uvx upd-skill <your-username>/hello-world
```

### Create Your Own Resources

Edit the files in your repo:

```
your-username/agent-resources/
└── .claude/
    ├── skills/          # Skill folders with SKILL.md
    ├── commands/        # Slash command .md files
    └── agents/          # Sub-agent .md files
```

Push to GitHub or Upd.dev. No registry, no publishing step.

---

## 🌍 Share With Others

Sharing is just a message:

> *"This skill saves me hours — try `uvx upd-skill yourname/cool-skill`"*

**One command. Zero friction.** The more you share, the more the community grows.

---

## 🗂 Community Resources

### 🚀 Go Development Toolkit — [@dsjacobsen](https://github.com/dsjacobsen/agent-resources)

A comprehensive Claude Code toolkit for Go developers.

```bash
uvx upd-skill dsjacobsen/golang-pro      # Expert Go knowledge
uvx upd-agent dsjacobsen/go-reviewer     # Code review agent
uvx upd-command dsjacobsen/go-check      # Quick code check
```

**Includes**: 1 skill, 9 agents, 11 commands covering scaffolding, testing, API building, refactoring, and more.

---

**Built something useful?** [Open an issue](https://github.com/kasperjunge/agent-resources-project/issues) with a link to your `agent-resources` repo and we'll add it here.

---

<div align="center">

**MIT License** · Fair fork of [kasperjunge/agent-resources-project](https://github.com/kasperjunge/agent-resources-project) to support more Git hosts and target environments (++ Codex, OpenCode, Amp, ClawdBot).

</div>
