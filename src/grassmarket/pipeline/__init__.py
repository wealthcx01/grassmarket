"""Pipeline management — prospects, kanban stages, workshops, recovery fees (PRD §4). Loop 3.

GRS-0011 ships the validated stage-transition machine, time-in-stage flags, and the (currency-free)
deal-volume forecast on top of the Loop 0 prospects skeleton.
"""

from grassmarket.pipeline.service import build_board, build_forecast, days_in_stage

__all__ = ["build_board", "build_forecast", "days_in_stage"]
