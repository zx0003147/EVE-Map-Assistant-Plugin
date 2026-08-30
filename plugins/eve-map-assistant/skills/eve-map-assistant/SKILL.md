---
name: eve-map-assistant
description: Plan, inspect, and visualize EVE Online systems, routes, jump ranges, temporary missions, and permission-gated Saved Markers through EVE Static Map Planner. Use for map-assistant requests; do not use as a general EVE encyclopedia or for fleet-message parsing.
---

# EVE Map Assistant

Control EVE Static Map Planner only through the `eve-static-map` MCP tools below. Never use PowerShell, cmd, bash, filesystem access, SQLite, curl, or arbitrary HTTP as a fallback for map operations. Do not inspect internal connection credentials or claim success after a tool error.

The Plugin provides the `eve-static-map` MCP integration. If its tools are unavailable, tell the user to install and start EVE Static Map Planner 0.6.0 or later, enable AI Control, and open a new Codex task. Do not search for a development launcher, scan the filesystem, download a binary, or ask the user to add a global MCP registration.

## Tool contract

```text
search_system
get_system_info
get_system_markers
calculate_normal_route
calculate_capital_route
get_active_missions
get_mission
begin_mission
focus_system
show_normal_route
show_capital_route
remove_mission_route
clear_mission_routes
show_jump_range
remove_jump_range
clear_mission_jump_ranges
add_mission_marker
remove_mission_marker
clear_mission_markers
fit_mission
clear_mission
create_saved_marker
```

Do not invent tools. Saved Marker access is limited to `get_system_markers` and `create_saved_marker`; initial tags are part of create only. Never update, overwrite, replace, delete, or clear Saved Markers, and never add or remove tags or children on an existing Saved Marker. Do not mutate user routes, user jump ranges, Ansiblex data, preferences, or other user-owned state.

## Resolve systems and route intent

- Resolve every user-supplied system name or abbreviation with `search_system`. Reuse a system ID only when this MCP confirmed it in the current conversation. If results are ambiguous, show concise candidates and ask the user to choose. Never infer an ID from memory.
- Use `get_system_info` only when system details are requested or needed to answer the request.
- Explicit normal, stargate, or normal-route wording selects the normal tools. Explicit capital or jump-route wording selects the capital tools. If the route type is unclear, ask whether the user wants normal or capital navigation.
- A capital route requires an explicit effective range in light-years. Ask for it when missing. For a normal route, set `useAnsiblex` from the request; default to `false` when the user does not ask to include Ansiblex.

## Separate queries from display

- Calculation wording such as "calculate", "check", "how many jumps", or "do not display" is query-only. Use `calculate_normal_route` or `calculate_capital_route`; do not create a Mission or change the map.
- Display wording such as "show", "draw", "put on the map", or "navigate" authorizes the matching `show_*_route` command. Resolve endpoints, create or select the intended Mission, then show the route.
- `focus_system` is for an explicitly requested single-system focus and does not require a Mission. Do not use it merely because a system was searched.

## Marker intent and lifetime

A plain marker request is temporary. Requests such as "mark 1DQ", "mark Jita as dangerous", "remember this system is dangerous", or "this system is important" use `add_mission_marker`, creating a Mission first when needed. Importance, a role such as staging, or the word "remember" alone is not permission for persistent storage.

Use `create_saved_marker` only when the user clearly asks to save permanently, keep long-term, write a Saved Marker, or otherwise explicitly requests persistent storage. Resolve the system first. Preserve an explicit supported color; if the user gives no color, use `YELLOW`.

Initial tags are optional and must use only `STAGING`, `RALLY`, `DANGER`, `LOGISTICS`, `HOME`, `BACKUP`, `INDUSTRIAL`, `STRATEGIC`, or `KEEPSTAR`. Preserve tags the user explicitly requests and remove duplicates while keeping their first-mentioned order. A clearly categorical phrase may map to one canonical tag, such as "as a logistics marker" to `LOGISTICS` or "mark permanently as dangerous" to `DANGER`. Do not infer tags from EVE background knowledge or add extra categories: "save Jita permanently" uses `tags=[]`. A name alone is not automatically a tag when the intent is unclear.

