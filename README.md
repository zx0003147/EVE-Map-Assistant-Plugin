# EVE Map Assistant

EVE Map Assistant is a Codex Plugin and Skill for controlling EVE Static Map Planner. Plugin 0.3.0 bundles the `eve-static-map` MCP definition and starts the stable `eve-map-mcp.exe` command installed by EVE Static Map Planner 0.5.0 or later.

Repository: [zx0003147/EVE-Map-Assistant-Plugin](https://github.com/zx0003147/EVE-Map-Assistant-Plugin)

## Requirements

- Windows
- EVE Static Map Planner 0.5.0 or later installed
- **Preferences > AI Control** enabled in the running map application
- Codex with local Plugin and STDIO MCP support

## Architecture

```text
Codex
  -> EVE Map Assistant Skill
  -> bundled eve-static-map MCP definition
  -> eve-map-mcp.exe on per-user PATH
  -> EVE Static Map Planner AI Control
```

The Plugin contains only metadata, its Skill, and the portable MCP definition. The Map MSI owns the executable and its per-user PATH entry. Neither side stores a control port, session secret, Windows username, or machine-specific absolute path in the Plugin.

## Install

1. Install or upgrade to EVE Static Map Planner 0.5.0 or later.
2. Start the map and enable **Preferences > AI Control**.
3. Add this local marketplace and install the Plugin from this repository:

   ```text
   codex plugin marketplace add "."
   codex plugin add eve-map-assistant@personal
   ```

4. Fully restart Codex or start a new Codex process so it inherits the updated Windows PATH, then open a new task.
5. Use `@EVE Map Assistant`.

No `codex mcp add` command is required for a new Gate A installation. If the Plugin tools cannot start, verify that EVE Static Map Planner 0.5.0 or later is installed and restart Codex; do not add a development launcher or shell wrapper.

## Legacy Gate B migration

Codex 0.149.0 gives a same-named global MCP configuration precedence over a Plugin-bundled server. That is non-fatal, but the older registration masks the bundled command. After upgrading the map and Plugin, remove only the legacy global registration once:

```text
codex mcp remove eve-static-map
```

Then fully restart Codex. Do not run another `codex mcp add`; the Plugin supplies `eve-static-map`. The Map installer and Plugin never modify or remove Codex global configuration themselves.

## Usage

Query-only route example:

```text
@EVE Map Assistant
帮我算一下 Jita 到 Amarr 的普通路线和跳数，先不要显示在地图上。
```

Visual Mission example:

```text
@EVE Map Assistant
创建一个临时任务 Delve Move，显示普通路线，添加 RALLY 和 DESTINATION 标记，显示 5 LY 跳跃范围，并适配整个任务视图。
```

Temporary marker requests such as `标记一下 Jita` create a session-only Mission Marker. Persistent storage must be explicit:

```text
@EVE Map Assistant
把 Jita 永久保存为 Logistics。
```

Saved Marker read/create requires **Preferences > AI Control > Saved Marker Access**. If it is disabled, the Plugin reports the denial and does not substitute a temporary marker.

If the map is not running or AI Control is disabled, the MCP server still initializes and lists its tools, while map calls return `APP_DISCONNECTED`.

## Safety

EVE Map Assistant:

- uses only the fixed 22 `eve-static-map` tools;
- defaults ordinary marker requests to temporary Mission-owned state;
- reads or creates Saved Markers only through permission-gated tools after explicit user intent;
- cannot update, overwrite, delete, clear, tag, or add children to Saved Markers;
- does not mutate Ansiblex connections or preferences;
- does not read local databases or secrets; and
- does not use Shell, filesystem, database, or arbitrary HTTP fallbacks for map control.

## Version

Plugin version: `0.3.0`.

The Plugin version is independent from the EVE Static Map Planner application version.

## License

Licensed under the [MIT License](LICENSE).
