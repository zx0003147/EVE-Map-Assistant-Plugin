# EVE Map Assistant

Ask naturally about EVE systems, routes, jump ranges, temporary Mission markers, and permission-gated Saved Markers in EVE Static Map Planner.

## Start

1. Start EVE Static Map Planner 1.0.0 or later and enable **Preferences > AI Control**.
2. Install or enable the **EVE Map Assistant** Plugin.
3. Open a new AI task so the Plugin is loaded.
4. Ask naturally, for example: `Jita 在哪？` or `Jita 到 Amarr 怎么走？`

Saved Marker reads and permanent creates also require **Preferences > AI Control > Saved Marker Access**. Ordinary marker requests stay temporary and disappear with the AI Control session.

If the map is unavailable, start EVE Static Map Planner and enable AI Control; no PATH, launcher, PowerShell, or manual MCP configuration is required.

## Local development install

```text
codex plugin marketplace add "."
codex plugin add eve-map-assistant@personal
```

Open a new task after reinstalling. The Plugin uses the map application's fixed localhost integration and does not bundle an executable or change EVE client destinations.

## Development

- Repository contract: `qa/validate-eve-map-assistant.py`
- Natural-language behavior contracts: `qa/eve-map-assistant-cases.json`
- Canonical 28-tool capability fixture: `qa/tool-capabilities.json`

Plugin version: `0.5.0`. Licensed under the [MIT License](LICENSE).
