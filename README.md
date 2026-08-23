# EVE Map Assistant

EVE Map Assistant is a Codex Plugin and Skill for controlling EVE Static Map Planner through the separately registered `eve-static-map` MCP server. It plans and visualizes systems, normal and capital routes, jump ranges, markers, and temporary AI-owned map missions.

Repository URL: pending publication.

## Requirements

- Windows
- EVE Static Map Planner installed
- **Preferences > AI Control** enabled in the map application
- Codex with local Plugin and STDIO MCP support
- The `eve-static-map` MCP server registered and enabled

## Architecture

```text
Codex
  -> EVE Map Assistant Skill
  -> eve-static-map MCP
  -> EVE Map MCP Bridge
  -> EVE Static Map Planner
```

The Plugin follows Gate B: it does not bundle `.mcp.json` or embed a machine-specific bridge path. MCP registration remains separate from Plugin distribution.

## Install Plugin from this repository

From this repository root, add its local marketplace and install the Plugin:

```text
codex plugin marketplace add "."
codex plugin add eve-map-assistant@personal
```

Start a new Codex task after installation so the Plugin, Skill, and MCP dependency are loaded. Do not remove a currently working installation merely to test this repository; migrate it only when you intend to switch sources.

## MCP Registration

The Plugin does not automatically register the local MCP bridge. Register the executable installed with EVE Static Map Planner by using its actual path:

```text
codex mcp add eve-static-map -- "<path-to-installed-EVE Map MCP Bridge.exe>"
codex mcp get eve-static-map
```

Start the bridge executable directly. Do not use a PowerShell, cmd, or script wrapper, and do not place a username, control port, or credential in the Plugin files.

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

## Safety

EVE Map Assistant:

- uses only the existing 20 `eve-static-map` tools;
- controls temporary Mission-owned state only;
- does not mutate saved markers, Ansiblex connections, or preferences;
- does not read local databases or secrets; and
- does not use Shell, filesystem, database, or arbitrary HTTP fallbacks for map control.

## Version

Plugin version: `0.1.0`.

The Plugin version is independent from the EVE Static Map Planner application version.

## License

Licensed under the [MIT License](LICENSE).
