"""Starter agent for Plugboard.

Importing this package registers the manifest; the host names it in
PLUGBOARD_EXTRA_AGENTS. Nothing else happens at import time.
"""

from pathlib import Path

from plugboard import AgentManifest, register

from plugboard_starter.tools import make_tools

register(
    AgentManifest(
        name="starter",
        title="Starter",
        routing_description=(
            "TODO: what this agent answers, the phrases a user would use "
            "('...', '...'), what to pass in, what comes back, and what it cannot do."
        ),
        persona=(
            "TODO: the method in order, how to use each tool, what the user already "
            "sees (so the result is a short summary), what to do when something is "
            "missing. Never invent data."
        ),
        tools=make_tools,
        requires=[],
        examples=["TODO: a prompt as the user would type it", "TODO: another"],
        source="https://github.com/plugboard-hq/plugboard-agent-starter",
        frontend=str(Path(__file__).parent / "static" / "starter.js"),
        surfaces=[{"kind": "artifact", "component": "StarterPane", "title": "Starter"}],
        config_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "title": "Row limit",
                    "description": "Most rows the example tool returns",
                    "default": 20,
                },
            },
        },
        max_iters=4,
    )
)
