# Developing on Windows (WSL 2)

Django Base Site's local tooling — the quickstart script, `just` recipes, Git hooks, and Docker bind mounts — expects a Unix shell. On Windows, the supported way to run it is inside **[WSL 2](https://learn.microsoft.com/en-us/windows/wsl/install)** (Windows Subsystem for Linux) with **Docker Desktop's WSL 2 backend**. Once WSL 2 and Docker Desktop are set up, every command in the [Installation guide](index.md#installation) works the same as on Linux and macOS.

## Prerequisites

- **Windows 10** (version 2004 / Build 19041 or higher) or **Windows 11**
- Hardware virtualization enabled in BIOS/UEFI (on by default on most modern machines)
- **[Windows Terminal](https://learn.microsoft.com/en-us/windows/terminal/install)** (pre-installed on Windows 11) is recommended for working in WSL

## 1. Install WSL 2 and Ubuntu

Open **PowerShell** or **Windows Terminal** as Administrator and run:

```powershell
wsl --install
```

This enables WSL 2 and installs Ubuntu as the default Linux distribution. Restart Windows if prompted.

After restarting, open **Ubuntu** from the Start menu (or as a tab in Windows Terminal) and follow the prompt to create your Linux username and password.

> **Note:** From this point on, run all project commands inside your **Ubuntu WSL terminal**, not PowerShell or Command Prompt.

Update Ubuntu's packages and install the base utilities required by the install script and frontend toolchain:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git unzip
```

`unzip` is omitted from fresh Ubuntu WSL images, and both the quickstart script (`scripts/start_new_project`) and Bun's installer depend on it.

## 2. Install Docker Desktop with the WSL 2 Backend

1. Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/) and follow Docker's [WSL 2 backend guide](https://docs.docker.com/desktop/features/wsl/).
2. Open Docker Desktop and check two settings:
   - **Settings → General**: ensure **Use the WSL 2 based engine** is checked.
   - **Settings → Resources → WSL Integration**: enable integration for your **Ubuntu** distribution, then click **Apply & restart**.
3. Verify Docker is reachable from inside your Ubuntu WSL terminal:

```bash
docker --version && docker compose version
```

## 3. Install `just`, `uv`, and `bun` Inside WSL

`just format` and `just lint` run the formatters and source linters natively via `uvx` and `bunx`, and `just create_env` uses `uvx epicenv`, so `just`, `uv`, and `bun` need to be on your `PATH` inside WSL.

### Option A: Install with mise (Recommended)

[mise](https://mise.jdx.dev/) manages CLI tool versions in one place and keeps them easy to update:

```bash
curl https://mise.run | sh
```

Activate mise in your shell (`~/.bashrc` for bash, or `~/.zshrc` for zsh) and reload it:

```bash
echo 'eval "$($HOME/.local/bin/mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
```

Install the required tools globally:

```bash
mise use -g just uv bun
```

If you plan to use parallel git worktrees (see [Worktrees](docker.md#worktrees)) or local Stripe webhook forwarding (see [Billing](billing.md)), mise can install those too:

```bash
mise use -g worktrunk stripe
```

### Option B: Install Each Tool Individually

If you prefer each tool's official installer:

```bash
# uv (provides uv and uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh

# bun (provides bun and bunx; requires unzip from step 1)
curl -fsSL https://bun.sh/install | bash

# just (or `sudo apt install just` on Ubuntu 24.04+)
mkdir -p ~/.local/bin
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin
```

Make sure `~/.local/bin` and `~/.bun/bin` are on your `PATH`, then open a new WSL terminal (or reload your shell profile). See each tool's docs if you want another install method: [uv](https://docs.astral.sh/uv/getting-started/installation/), [bun](https://bun.sh/docs/installation), [just](https://github.com/casey/just#installation).

### Verify Your Toolchain

```bash
docker compose version
just --version
uv --version
bun --version
```

## 4. Keep Projects in the WSL Filesystem

> **Important:** Always create and clone projects inside your Linux home directory (for example `~/projects` or `~/Sites`), **never** under `/mnt/c/` (your Windows `C:\` drive).

Keeping repositories on the native WSL 2 `ext4` filesystem avoids the three biggest Windows + Docker headaches:

| Area | WSL Filesystem (`~/projects`) | Windows Mount (`/mnt/c/...`) |
|------|-------------------------------|------------------------------|
| **I/O & Docker bind mounts** | Near-native Linux speed | Slow across the 9P filesystem bridge |
| **Auto-reload & Vite HMR** | `inotify` events work natively | File changes frequently fail to trigger reloads |
| **Permissions & Git hooks** | Native POSIX bits (`chmod +x .githooks/*`) and UID `1000:1000` match `compose.yml` | Windows permissions can break executable scripts and dirty `git status` |

## 5. Create and Run Your Project

From your Ubuntu WSL terminal, follow the standard [Installation](index.md#installation) steps inside your Linux home directory:

```bash
mkdir -p ~/projects && cd ~/projects
bash <(curl -s https://raw.githubusercontent.com/epicserve/django-base-site/main/scripts/start_new_project)
```

Then initialize Git and boot the stack:

```bash
cd my-project
git init
just init
```

Once the services are up, seed the development logins (optional):

```bash
just seed
```

Open **http://localhost:8000/** in your normal Windows browser. WSL 2 automatically forwards `localhost` ports from Linux and Docker to Windows, so all of the standard dev URLs work directly from Windows:

| URL | What |
|-----|------|
| http://localhost:8000/ | Vue SPA |
| http://localhost:8000/admin/ | Django admin |
| http://localhost:8000/api/docs | OpenAPI docs (DEBUG only) |
| http://localhost:8025/ | Mailpit (outgoing emails) |
| http://localhost:9001/ | Silo console (local media bucket) |

> **Note:** Always use `http://localhost:8000/`, not `http://127.0.0.1:8000/`. WebAuthn passkey enrollment rejects bare IP addresses as Relying Party IDs.

## Editors and IDEs

Because your project files live inside the WSL filesystem, use your editor's WSL integration rather than opening files over `/mnt/c/`:

### VS Code

1. Install the [WSL extension](https://code.visualstudio.com/docs/remote/wsl) in VS Code on Windows.
2. From your project directory in the Ubuntu WSL terminal, run:

```bash
code .
```

VS Code starts its server inside WSL while rendering the UI on Windows. File access, the integrated terminal, Git hooks, and remote debugging (`just start_with_debugpy` + F5 — see [Debugging](debugging.md#vs-code-setup)) all work out of the box.

### PyCharm

1. Open your project from the WSL filesystem via `\\wsl$\Ubuntu\home\<username>\projects\<project>` (or through PyCharm's **Open** dialog under **WSL**).
2. Connect PyCharm to Docker inside WSL: go to **Settings → Build, Execution, Deployment → Docker**, click **+**, and select **WSL** with your Ubuntu distribution (see [JetBrains' Docker connection settings](https://www.jetbrains.com/help/pycharm/docker-connection-settings.html)).
3. Follow the [PyCharm setup in the Debugging guide](debugging.md#pycharm-setup) using that WSL Docker server. See also [JetBrains' WSL interpreter guide](https://www.jetbrains.com/help/pycharm/using-wsl-as-a-remote-interpreter.html).

### Terminal Editors (Neovim, etc.)

Run Neovim or other terminal editors directly inside your Ubuntu WSL terminal. See [LazyVim/Neovim Setup](debugging.md#lazyvimneovim-setup) for remote debugging via `localhost:5678`.

## WSL Tips and Gotchas

### Keep Unix Line Endings in Git

Configure Git inside WSL to preserve `LF` line endings so bash scripts (`.githooks/pre-commit`, `.githooks/pre-push`, `scripts/worktree`) don't fail with `\r: command not found`:

```bash
git config --global core.autocrlf input
```

### Limit WSL Memory and CPU (`.wslconfig`)

Running Postgres, Redis, Celery, Django, Vite, and Playwright inside WSL can use noticeable RAM. To cap WSL 2's resource usage, create or edit `C:\Users\<YourWindowsUsername>\.wslconfig` on the Windows side (see [Microsoft's `.wslconfig` reference](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)):

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
```

Apply changes by running `wsl --shutdown` in PowerShell, then restarting Docker Desktop and your Ubuntu terminal.

### Using 1Password SSH Keys in WSL

If you store Git SSH keys or commit-signing keys in 1Password on Windows, you don't need to duplicate keys into WSL. Configure Git in WSL to use Windows' `ssh.exe` and `op-ssh-sign.exe` by following [1Password's WSL SSH integration guide](https://developer.1password.com/docs/ssh/integrations/wsl/).

### Database Dumps (`just db_dump` / `just db_restore`)

`just db_dump` writes dumps to `~/Downloads` inside WSL (`/home/<username>/Downloads`), not your Windows `Downloads` folder. Make sure `~/Downloads` exists (`mkdir -p ~/Downloads`), or pass an explicit path when restoring a dump saved on Windows:

```bash
just db_restore /mnt/c/Users/<YourWindowsUsername>/Downloads/my-project-20260101-120000.dump
```

### Opening Coverage Reports and Browser Links

- `just test_with_coverage` finishes by running `open htmlcov/index.html`, which targets macOS. On WSL, open the report in your Windows browser with `explorer.exe htmlcov/index.html` (or run `just test` / `docker compose exec web pytest --cov --ds=config.settings.test_runner` directly).
- If CLI tools in WSL need to open URLs in your Windows browser, add this to your `~/.bashrc` or `~/.zshrc`:

```bash
export BROWSER="/mnt/c/Windows/System32/cmd.exe /c start"
```

### Locale Warnings on Minimal Ubuntu Images

If a fresh Ubuntu WSL image prints locale warnings when running Python or shell tools, generate `en_US.UTF-8`:

```bash
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
```

### `localhost` Stops Responding After Windows Sleep

WSL 2 occasionally drops localhost port forwarding after Windows hibernates or sleeps. If `http://localhost:8000/` stops answering even though `docker compose ps` shows containers running, restart WSL from PowerShell:

```powershell
wsl --shutdown
```

Then reopen Docker Desktop and run `just start` again in Ubuntu.

### File Ownership (`HOST_UID` / `HOST_GID`)

`compose.yml` runs the `web` and `frontend` containers as `${HOST_UID:-1000}:${HOST_GID:-1000}` so files created inside containers aren't owned by `root`. The default Ubuntu WSL user is UID `1000` / GID `1000`, so this matches automatically. If `id -u` in WSL prints a different number, export `HOST_UID=$(id -u)` and `HOST_GID=$(id -g)` in your shell profile.