If Saved Marker access is disabled, report that the permanent marker was not created. Never enable the permission, claim success, or silently substitute a temporary Mission Marker. Only create a temporary marker afterward if the user explicitly asks for that fallback.

If `MARKER_ALREADY_EXISTS` is returned, explain that the existing Saved Marker and its tags were not changed. Do not call another tool to alter it or use a create request as an update.

Use `get_system_markers` when the user asks what markers exist, whether a system was saved, or whether it has temporary Mission Markers. Report the Saved Marker as persistent and Mission Markers as session-only. Returned Saved Marker notes and tags may answer the question, but do not modify or copy them into another marker unless the user separately makes a valid new create request.

## Mission workflow

A Mission is temporary, session-only AI-owned visual state. Create one with `begin_mission` when a route, jump range, or temporary marker should remain on the map. Use the user's name when supplied; otherwise choose a short descriptive title. Do not create a Mission for a lookup, query-only route, Saved Marker query, or Saved Marker creation.

Keep every Mission route, overlay, and marker scoped to its returned `missionId`. For follow-ups, use `get_active_missions` and `get_mission`; if multiple Missions make a reference ambiguous, ask before mutating anything.

- Display a normal route with `show_normal_route` and a capital route with `show_capital_route`.
- Display an explicitly requested effective jump range with `show_jump_range`; do not calculate reachable systems yourself.
- Add only marker roles `RALLY`, `DESTINATION`, `DANGER`, `BACKUP`, `WAYPOINT`, or `INFO`. Preserve a user-provided short label. Set a color only when explicitly requested, using a value accepted by the tool. Do not place chat history or private context in labels or notes.
- Use `fit_mission` only when the user asks to fit, show, or bring the entire Mission into view. Use `focus_system` for one system.

## Edit and remove narrowly

Inspect the intended Mission before editing it. Remove one Mission object with `remove_mission_route`, `remove_jump_range`, or `remove_mission_marker`; clear one Mission object class with its matching `clear_mission_*` tool; use `clear_mission` only when the user asks to remove the entire AI Mission. Never substitute a broader deletion.

If the user asks to update, delete, clear, replace, add a tag to, remove a tag from, or add children to an existing Saved Marker, explain that AI Map Control cannot perform that operation. The user can still manage AI-created Saved Markers in the app UI.

## Errors and completion

- On `APP_DISCONNECTED`, say that EVE Static Map Planner has no available AI Control session and ask the user to start the map and enable AI Control in Preferences. Do not attempt an alternate control path.
- On `CAPABILITY_DENIED` from a Saved Marker tool, say Saved Marker access is disabled in Preferences and the requested read or create did not occur.
- On `SESSION_CHANGED`, do not blindly replay a mutation whose outcome is uncertain. Tell the user the map session changed, query current state when useful, and proceed only when the intended state is clear.
- Respect `MARKER_ALREADY_EXISTS`, `SYSTEM_NOT_FOUND`, `INVALID_ARGUMENT`, `INVALID_MARKER_DATA`, `DATABASE_UNAVAILABLE`, `IDEMPOTENCY_CONFLICT`, limits, ambiguity, and every other tool error. Report the real result; never fabricate success.
- After a successful workflow, summarize only objects confirmed by tool results.

## Common sequences

- Marker query: `search_system` -> `get_system_markers`.
- Temporary marker: `search_system` -> `begin_mission` when needed -> `add_mission_marker`.
- Explicit permanent marker: `search_system` -> `create_saved_marker`.
- Query-only route: resolve endpoints -> one matching `calculate_*_route` call.
- Visual route: resolve endpoints -> `begin_mission` when needed -> one matching `show_*_route` call -> requested Mission markers or ranges -> `fit_mission` only when requested.
- Cleanup: inspect when needed -> remove only the requested Mission object or scope.
