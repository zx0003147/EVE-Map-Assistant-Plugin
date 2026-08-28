#!/usr/bin/env python3
"""Static contract checks for the repo-local EVE Map Assistant plugin."""

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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def extract_tool_contract(skill: str) -> list[str]:
    match = re.search(r"## Tool contract\s+```text\s+(.*?)\s+```", skill, re.DOTALL)
    require(match is not None, "SKILL.md is missing its tool contract block")
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    plugin = root / "plugins" / "eve-map-assistant"
    skill_dir = plugin / "skills" / "eve-map-assistant"
    skill_path = skill_dir / "SKILL.md"
    openai_yaml_path = skill_dir / "agents" / "openai.yaml"
    manifest_path = plugin / ".codex-plugin" / "plugin.json"
    mcp_path = plugin / ".mcp.json"
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    cases_path = root / "qa" / "eve-map-assistant-cases.json"
    readme_path = root / "README.md"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
    skill = skill_path.read_text(encoding="utf-8")
    openai_yaml = openai_yaml_path.read_text(encoding="utf-8")
    readme = readme_path.read_text(encoding="utf-8")

    require(manifest["name"] == "eve-map-assistant", "Unexpected plugin name")
    require(manifest["version"] == "0.3.0", "Phase 5 Plugin version must be 0.3.0")
    require(manifest["skills"] == "./skills/", "Plugin must point to bundled skills")
    require(manifest["mcpServers"] == "./.mcp.json", "Plugin must link the bundled MCP companion file")
    require(set(mcp) == {"mcpServers"}, "Bundled MCP file must use the current mcpServers wrapper")
    require(set(mcp["mcpServers"]) == {"eve-static-map"}, "Plugin must bundle exactly eve-static-map")
    server = mcp["mcpServers"]["eve-static-map"]
    require(server == {"command": "eve-map-mcp.exe"}, "Bundled MCP must use only the stable launcher command")
    command = server["command"]
    require(not Path(command).is_absolute() and ":" not in command and "/" not in command and "\\" not in command,
            "Bundled MCP command must be a portable executable name")
    require(not any(shell in command.lower() for shell in ["powershell", "cmd", "bash", ".bat", ".ps1"]),
            "Bundled MCP command must not use a shell or wrapper")

    entries = [entry for entry in marketplace["plugins"] if entry["name"] == manifest["name"]]
    require(marketplace["name"] == "personal", "Unexpected marketplace name")
    require(marketplace.get("interface") == {"displayName": "Personal"}, "Unexpected marketplace interface")
    require(len(entries) == 1, "Marketplace must expose the plugin exactly once")
    require(entries[0]["source"] == {"source": "local", "path": "./plugins/eve-map-assistant"},
            "Unexpected marketplace source")
    require(entries[0]["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "Unexpected marketplace policy")
    require(entries[0]["category"] == "Productivity", "Unexpected marketplace category")

    require('value: "eve-static-map"' in openai_yaml, "Skill must declare the bundled MCP dependency")
    require("plugin-bundled local mcp integration" in openai_yaml.lower(), "Dependency description must state Gate A ownership")
    require("transport:" not in openai_yaml and "url:" not in openai_yaml, "Dependency must not invent a transport or URL")
    require(extract_tool_contract(skill) == EXPECTED_TOOLS, "SKILL.md tool contract must contain exactly the fixed 22 tools")

    artifact_text = "\n".join([
        skill,
        openai_yaml,
        readme,
        json.dumps(manifest),
        json.dumps(mcp),
        json.dumps(marketplace),
        json.dumps(cases),
    ])
    lowered = artifact_text.lower()
    for forbidden in [
        "session.key",
        "bearer token",
        "localhost:",
        "127.0.0.1:",
        "fc ping",
        "discord parser",
        "static.db",
    ]:
        require(forbidden not in lowered, f"Forbidden private detail or out-of-scope feature found: {forbidden}")
    require(
        re.search(r"(?i)[a-z]:[\\/]+users[\\/]+[^<%$\\/\s]+", artifact_text) is None,
        "Step 4 artifacts must not contain a concrete Windows user profile path",
    )
    require(re.search(r"\b30\d{6}\b", skill) is None, "SKILL.md must not hard-code EVE system IDs")
    require("only through the `eve-static-map` mcp tools" in skill.lower(), "SKILL.md must prohibit non-MCP map control")
    require(
        "never use powershell, cmd, bash, filesystem access, sqlite, curl, or arbitrary http as a fallback" in skill.lower(),
        "SKILL.md must explicitly prohibit shell, filesystem, database, and HTTP fallbacks",
    )
    require("saved markers" in skill.lower() and "ansiblex" in skill.lower(), "SKILL.md must protect user-owned state")
    for required_rule in [
        "a plain marker request is temporary",
        "importance, a role such as staging, or the word \"remember\" alone is not permission",
        "use `create_saved_marker` only when the user clearly asks",
        "never enable the permission, claim success, or silently substitute",
        "the existing saved marker and its tags were not changed",
        "report the saved marker as persistent and mission markers as session-only",
        "initial tags are optional",
        "do not infer tags from eve background knowledge",
        "never add or remove tags or children on an existing saved marker",
    ]:
        require(required_rule in skill.lower(), f"SKILL.md is missing Saved Marker safety rule: {required_rule}")

    all_tools = set(EXPECTED_TOOLS)
    case_names = {case["name"] for case in cases}
    require(case_names == {
        "query-only normal route",
        "visual normal mission",
        "visual capital mission",
        "disconnected safety",
        "temporary marker default",
        "explicit permanent marker",
        "saved marker permission denied",
        "saved marker duplicate",
        "saved and Mission marker query",
        "ambiguous remember stays temporary",
        "saved marker mutation protection",
        "explicit saved marker tags",
        "semantic saved marker tag",
        "saved marker no implicit tags",
        "duplicate saved marker tag protection",
    }, "Behavior contract cases are incomplete")
    for case in cases:
        required = set(case["requiredTools"])
        forbidden = set(case["forbiddenTools"])
        require(required <= all_tools and forbidden <= all_tools, f"{case['name']} declares an unknown tool")
        require(required.isdisjoint(forbidden), f"{case['name']} requires and forbids the same tool")
        require(bool(case.get("expectedBehavior", "").strip()), f"{case['name']} is missing expected behavior")

    require("EVE Static Map Planner 0.5.0 or later" in readme, "README must state the Saved Marker prerequisite")
    require("Plugin version: `0.3.0`" in readme, "README must state the independent Plugin version")
    require("No `codex mcp add` command is required" in readme, "README must make Gate A the normal install path")
    require("codex mcp remove eve-static-map" in readme, "README must include the one-time Gate B migration")
    require("fully restart Codex" in readme, "README must explain Windows process environment refresh")
    require("codex plugin marketplace add \".\"" in readme, "README must include local marketplace installation")
    require("codex plugin add eve-map-assistant@personal" in readme, "README must include the Plugin install command")

    print("EVE Map Assistant contract validation passed (22 tools, atomic Saved Marker create tags gated, 15 behavior cases).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, json.JSONDecodeError) as failure:
        print(f"ERROR: {failure}", file=sys.stderr)
        raise SystemExit(1)
