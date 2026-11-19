<p align="center">
  <img src=".github/assets/logo.png" alt="Boomy" width="120">
</p>

<h1 align="center">Boomy</h1>

<p align="center"><b>Talk to your coding agents, on Windows.</b></p>

<p align="center">
  <a href="https://github.com/Jcapathy/boomy/actions/workflows/ci.yml"><img src="https://github.com/Jcapathy/boomy/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011%20(x64)-informational" alt="Windows 10 and 11, x64">
</p>

Boomy is a desktop app you talk to. Start a call on a project, say what you want done, and Boomy hands the work to the coding agent already on your computer: Claude Code, Codex, OpenCode, goose or omp. It keeps the conversation going while the agent works, and tells you out loud how it went.

Boomy is a Windows port of [Bomby](https://github.com/bomby-app/bomby), an MIT-licensed macOS app. It isn't affiliated with or endorsed by Bomby or its author.

> **Status: early.** Boomy builds, installs and launches on Windows 11, and its test suites pass there. Voice calls depend on your own provider keys and haven't had wide testing yet. Installers aren't code-signed, so Windows SmartScreen warns on first run.

## Contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Supported agents](#supported-agents)
- [Install](#install)
- [Your keys and your data](#your-keys-and-your-data)
- [Good to know](#good-to-know)
- [Build from source](#build-from-source)
- [Project layout](#project-layout)
- [What the Windows port changed](#what-the-windows-port-changed)
- [Releasing](#releasing)
- [License and credits](#license-and-credits)

## What it does

- **You talk, it answers.** Boomy listens and answers out loud through the voice model you pick: Gemini Live, OpenAI's GPT-Live or Rime's Prism.
- **Your agent does the work.** Real work goes to the agent you already use, with your own login, models and rules. Boomy never sees your agent's credentials.
- **Several things at once.** Each piece of work gets its own agent session, and sessions run side by side. The agents panel shows what each one is doing.
- **See the work as it happens.** Beside a project, panels show its git changes, its files, PowerShell terminals of your own and the project's to-dos.
- **Pick up where you left off.** Every call is saved with its transcript, to read back or resume. Turn on memory and Boomy remembers you across calls, in your own [Zep](https://www.getzep.com) project.
- **Extensions.** Connect Zapier or Composio and the voice can act on your other tools during a call.
- **Out of your way.** Boomy lives in the system tray: start or end a call from there, and closing the window keeps the call going. Opening Boomy again brings back its window instead of starting a second copy.

## How it works

```
 you ──voice──▶ LiveKit (local) ──▶ voice agent (Python) ──ACP──▶ your coding agent
                                       ▲          │                 (Claude Code, Codex, …)
                                       │          ▼
                           Boomy app (Tauri: Rust core + React UI)
```

1. **You talk.** Your voice goes over [LiveKit](https://livekit.io), which Boomy runs on your computer (or you point it at your own LiveKit Cloud project), to the voice model you picked.
2. **Your agent works.** When there's real work, Boomy's voice agent starts a session with your coding agent in the project's folders, over the [Agent Client Protocol](https://agentclientprotocol.com) (ACP).
3. **You hear the result.** When the agent finishes, Boomy tells you what happened in a sentence or two, and the full transcript stays in the app.

The app has three parts:

| Part | What it is |
| --- | --- |
| `app/` | The desktop app: [Tauri 2](https://tauri.app) with a Rust core (`app/src-tauri`) and a React + TypeScript frontend (`app/src`). |
| `agent/` | The voice agent: Python on [uv](https://docs.astral.sh/uv/) and LiveKit Agents, frozen into `bomby-agent.exe` with PyInstaller for release. |
| LiveKit server | LiveKit's own Windows build, downloaded and checked against its SHA-256, bundled next to the app. |

[docs/architecture.md](docs/architecture.md) goes deeper.

## Supported agents

Boomy finds these on your `PATH`, and in npm's and Scoop's install folders, and lists them in Settings, Agents:

| Agent | How Boomy runs it |
| --- | --- |
| [Claude Code](https://claude.com/product/claude-code) | through `claude-agent-acp`, on your own Claude plan |
| [Codex](https://developers.openai.com/codex/cli) | through `codex-acp`, on your own login |
| [OpenCode](https://opencode.ai) | `opencode acp` |
| [goose](https://goose-docs.ai) | `goose acp` |
| [omp](https://github.com/can1357/oh-my-pi) | `omp acp` |

Claude Code and Codex speak ACP through small adapters, which Boomy installs for you on first setup.

## Install

**Requirements:** Windows 10 or 11, x64, with the Microsoft Edge WebView2 runtime (built into Windows 11; the installer fetches it on Windows 10 if it's missing).

1. Download `Boomy-setup.exe` from the [latest release](https://github.com/Jcapathy/boomy/releases/latest), once one is published.
2. Run it. It installs for your user only, so it doesn't need administrator rights. SmartScreen will say the publisher is unknown, because the installer isn't code-signed yet: choose **More info**, then **Run anyway**.
3. Open Boomy from the Start menu. The first run walks you through picking an agent and a voice model, and entering its key: [Gemini](https://aistudio.google.com/apikey), [OpenAI](https://platform.openai.com/api-keys) (paid tier) or [Rime](https://app.rime.ai/tokens).
4. On your first call, Windows Security asks whether `livekit-server.exe` may use your network. Leave access off: calls only pass between programs on your computer, and that traffic isn't blocked.

Boomy updates itself from this repo's releases. Each update is signed, and Boomy checks the signature before installing.

## Your keys and your data

- **Keys** stay in Windows Credential Manager. Each one goes only to its own service.
- **Your voice** goes to the voice model you picked, through LiveKit on your computer (or your own LiveKit Cloud project).
- **Projects, calls, transcripts and to-dos** stay in a database on your computer, in `%APPDATA%\app.boomy.desktop`.
- **Logs** are in `%LOCALAPPDATA%\app.boomy.desktop\logs`. Settings, About, Export diagnostics zips them with keys and token-shaped strings removed.
- **Your agents** run as they always do, with their own logins and providers.

Boomy has no servers of its own and adds no analytics.

## Good to know

- **Agents run with full access.** Permissions are bypassed in every agent, so they can work anywhere on your computer. A project's folders tell an agent where to work; they don't fence it in.
- **Use wired headphones or speakers.** With Bluetooth headphones as the output, the voice can pick itself up and answer itself.

## Build from source

You need [Git for Windows](https://gitforwindows.org), [Rust](https://rustup.rs), [Bun](https://bun.sh) 1.4.4, [uv](https://docs.astral.sh/uv/) and [just](https://just.systems), or [mise](https://mise.jdx.dev), which installs the versions pinned in `mise.toml`. Run `just` from **Git Bash**: the recipes are shell scripts.

```bash
git clone https://github.com/Jcapathy/boomy.git
cd boomy
just livekit build     # LiveKit's own Windows server, checked against its SHA-256
just agent install     # the voice agent's Python dependencies and the ACP adapters
just app install       # the frontend's dependencies
just app dev           # start the app with hot reload
```

Other useful commands:

```bash
just check             # everything CI checks: lint, types, tests, licenses, docs links
just app build         # the release app and its installer, in app/src-tauri/target/release/bundle/nsis
just app smoke         # launch the built app and check it opens
just                   # list every recipe
```

[CONTRIBUTING.md](CONTRIBUTING.md) has the conventions and the checks every change must pass.

## Project layout

```
app/                 desktop app (Tauri 2)
  src/               React + TypeScript frontend
  src-tauri/         Rust core, Tauri config, icons, capabilities
  scripts/           draw-icons.py: draws every icon from the mascot's geometry
agent/               Python voice agent, ACP client, harnesses for each coding agent
  adapters/          the ACP adapters for Claude Code and Codex (Bun)
docs/                architecture, provider notes and decision records
scripts/             LiveKit server download for Windows, version tooling
.github/workflows/   CI, Package (installer build) and Release, all on Windows runners
*.just, justfile     every build, run and check command
```

## What the Windows port changed

For anyone comparing with Bomby, the main changes were:

- **IPC:** loopback TCP with a shared secret instead of Unix domain sockets, between the Rust core and the Python agent.
- **Call media:** the local LiveKit server answers on the computer's own addresses as well as loopback, because Windows won't route between the two and the agent's WebRTC client only uses network addresses. Signalling stays on loopback.
- **Processes:** `CREATE_NO_WINDOW` and `taskkill /T` instead of process groups and signals, so no console windows flash up and child processes never outlive Boomy.
- **Terminals:** PowerShell over ConPTY instead of a Unix shell over a pty.
- **Discovery:** agents found through `PATH` and `PATHEXT` (`.exe`, `.cmd`, `.bat`), plus npm's and Scoop's install folders.
- **Bundling:** LiveKit's prebuilt Windows server, Bun for Windows for the adapters, the agent frozen as a Windows executable, and an NSIS installer instead of a DMG.
- **Brand:** a new name, mascot, colour and icon set, as Bomby's [trademark policy](TRADEMARKS.md) asks of forks.

## Releasing

Releases are built by the [Release workflow](.github/workflows/release.yml), started by hand from the Actions tab. It builds the app and installer from scratch, checks the frozen agent and that the app launches, signs the update with the updater key, and attaches `Boomy-setup.exe` and `latest.json` to a draft release. Publishing the draft makes it the update installed copies pick up.

It needs one secret in the repository's `release` environment: `TAURI_SIGNING_PRIVATE_KEY`, the private half of the updater key whose public half is in [`tauri.windows.conf.json`](app/src-tauri/tauri.windows.conf.json).

## License and credits

Boomy's code is [MIT](LICENSE), as is Bomby's, which it's forked from. Thanks to Bomby's author for building it in the open.

Bomby™ and its brand belong to their owner and aren't used here; see [TRADEMARKS.md](TRADEMARKS.md). Security reports go through [SECURITY.md](SECURITY.md), never a public issue.
