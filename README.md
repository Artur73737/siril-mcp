# Siril MCP

LLM control of a live **Siril** GUI session via an in-app Python bridge.

Works on macOS, Linux and Windows, with Cursor, opencode and any MCP client.

## Architecture

1. **Bridge** (`bridge/bridge.py`) — started inside Siril with `pyscript -async`. Talks to Siril through `sirilpy` and listens for MCP requests.
2. **MCP server** (`siril-mcp`) — stdio MCP process; forwards tools to the bridge.

```
MCP client → siril-mcp (stdio) → bridge → Siril
```

Transport between server and bridge:

| Transport | When | Endpoint |
|---|---|---|
| Unix socket | macOS / Linux (has `AF_UNIX`) | `~/Library/Application Support/siril-mcp/bridge.sock` (override with `SIRIL_MCP_SOCKET`) |
| TCP | Windows, or when `AF_UNIX` is unavailable | `127.0.0.1:27777` (override with `SIRIL_MCP_HOST` / `SIRIL_MCP_PORT`) |

Select explicitly with `SIRIL_MCP_TRANSPORT=unix|tcp`. Default is `unix` where supported, otherwise `tcp`. Set the **same** variables on both sides (MCP server env + Siril launcher).

## Setup

### 1. Install the MCP package

```bash
cd /path/to/siril-mcp
uv sync
```

or with pip:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Install the Siril launcher

**macOS / Linux:**

```bash
./scripts/install_bridge_to_siril_scripts.sh
```

**Windows (manual):** the script above only knows macOS paths. Copy the launcher by hand:

