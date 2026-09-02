"""
DECOMMISSIONED: legacy unauthenticated Temperans Pilot API.

This module previously exposed PilotService directly over HTTP without
organization authentication. It must never be used as a partner-facing
server.

Use:

    python -m temperans.partner_api

instead.

The file intentionally remains as a tombstone so old integrations fail
loudly and explain how to migrate rather than failing with an import error.
"""

from __future__ import annotations


DECOMMISSIONED = True

MIGRATION_MESSAGE = (
    "temperans.pilot_api has been decommissioned because it bypassed "
    "multi-organization authentication. "
    "Use `python -m temperans.partner_api` instead."
)


def main():
    raise RuntimeError(MIGRATION_MESSAGE)


if __name__ == "__main__":
    main()
