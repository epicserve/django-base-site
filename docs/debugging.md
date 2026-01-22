# Debugging Django in Docker

This project supports remote debugging of Django running inside Docker containers using the Debug Adapter Protocol (DAP). This works with VS Code, LazyVim/Neovim, and any other DAP-compatible editor.

## Quick Start

### 1. Enable Debugging

Choose one of these methods:

**Option A: Using .env file (Recommended)**
```bash
# Uncomment this line in your .env file
ENABLE_DEBUGGER=true
```

**Option B: Using docker compose command**
```bash
ENABLE_DEBUGGER=true docker compose up
```

**Option C: Edit compose.yml**
```yaml
# Uncomment this line in the web service environment section
ENABLE_DEBUGGER: 'true'
```

### 2. Restart the containers

```bash
just stop
just start
```

Or using docker compose directly:
```bash
docker compose down
docker compose up
```

### 3. Attach your debugger

The debugger will be listening on `localhost:5678`.

## VS Code Setup

The project includes a pre-configured launch configuration in [.vscode/launch.json](.vscode/launch.json).

### Usage

1. Enable debugging (see Quick Start above)
2. Start the containers
3. Open VS Code
4. Go to Run and Debug (Ctrl+Shift+D / Cmd+Shift+D)
5. Select "Django: Attach to Docker" from the dropdown
6. Press F5 or click the green play button
7. Set breakpoints in your Python code
8. Make requests to your Django app (http://localhost:8000)

### Troubleshooting

- **"Cannot connect to runtime process"**: Make sure `ENABLE_DEBUGGER=true` is set and containers are running
- **Breakpoints not hitting**: Ensure the code path is being executed and breakpoints are in valid locations
- **"Source not found"**: Check that path mappings in launch.json are correct

## LazyVim/Neovim Setup

LazyVim and Neovim use nvim-dap for debugging. Here's a sample configuration:

### Install nvim-dap and nvim-dap-python

Using lazy.nvim:

```lua
{
  "mfussenegger/nvim-dap",
  dependencies = {
    "mfussenegger/nvim-dap-python",
    "rcarriga/nvim-dap-ui",
  },
  config = function()
    local dap = require("dap")
    local dap_python = require("dap-python")

    -- Configure Python adapter for remote debugging
    dap.adapters.python = {
      type = 'server',
      host = 'localhost',
      port = 5678,
    }

    -- Configure Django debugging
    dap.configurations.python = {
      {
        type = 'python',
        request = 'attach',
        name = 'Django: Attach to Docker',
        host = 'localhost',
        port = 5678,
        pathMappings = {
          {
            localRoot = vim.fn.getcwd(),
            remoteRoot = '/srv/app',
          },
        },
      },
    }
  end,
}
```

### Usage

1. Enable debugging (see Quick Start above)
2. Start the containers
3. Open your file in Neovim
4. Set breakpoints: `:lua require('dap').toggle_breakpoint()`
5. Start debugging: `:lua require('dap').continue()`
6. Use standard nvim-dap commands to step through code

### Key Bindings (Example)

Add these to your Neovim config:

```lua
vim.keymap.set('n', '<F5>', function() require('dap').continue() end)
vim.keymap.set('n', '<F10>', function() require('dap').step_over() end)
vim.keymap.set('n', '<F11>', function() require('dap').step_into() end)
vim.keymap.set('n', '<F12>', function() require('dap').step_out() end)
vim.keymap.set('n', '<Leader>b', function() require('dap').toggle_breakpoint() end)
```

## How It Works

When `ENABLE_DEBUGGER=true`:

1. The startup script ([scripts/start_dev.sh](../scripts/start_dev.sh)) runs Django with debugpy
2. debugpy listens on `0.0.0.0:5678` inside the container
3. Docker exposes this port to `localhost:5678` on your host machine
4. Your editor connects to this port using the DAP protocol
5. You can set breakpoints, inspect variables, and step through code

### Important Notes

- **Auto-reload is disabled** when debugging is enabled to prevent conflicts with the debugger
- You must **manually restart the server** after code changes when debugging
- For normal development (with auto-reload), leave `ENABLE_DEBUGGER` unset or set to `false`

## Port Configuration

- **Django**: http://localhost:8000
- **Debugpy**: localhost:5678
- **Vite (frontend)**: http://localhost:3000
- **MkDocs (docs)**: http://localhost:4000

## Debugging Best Practices

1. **Use conditional breakpoints** to avoid stopping on every iteration in loops
2. **Inspect the call stack** to understand the execution flow
3. **Watch variables** to track state changes
4. **Use the debug console** to evaluate expressions
5. **Remember to disable debugging** when not needed to enable auto-reload

## Other DAP-Compatible Editors

The debugpy server works with any editor that supports DAP:

- **PyCharm/IntelliJ IDEA**: Use "Python Debug Server" run configuration
- **Emacs**: Use dap-mode
- **Sublime Text**: Use Debugger package
- **Eclipse**: Use PyDev

Configure them to connect to `localhost:5678` with path mapping from your local workspace to `/srv/app`.

## Additional Resources

- [debugpy documentation](https://github.com/microsoft/debugpy)
- [VS Code Python debugging](https://code.visualstudio.com/docs/python/debugging)
- [nvim-dap documentation](https://github.com/mfussenegger/nvim-dap)
- [Debug Adapter Protocol](https://microsoft.github.io/debug-adapter-protocol/)
