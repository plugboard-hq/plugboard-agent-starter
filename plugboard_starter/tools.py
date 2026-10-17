"""Tools for the Starter agent.

Every tool reads the turn through ``current_turn()``: it records one
``tool_call`` summary on every path, shows results as widgets, publishes rows
as datasets so other agents can use them by id, and returns plain text the
model can act on. Expected failures are returned, not raised.
"""

from __future__ import annotations

from collections.abc import Callable

from plugboard.artifacts import Dataset
from plugboard.registry import registry
from plugboard.turn import current_turn
from plugboard.widgets import TableWidget


def _settings() -> dict:
    """Settings are read at call time; the console may have changed them."""
    return registry.get("starter").settings


def make_tools() -> list[Callable]:
    def example(query: str) -> str:
        """TODO: one sentence the model reads to decide when to call this, what
        `query` is, and what comes back."""
        turn = current_turn()
        limit = int(_settings().get("limit", 20))
        try:
            rows = [[query, i] for i in range(1, 4)][:limit]  # TODO: the real work
        except Exception as exc:  # noqa: BLE001 - expected failures are returned as text
            turn.tool_call("example", {"query": query}, f"failed: {exc}")
            return f"failed: {exc}"
        dataset = turn.artifacts.publish(
            Dataset(title=f"Example for {query}", columns=["query", "n"], rows=rows,
                    created_by="starter")
        )
        turn.tool_call("example", {"query": query}, f"{len(rows)} rows -> dataset {dataset.id}")
        turn.show(TableWidget(title=dataset.title, columns=dataset.columns, rows=rows,
                              total_rows=len(rows), dataset_id=dataset.id))
        return f"dataset {dataset.id} with {len(rows)} rows: {rows}"

    return [example]
