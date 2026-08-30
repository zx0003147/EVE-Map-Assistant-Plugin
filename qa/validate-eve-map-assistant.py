#!/usr/bin/env python3
"""Repository contract checks for EVE Map Assistant 0.5.0."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


EXPECTED_TOOLS = [
    "search_system",
    "get_system_info",
    "get_system_markers",
    "calculate_normal_route",
    "calculate_capital_route",
    "get_active_missions",
    "get_mission",
    "begin_mission",
    "focus_system",
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
]

READ_TOOLS = {
    "search_system",
    "get_system_info",
    "get_system_markers",
    "calculate_normal_route",
    "calculate_capital_route",
    "get_active_missions",
    "get_mission",
}

REQUIRED_SCENARIOS = {
    "exact system search",
    "abbreviated system search",
    "ambiguous system search",
    "system details",
    "unqualified route defaults normal",
    "query-only normal route",
    "visual normal mission",
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
    require(manifest["version"] == "0.5.0", "Capability/UX Plugin version must be 0.5.0")
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
    require(extract_tool_contract(skill) == EXPECTED_TOOLS, "SKILL.md must contain exactly the canonical 22 tools")

    lowered_skill = skill.lower()
    for required_rule in [
        "smallest tool chain",
        "currently selected system",
        "user-owned route drafts",
        "unqualified route",
        "useansiblex",
        "do not call both calculate and show",
        "a plain marker request is temporary",
        "use `create_saved_marker` only when the user clearly asks",
        "never update, overwrite, replace, delete, clear, add children to, or change tags",
        "app_disconnected",
        "do not try another control path",
    ]:
        require(required_rule in lowered_skill, f"SKILL.md is missing decision rule: {required_rule}")

    artifact_text = "\n".join(
        [skill, openai_yaml, readme, json.dumps(manifest), json.dumps(mcp), json.dumps(cases_document), json.dumps(capabilities_document)]
    )
    lowered_artifacts = artifact_text.lower()
    for forbidden in ["session.key", "bearer token", "fc ping", "discord parser", "static.db"]:
        require(forbidden not in lowered_artifacts, f"Forbidden private or out-of-scope detail found: {forbidden}")
    require(re.search(r"(?i)[a-z]:[\\/]+users[\\/]+[^<%$\\/\s]+", artifact_text) is None, "Artifacts contain a concrete user path")
    require(re.search(r"\b30\d{6}\b", skill) is None, "SKILL.md must not hard-code EVE system IDs")

    require(capabilities_document["expectedToolCount"] == 22, "Capability fixture count changed")
    capabilities = capabilities_document["tools"]
    require([tool["name"] for tool in capabilities] == EXPECTED_TOOLS, "Capability fixture must follow the canonical tool order")
    require(len(capabilities) == 22, "Capability fixture must contain exactly 22 tools")
    for tool in capabilities:
        expected_access = "READ" if tool["name"] in READ_TOOLS else "WRITE"
        require(tool["access"] == expected_access, f"Wrong access class for {tool['name']}")
        for field in ["purpose", "inputSchema", "sideEffects", "expectedResult", "whenToUse", "preconditions", "commonSequence"]:
            require(field in tool and tool[field] not in (None, ""), f"{tool['name']} is missing {field}")
    require(sum(tool["access"] == "READ" for tool in capabilities) == 7, "Expected seven read tools")
    require(sum(tool["access"] == "WRITE" for tool in capabilities) == 15, "Expected fifteen write tools")

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

    for phrase in [
        "Start EVE Static Map Planner 0.6.0 or later",
        "Install or enable the **EVE Map Assistant** Plugin",
        "Open a new AI task",
        "Ask naturally",
        "Plugin version: `0.5.0`",
    ]:
        require(phrase in readme, f"README is missing simple user step: {phrase}")

    print("EVE Map Assistant repository validation passed (22 tools: 7 read / 15 write; 27 behavior contracts; Plugin 0.5.0).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, json.JSONDecodeError) as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(1)
