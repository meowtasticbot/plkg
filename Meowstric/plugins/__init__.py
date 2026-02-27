"""Plugin package for Meowstric.

Avoid eager star-imports here because plugin modules depend on symbols from
`catverse_bot`, and importing them all at package import time creates circular
imports during startup.
"""

__all__: list[str] = []
