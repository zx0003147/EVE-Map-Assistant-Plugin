#!/usr/bin/env python3
"""Repository contract checks for EVE Map Assistant 0.7.0."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


EXPECTED_TOOLS = [
    "search_system",
    "get_system_info",
    "get_system_markers",
    "list_wormholes",
    "calculate_normal_route",
    "calculate_capital_route",
    "list_views",
    "get_current_view",
    "create_view",
    "rename_view",
    "switch_view",
    "delete_view",
    "get_active_missions",
    "get_mission",
    "list_eve_navigation_targets",
    "begin_mission",
    "focus_system",
    "create_wormhole",
    "show_normal_route",
    "show_capital_route",
    "remove_mission_route",
    "clear_mission_routes",
    "show_jump_range",
    "remove_jump_range",
    "clear_mission_jump_ranges",
    "add_mission_marker",
    "remove_mission_marker",
    "clear_mission_markers",
    "fit_mission",
    "clear_mission",
    "create_saved_marker",
    "send_mission_navigation_to_eve",
]

READ_TOOLS = {
    "search_system",
    "get_system_info",
    "get_system_markers",
    "list_wormholes",
    "calculate_normal_route",
    "calculate_capital_route",
    "list_views",
    "get_current_view",
    "get_active_missions",
    "get_mission",
    "list_eve_navigation_targets",
}

REQUIRED_SCENARIOS = {
    "exact system search",
    "abbreviated system search",
    "ambiguous system search",
    "system details",
    "unqualified route defaults normal",
    "query-only normal route",
    "visual normal mission",
    "list current wormholes",
    "create temporary wormhole",
    "duplicate wormhole is normal",
    "query normal route with wormholes",
    "visual normal route with wormholes",
    "query normal route without wormholes",
    "query normal route with ansiblex and wormholes",
    "wormhole deletion unavailable",
    "wormhole clear unavailable",
    "capital route missing range",
    "query-only capital route",
    "visual capital mission",
    "current AI mission routes",
    "current selected system unsupported",
    "marker read",
    "temporary marker default",
    "explicit permanent marker",
    "saved marker permission denied",
    "saved marker duplicate",
    "saved marker mutation protection",
    "map offline",
    "app disconnected error",
    "route tool error",
    "route calculation never auto sends to EVE",
    "explicit Mission Normal send to named character",
    "Mission send requires explicit character",
    "ambiguous Mission route is not sent",
    "Capital route send is prohibited",
    "manual draft send is prohibited",
    "Mission send preserves exact authored targets",
    "ambiguous EVE send is not blindly retried",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_tool_contract(skill: str) -> list[str]:
    match = re.search(r"## Tool contract and ownership\s+```text\s+(.*?)\s+```", skill, re.DOTALL)
    require(match is not None, "SKILL.md is missing its tool contract block")
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    plugin = root / "plugins" / "eve-map-assistant"
    skill_dir = plugin / "skills" / "eve-map-assistant"

    manifest = load_json(plugin / ".codex-plugin" / "plugin.json")
    mcp = load_json(plugin / ".mcp.json")
    marketplace = load_json(root / ".agents" / "plugins" / "marketplace.json")
    cases_document = load_json(root / "qa" / "eve-map-assistant-cases.json")
    capabilities_document = load_json(root / "qa" / "tool-capabilities.json")
    skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    openai_yaml = (skill_dir / "agents" / "openai.yaml").read_text(encoding="utf-8")
    readme = (root / "README.md").read_text(encoding="utf-8")

    require(manifest["name"] == "eve-map-assistant", "Unexpected plugin name")
    require(manifest["version"] == "0.7.0", "Capability/UX Plugin version must be 0.7.0")
    require(manifest["skills"] == "./skills/", "Plugin must point to bundled skills")
    require(manifest["mcpServers"] == "./.mcp.json", "Plugin must link the bundled MCP file")
    require(manifest["interface"]["capabilities"] == ["Read", "Write"], "Plugin capabilities changed")
    prompts = manifest["interface"]["defaultPrompt"]
    require(1 <= len(prompts) <= 3, "Plugin must expose one to three natural-language prompts")
    require(not any("_" in prompt or "tool" in prompt.lower() for prompt in prompts), "Starter prompts must not expose tool names")

    require(set(mcp) == {"mcpServers"}, "Bundled MCP file must use the mcpServers wrapper")
    require(set(mcp["mcpServers"]) == {"eve-static-map"}, "Plugin must bundle exactly eve-static-map")
    server = mcp["mcpServers"]["eve-static-map"]
    require(
        server == {"type": "http", "url": "http://127.0.0.1:27892/mcp"},
        "Bundled MCP must remain the fixed localhost Streamable HTTP endpoint",
    )

    entries = [entry for entry in marketplace["plugins"] if entry["name"] == manifest["name"]]
    require(marketplace["name"] == "personal", "Unexpected marketplace name")
    require(marketplace.get("interface") == {"displayName": "Personal"}, "Unexpected marketplace interface")
    require(len(entries) == 1, "Marketplace must expose the plugin exactly once")
    require(
        entries[0]["source"] == {"source": "local", "path": "./plugins/eve-map-assistant"},
        "Unexpected marketplace source",
    )
    require(entries[0]["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "Unexpected marketplace policy")

    require('value: "eve-static-map"' in openai_yaml, "Skill must declare its MCP dependency")
    require("$eve-map-assistant" in openai_yaml, "Default prompt must name the skill")
    require("allow_implicit_invocation: true" in openai_yaml, "Natural-language implicit invocation must remain enabled")
    require(extract_tool_contract(skill) == EXPECTED_TOOLS, "SKILL.md must contain exactly the canonical 32 tools")
    require(len(EXPECTED_TOOLS) == 32, "Validator must define exactly 32 canonical tools")
    wormhole_tools = [name for name in EXPECTED_TOOLS if "wormhole" in name]
    require(wormhole_tools == ["list_wormholes", "create_wormhole"], "Only Wormhole list/create tools may exist")
    require(
        not any(any(action in name for action in ["remove", "delete", "clear", "replace", "edit"]) for name in wormhole_tools),
        "A forbidden Wormhole mutation tool exists",
    )

    lowered_skill = skill.lower()
    for required_rule in [
        "smallest tool chain",
        "currently selected system",
        "user-owned route drafts",
        "unqualified route",
        "useansiblex",
        "usewormholes",
        "do not call both calculate and show",
        "a plain marker request is temporary",
        "use `create_saved_marker` only when the user clearly asks",
        "never update, overwrite, replace, delete, clear, add children to, or change tags",
        "app_disconnected",
        "do not try another control path",
        "view labels are editable and unique",
        "never send a label where a `viewid` is required",
        "omit `viewid`",
        "wormholes are not mission-owned or view-owned",
        "ai cannot remove wormhole connections",
        "already_exists",
        "planning views and ai missions are session-only",
        "send_mission_navigation_to_eve` is an external eve mutation",
        "manual user drafts are not visible to this tool and are structurally prohibited",
        "capital routes are structurally prohibited",
        "require the user to identify one returned `characterid`, even when only one character is available",
        "start and calculated transit systems are excluded",
        "a stale displayed calculation does not block sending and must not trigger recalculation",
        "without compression, sampling, deduplication, or truncation",
        "do not retry an ambiguous external mutation blindly",
    ]:
        require(required_rule in lowered_skill, f"SKILL.md is missing decision rule: {required_rule}")
    obsolete_restart_claim = "restored by the map across " + "restarts"
    require(obsolete_restart_claim not in lowered_skill, "SKILL.md still claims Missions survive restarts")
    require(
        re.search(r"ai\s+(?:can|may|should)\s+(?:remove|delete|clear|replace|edit|update)\s+(?:temporary\s+)?wormhole", lowered_skill)
        is None,
        "SKILL.md claims AI can mutate existing Wormholes",
    )

    artifact_text = "\n".join(
        [skill, openai_yaml, readme, json.dumps(manifest), json.dumps(mcp), json.dumps(cases_document), json.dumps(capabilities_document)]
    )
    lowered_artifacts = artifact_text.lower()
    for forbidden in ["session.key", "bearer token", "fc ping", "discord parser", "static.db"]:
        require(forbidden not in lowered_artifacts, f"Forbidden private or out-of-scope detail found: {forbidden}")
    require(re.search(r"(?i)[a-z]:[\\/]+users[\\/]+[^<%$\\/\s]+", artifact_text) is None, "Artifacts contain a concrete user path")
    require(re.search(r"\b30\d{6}\b", skill) is None, "SKILL.md must not hard-code EVE system IDs")

    require(capabilities_document["expectedToolCount"] == 32, "Capability fixture must declare 32 tools")
    capabilities = capabilities_document["tools"]
    require([tool["name"] for tool in capabilities] == EXPECTED_TOOLS, "Capability fixture must follow the canonical tool order")
    require(len(capabilities) == 32, "Capability fixture must contain exactly 32 tools")
    for tool in capabilities:
        expected_access = "READ" if tool["name"] in READ_TOOLS else "WRITE"
        require(tool["access"] == expected_access, f"Wrong access class for {tool['name']}")
        for field in ["purpose", "inputSchema", "sideEffects", "expectedResult", "whenToUse", "preconditions", "commonSequence"]:
            require(field in tool and tool[field] not in (None, ""), f"{tool['name']} is missing {field}")
    require(sum(tool["access"] == "READ" for tool in capabilities) == 11, "Expected eleven read tools")
    require(sum(tool["access"] == "WRITE" for tool in capabilities) == 21, "Expected twenty-one write tools")
    capability_by_name = {tool["name"]: tool for tool in capabilities}
    for route_tool in ["calculate_normal_route", "show_normal_route"]:
        require("useWormholes" in capability_by_name[route_tool]["inputSchema"], f"{route_tool} must expose useWormholes")
        require("wormholeJumps" in capability_by_name[route_tool]["expectedResult"], f"{route_tool} must report wormholeJumps")
    require(capability_by_name["list_wormholes"]["access"] == "READ", "list_wormholes must be read-only")
    require(capability_by_name["create_wormhole"]["access"] == "WRITE", "create_wormhole must mutate topology")
    require("already_exists" in capability_by_name["create_wormhole"]["expectedResult"], "Duplicate semantics are missing")
    require(capability_by_name["list_eve_navigation_targets"]["access"] == "READ", "EVE targets must be read-only")
    send_navigation = capability_by_name["send_mission_navigation_to_eve"]
    require(send_navigation["access"] == "WRITE", "EVE navigation send must be a write")
    require(send_navigation["inputSchema"] == "missionId: string; routeId: string; characterId: string", "EVE send must require three explicit identities")
    require("replaces" in send_navigation["sideEffects"].lower(), "EVE send must disclose replacement semantics")
    require("partial" in send_navigation["sideEffects"].lower(), "EVE send must disclose partial mutation risk")
    require(any("manual draft" in item.lower() and "capital" in item.lower() for item in send_navigation["preconditions"]), "EVE send exclusions are missing")

    require("real model selection remains Human QA" in cases_document["suite"], "Scenario suite must not claim model-choice automation")
    cases = cases_document["cases"]
    require(len(cases) >= 25, "Expected at least 25 natural-language behavior contracts")
    case_names = {case["name"] for case in cases}
    require(REQUIRED_SCENARIOS <= case_names, "Required behavior scenarios are incomplete")
    all_tools = set(EXPECTED_TOOLS)
    for case in cases:
        required = set(case["requiredTools"])
        forbidden = set(case["forbiddenTools"])
        require(required <= all_tools and forbidden <= all_tools, f"{case['name']} declares an unknown tool")
        require(required.isdisjoint(forbidden), f"{case['name']} requires and forbids the same tool")
        require(bool(case["prompt"].strip()), f"{case['name']} is missing a prompt")
        require(bool(case["expectedBehavior"].strip()), f"{case['name']} is missing expected behavior")
    explicit_send_case = next(case for case in cases if case["name"] == "explicit Mission Normal send to named character")
    require(
        set(explicit_send_case["requiredTools"]) == {
            "get_active_missions", "get_mission", "list_eve_navigation_targets", "send_mission_navigation_to_eve"
        },
        "Explicit EVE send scenario must resolve Mission, route, and character before sending",
    )
    for case_name in [
        "route calculation never auto sends to EVE",
        "Mission send requires explicit character",
        "ambiguous Mission route is not sent",
        "Capital route send is prohibited",
        "manual draft send is prohibited",
    ]:
        case = next(item for item in cases if item["name"] == case_name)
        require("send_mission_navigation_to_eve" in case["forbiddenTools"], f"{case_name} must forbid EVE mutation")

    for phrase in [
        "Start EVE Static Map Planner 1.2.0 or later",
        "Install or enable the **EVE Map Assistant** Plugin",
        "Open a new AI task",
        "Ask naturally",
        "Plugin version: `0.7.0`",
        "Canonical 32-tool capability fixture",
        "assistant can list current temporary Wormholes and create a new one, but it cannot delete",
        "Only an explicitly requested Mission-owned Normal route can be sent to an explicitly selected connected EVE character",
    ]:
        require(phrase in readme, f"README is missing simple user step: {phrase}")

    print(f"EVE Map Assistant repository validation passed (32 tools: 11 read / 21 write; {len(cases)} behavior contracts; Plugin 0.7.0).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, json.JSONDecodeError) as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(1)