1. Create the folder `C:\Users\<you>\AppData\Roaming\siril\scripts` if missing (check Siril's script path in `config.1.4.ini`, key `script_path`).
2. Create `Start_MCP_Bridge.py` inside it with this content (adjust the bridge path):

```python
#version = 1.3.0
import os
import runpy

os.environ.setdefault("SIRIL_MCP_TRANSPORT", "tcp")
os.environ.setdefault("SIRIL_MCP_HOST", "127.0.0.1")
os.environ.setdefault("SIRIL_MCP_PORT", "27777")

runpy.run_path(r"E:\siril-mcp\bridge\bridge.py", run_name="__main__")
```

### 3. Start the bridge in Siril

Open Siril, wait until the log shows `Python module is up-to-date` and `Caricamento dello script: Start_MCP_Bridge.py`, then:

- Scripts menu → **Start_MCP_Bridge** (prefer async), or
- Siril command line: `pyscript -async /path/to/siril-mcp/bridge/bridge.py`

You should see in the Siril log:

```
[siril-mcp] connected to Siril
[siril-mcp] listening on tcp 127.0.0.1:27777
```

(on macOS/Linux: `listening on .../bridge.sock`). Keep Siril open while using the MCP.

### 4. Register the MCP server

**opencode** (`C:\Users\<you>\.config\opencode\opencode.json` or `~/.config/opencode/opencode.json`):

```json
{
  "mcp": {
    "siril": {
      "type": "local",
      "command": ["uv", "--directory", "E:\\siril-mcp", "run", "siril-mcp"],
      "enabled": true,
      "environment": {
        "SIRIL_MCP_TRANSPORT": "tcp",
        "SIRIL_MCP_HOST": "127.0.0.1",
        "SIRIL_MCP_PORT": "27777"
      }
    }
  }
}
```

On macOS/Linux the `environment` block can be omitted (Unix socket is the default).

**Cursor** (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "siril": {
      "command": "/path/to/siril-mcp/.venv/bin/siril-mcp",
      "args": [],
      "env": {
        "SIRIL_MCP_TRANSPORT": "tcp",
        "SIRIL_MCP_HOST": "127.0.0.1",
        "SIRIL_MCP_PORT": "27777"
      }
    }
  }
}
```

Restart the MCP client after editing. Verify with `opencode mcp list` (expect `siril ✓ connected`) or by calling `siril_ping`.

### Optional: StarNet

If you plan to use StarNet for star removal, install it via Siril's usual StarNet setup. This stack does not install or configure StarNet; once it is available to Siril, scriptable StarNet commands work like any other command through the bridge.

## Tools

| Tool | Purpose |
|------|---------|
| `siril_ping` | Bridge health |
| `siril_get_state` | Loaded image, size, selection, cwd, keywords |
| `siril_list_commands` | Filterable scriptable command catalog |
| `siril_run_command` | Run one Siril command |
| `siril_run_script` | Run multi-line `.ssf` or `.py` |
| `siril_get_preview` | Autostretched PNG (optional ROI, max edge) |
| `siril_set_selection` | Set selection rectangle |
| `siril_get_stats` | Per-channel stats |
| `siril_undo` | Undo last op |

If the bridge is down, tools fail with an explicit start hint (they do **not** fall back to browsing the filesystem).

## Batch stacking without the bridge

The bridge is for interactive work on the live GUI session. For heavy batch jobs (calibrate / register / stack of many frames) prefer `siril-cli` with an `.ssf` script — same engine, headless, reproducible:

```bash
siril-cli -d /path/to/work -s stack_lights_darks.ssf
```

Example (lights + darks only, OSC camera, Siril 1.4):

```
requires 1.3.0
cd darks
convert dark -out=../process
cd ../process
stack dark rej 3 3 -nonorm -out=../masters/dark_stacked
cd ..
cd lights
convert light -out=../process
cd ../process
calibrate light -dark=../masters/dark_stacked -cfa -equalize_cfa -debayer -cc=dark
register pp_light
stack r_pp_light rej 3 3 -norm=addscale -output_norm -rgb_equal -32b -out=result
```

This is the reference `OSC_Preprocessing.ssf` workflow minus flats/biases; see the full script in Siril's script collection for the 4-frame variant.

## Bridge limitations (what you don't get yet)

This stack only reaches what **scripts / `sirilpy` already expose**. GUI-only or poorly scripted Siril features are out of scope for the bridge approach, including:

- Display / STF / `visu` state matching exactly what the user sees in the viewport
- Inspector-style diagnostics
- Curves, remixer, and compositing UI hooks (unless a documented command equivalent exists)
- Reliable sequence / `load_seq` context and Python-style metadata that today only exists on GUI-only paths
- True canvas screenshots (overlays, zoom, annotations) vs an autostretched `gfit` preview
- Attaching to Siril without manually starting the bridge (`pyscript -async`)
- Headless `siril-cli -p` as the primary control path (optional later; not what this bridge is)

## Canonical test queries

1. *Ping Siril and tell me if an image is loaded, its size, filename, and selection.*
2. *Show a preview of the current image (max 1024px) and describe it.*
3. *List stretch-related Siril commands.*

## Troubleshooting

- **Bridge not running:** start `pyscript -async` again; check `bridge.status.json` under the support dir.
- **Windows `AF_UNIX` error:** fixed by the TCP fallback — make sure both the launcher and the MCP server env use `SIRIL_MCP_TRANSPORT=tcp` and the Siril log shows `listening on tcp ...`.
- **Port already in use:** another bridge is running, or set another port via `SIRIL_MCP_PORT` on both sides.
- **Launcher missing from Scripts menu:** check Siril's `script_path` in the config and restart Siril after copying `Start_MCP_Bridge.py`.
- **Socket permissions (Unix):** socket is created mode `0600` under Application Support.
- **First Siril run:** wait until Siril finishes Python venv setup before starting the bridge.
- **Nested `pyscript`:** `siril_run_script` with `kind=py` runs sync `pyscript`; prefer `siril_run_command` for simple ops.

## License

[GPL-3.0-or-later](LICENSE.md) — same as [Siril](https://siril.org).
