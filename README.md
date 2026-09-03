# EVE Map Assistant

**EVE Map Assistant is the AI companion plugin for EVE Static Map Planner. It lets Codex query and control the running EVE map in natural language — find solar systems, calculate or display routes and jump ranges, manage AI Missions and markers, list or create temporary Wormhole connections, and explicitly send an identified Mission Normal route to EVE.**

**This repository does not contain the map application itself. EVE Static Map Planner 1.2.0 or later must be running with AI Control enabled.**

## Start

1. Start EVE Static Map Planner 1.2.0 or later and enable **Preferences > AI Control**.
2. Install or enable the **EVE Map Assistant** Plugin.
3. Open a new AI task so the Plugin is loaded.
4. Ask naturally, for example: `Jita 在哪？` or `Jita 到 Amarr 怎么走？`

Saved Marker reads and permanent creates also require **Preferences > AI Control > Saved Marker Access**. Ordinary marker requests stay temporary and disappear with the AI Control session.

Wormhole AI access is intentionally limited: the assistant can list current temporary Wormholes and create a new one, but it cannot delete, clear, replace, or edit them. Remove Wormholes manually in the map's Wormhole Manager or a system's right-click menu.

Normal and capital routes can include ordered required Waypoints. The assistant resolves each named stop, preserves the supplied order (including non-adjacent repeats), and submits the complete intent as one atomic route; if any segment fails, no partial Mission route is added. Destination may be omitted when the last Waypoint should be the endpoint.

Only an explicitly requested Mission-owned Normal route can be sent to an explicitly selected connected EVE character. Sending replaces that character's existing EVE navigation with the stored route's exact ordered Waypoints plus optional Destination; Start and calculated transit systems are excluded. Manual drafts, Capital routes, automatic character choice, compression, and silent retries after ambiguous failures are prohibited.

If the map is unavailable, start EVE Static Map Planner and enable AI Control; no PATH, launcher, PowerShell, or manual MCP configuration is required.

## Local development install

```text
codex plugin marketplace add "."
codex plugin add eve-map-assistant@personal
```

Open a new task after reinstalling. The Plugin uses the map application's fixed localhost integration and does not bundle an executable. It changes EVE navigation only through the explicit Mission Normal send workflow described above.

## Development

- Repository contract: `qa/validate-eve-map-assistant.py`
- Natural-language behavior contracts: `qa/eve-map-assistant-cases.json`
- Canonical 32-tool capability fixture: `qa/tool-capabilities.json`

Plugin version: `0.7.0`. Licensed under the [MIT License](LICENSE).
