# Contributing to Boomy

Thanks for helping. Boomy, a Windows fork of [Bomby](https://github.com/bomby-app/bomby), is designed and tested by its maintainer. Contributions are welcome however you write them, and you're responsible for every line of yours.

## Start with an issue

- **Bugs**: open a [bug report](https://github.com/Jcapathy/boomy/issues/new?template=bug.yml) with the steps, what you expected and what happened.
- **Ideas and features**: open a [feature request](https://github.com/Jcapathy/boomy/issues/new?template=feature.yml) and wait for it to be marked `accepted` before you build it. Boomy is opinionated about how it looks, sounds and behaves, and a pull request for something that wasn't agreed may be closed, however good the code.
- **Small fixes** (a typo, a broken link, a bug with an obvious fix) can go straight to a pull request.
- **Looking for something to do?** Try issues marked [`good first issue`](https://github.com/Jcapathy/boomy/labels/good%20first%20issue) or [`help wanted`](https://github.com/Jcapathy/boomy/labels/help%20wanted).

Changes to how Boomy looks go through design first ([docs/brand.md](docs/brand.md)); say so in the issue and the maintainer will design it or agree a design with you. Boomy's spoken prompts (`agent/prompts/`) are the maintainer's: propose a change in an issue rather than a pull request.

Security problems go through [SECURITY.md](SECURITY.md), never a public issue.

## Set up

You need Windows 10 or 11 (x64), [Git for Windows](https://gitforwindows.org), [mise](https://mise.jdx.dev) and [just](https://just.systems). mise installs every other tool at the version pinned in `mise.toml`. Run `just` from Git Bash: the recipes are shell scripts.

```bash
just install    # the pinned tools and every part's dependencies; downloads LiveKit's own Windows server and checks its SHA-256
just app dev    # start the app with hot reload
just            # every command
```

The first run sets up an agent and your keys, as it does for everyone.

### Try a state your computer isn't in

Development builds take flags that change nothing on your computer:

```bash
just app dev --splash                 # the first-run splash at every launch
just app dev --agents=none            # as if no agent were installed (or --agents=codex,goose)
just app dev --signed-out             # Claude Code signed out, on an empty config folder
just app dev --no-keys                # no LiveKit or voice keys; any you add last for the run
```

### Talk to the voice agent without the app

```bash
cp agent/.env.example agent/.env    # add your GOOGLE_API_KEY
just agent console                  # talk out loud
just agent console-text             # or type
```

## Find your way around

| Path | What's there |
| --- | --- |
| `app/` | The desktop app: Tauri v2, a React frontend in `src/` and a Rust core in `src-tauri/` ([app/AGENTS.md](app/AGENTS.md)) |
| `agent/` | The voice agent: Python on LiveKit Agents, one definition per voice provider, coding agent and extension ([agent/AGENTS.md](agent/AGENTS.md)) |
| `docs/` | Architecture, roadmap, decisions, and notes on every library we rely on ([docs/AGENTS.md](docs/AGENTS.md)) |

Read [docs/architecture.md](docs/architecture.md) first. The `AGENTS.md` files are written for coding agents and people alike; your agent reads them by itself. Adding another ACP agent is a few lines: [the steps](docs/decisions/detect-acp-native-agents.md#adding-an-agent).

## Rules

- **Commands run through `just`** from the repository root.
- **`just check` passes** before a change is done: lint, formatting, types with 0 errors and 0 warnings, tests, generated files current, dependency licenses, and the docs' links. Fix any failure you see, even one you didn't cause.
- **Docs change with the code**, in the same pull request ([how we document](docs/AGENTS.md#how-we-document)). A choice someone could reasonably question gets a decision record in `docs/decisions/`.
- **Check library facts, don't recall them.** LiveKit, the voice providers, ACP and Tauri move fast: check the installed source or current docs, and note what you relied on, with its source and version, in the matching `docs/*-notes.md`.
- **New tools are pinned** in `mise.toml`; nothing is installed system-wide.
- **No secrets and no personal details** in code, docs or tests: no real local paths, accounts or devices. Use placeholders like `C:\Users\me\...`. Keys live only in `agent/.env` (gitignored) and Windows Credential Manager.

## Pull requests

- One change per pull request, titled with what changes for the person using Boomy.
- Say how you tried it: a call in the app, with which voice provider and which agent, on which Windows version. CI can't hold a call, so this is the test that counts.
- For anything you can see, add a screenshot or a short screen recording, light and dark when both change.
- Pull requests are merged with a merge commit, so your branch's commits stay in the history as you wrote them: make each one say what it changes, and tidy them before review rather than after.

### What CI runs

Every pull request runs [CI](.github/workflows/ci.yml); the first three must pass to merge.

| Check | Runs | On |
| --- | --- | --- |
| `agent` | `just agent check`: ruff, basedpyright, pytest, the providers' and extensions' catalogues current | Windows |
| `app` | `just app check`: Vite+ (format, lint, types), clippy, rustfmt, the frontend's and the core's tests, the generated types current, cargo-deny's licenses and sources, the frontend's production build | Windows |
| `repo` | `just lint-workflows` (actionlint, zizmor) `just lint-docs` (every link and anchor between the Markdown files) and `just lint-versions` (every place that carries Boomy's version says the same) | Linux |
| `advisories` | `just app advisories`: RustSec advisories for the core's dependencies, also every Monday | Linux |
| `dependency-review` | New dependencies with known vulnerabilities, in any lockfile | GitHub |

[Package](.github/workflows/package.yml) also builds the app and its installer as a release would, and checks its frozen agent runs and the app opens, when a pull request touches the agent, the core, the build or the pinned tools.

## License

By contributing, you agree that your contribution is licensed under the [MIT License](LICENSE), like the rest of the code. Bomby's name, logo, mascot and icons belong to their owner and aren't used here ([TRADEMARKS.md](TRADEMARKS.md)).

Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md).
