"""MCP resources: canonical documentation, exposed so agents can ground answers in it.

Built in ROADMAP.md Sprint 13. Wraps two documents this repo already treats as the single
source of truth for their respective domains, so an agent answering a business or access
question quotes the governed definition instead of inventing one:

- `docs/semantic-dictionary.md` — canonical metric definitions (Revenue, AOV, Churn, CLV, NPS,
  Delivery SLA, ...), owned by the Sprint 8 semantic layer work (ARCHITECTURE.md §11). This is
  what stops the "Power BI said R$10M, the agent said R$13M" failure mode ADR-005 exists to
  prevent — an agent should read this resource before ever stating a metric value in prose.
- `governance/access_control.md` — RBAC/access-control policy, owned by the Sprint 16
  governance work (ARCHITECTURE.md §16). Used when an agent needs to reason about *whether* it
  is allowed to answer a question, not just how.

Both files are owned by other workstreams — this module only reads and re-serves them as MCP
resources; it must never fork or restate their content, only point at the current file on disk
so there is exactly one place either document can drift.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

REPO_ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_DICTIONARY_PATH = REPO_ROOT / "docs" / "semantic-dictionary.md"
ACCESS_CONTROL_PATH = REPO_ROOT / "governance" / "access_control.md"


def get_semantic_dictionary() -> dict[str, str | bool]:
    """Return the raw contents of docs/semantic-dictionary.md.

    Returns:
        {"path": str, "content": str, "found": bool}
        `found=False` with empty content if the file does not exist yet in this checkout (it is
        owned by the Sprint 8 semantic layer work and may not have landed).
    """
    # TODO(Sprint 8 / docs): once docs/semantic-dictionary.md exists, consider caching this
    # read with an mtime check instead of reading from disk on every call — metric definitions
    # change rarely relative to how often an agent might consult them.
    if not SEMANTIC_DICTIONARY_PATH.exists():
        return {"path": str(SEMANTIC_DICTIONARY_PATH), "content": "", "found": False}
    return {
        "path": str(SEMANTIC_DICTIONARY_PATH),
        "content": SEMANTIC_DICTIONARY_PATH.read_text(encoding="utf-8"),
        "found": True,
    }


def get_access_control_policy() -> dict[str, str | bool]:
    """Return the raw contents of governance/access_control.md.

    Returns:
        {"path": str, "content": str, "found": bool}
        `found=False` with empty content if the file does not exist yet in this checkout (it is
        owned by the Sprint 16 governance work and may not have landed).
    """
    # TODO(Sprint 16 / governance): once governance/access_control.md exists, this should be
    # read-through cached the same way as get_semantic_dictionary() above.
    if not ACCESS_CONTROL_PATH.exists():
        return {"path": str(ACCESS_CONTROL_PATH), "content": "", "found": False}
    return {
        "path": str(ACCESS_CONTROL_PATH),
        "content": ACCESS_CONTROL_PATH.read_text(encoding="utf-8"),
        "found": True,
    }


def register(mcp: FastMCP) -> None:
    """Register this module's resources on the given FastMCP server instance."""

    @mcp.resource("docs://semantic-dictionary")
    def semantic_dictionary_resource() -> dict[str, str | bool]:
        """Canonical metric definitions — see get_semantic_dictionary()."""
        return get_semantic_dictionary()

    @mcp.resource("docs://access-control")
    def access_control_resource() -> dict[str, str | bool]:
        """RBAC / access-control policy — see get_access_control_policy()."""
        return get_access_control_policy()
