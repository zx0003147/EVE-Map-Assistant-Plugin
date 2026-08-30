# EVE Map Assistant

EVE Map Assistant is a Codex Plugin and Skill for controlling EVE Static Map Planner. Plugin 0.4.0 connects the bundled `eve-static-map` definition to the localhost MCP endpoint served by EVE Static Map Planner 0.6.0 or later.

Repository: [zx0003147/EVE-Map-Assistant-Plugin](https://github.com/zx0003147/EVE-Map-Assistant-Plugin)

## Requirements

- Windows
- EVE Static Map Planner 0.6.0 or later installed and running
- **Preferences > AI Control** enabled in the running map application
- Codex with local Plugin and Streamable HTTP MCP support

## Architecture

```text
Codex
  -> EVE Map Assistant Skill
  -> bundled eve-static-map MCP definition
  -> EVE Static Map Planner localhost MCP endpoint
  -> EVE Static Map Planner AI Control
```

The Plugin contains only metadata, its Skill, and a small fixed-URL MCP definition. It contains no executable, JVM runtime, shell wrapper, user profile path, or Control credential. The Map application owns the localhost server; the Plugin is only a client configuration.

## Install

1. Install or upgrade to EVE Static Map Planner 0.6.0 or later.
2. Start the map and enable **Preferences > AI Control**.
3. Add this local marketplace and install the Plugin from this repository:

   ```text
   codex plugin marketplace add "."
   codex plugin add eve-map-assistant@personal
   ```

4. Open a new Codex task after the Plugin is installed and the Map is running.
5. Use `@EVE Map Assistant`.

No `codex mcp add` command is required for a new Gate A installation. If the Plugin tools are unavailable, verify that EVE Static Map Planner 0.6.0 or later is running with AI Control enabled, then open a new task. Do not add a development launcher or shell wrapper.

## Legacy Gate B migration

Codex 0.149.0 gives a same-named global MCP configuration precedence over a Plugin-bundled server. That is non-fatal, but the older registration masks the bundled command. After upgrading the map and Plugin, remove only the legacy global registration once:

```text
codex mcp remove eve-static-map
```

Then open a new Codex task. Do not run another `codex mcp add`; the Plugin supplies `eve-static-map`. The Map application and Plugin never modify or remove Codex global configuration themselves.

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

Initial tags can be included in the same permanent create request, for example `永久保存 1DQ，并加 staging 和 strategic 标签`. Tags are create-time data only; the Plugin cannot add or remove tags on an existing Saved Marker.

Saved Marker read/create requires **Preferences > AI Control > Saved Marker Access**. If it is disabled, the Plugin reports the denial and does not substitute a temporary marker.

When the Map is running but AI Control is disabled, the MCP server still initializes and lists its tools, while map calls return `APP_DISCONNECTED`. If the Map is not running, Codex remains usable but this Plugin's MCP connection is unavailable.

## Safety

EVE Map Assistant:

- uses only the fixed 22 `eve-static-map` tools;
- defaults ordinary marker requests to temporary Mission-owned state;
- reads or creates Saved Markers only through permission-gated tools after explicit user intent;
- can set supported initial tags only while creating a Saved Marker;
- cannot update, overwrite, delete, clear, or change tags or children on an existing Saved Marker;
- does not mutate Ansiblex connections or preferences;
- does not read local databases or secrets; and
- does not use Shell, filesystem, database, or arbitrary HTTP fallbacks for map control.

## Version

Plugin version: `0.4.0`.

The Plugin version is independent from the EVE Static Map Planner application version.

## License

Licensed under the [MIT License](LICENSE).
