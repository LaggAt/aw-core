import logging
from typing import List, Iterable, Tuple
from copy import deepcopy

from aw_core.models import Event
from aw_core import TimePeriod

logger = logging.getLogger(__name__)


def _get_event_period(event: Event) -> TimePeriod:
    start = event.timestamp
    end = start + event.duration
    return TimePeriod(start, end)


def _replace_event_period(event: Event, period: TimePeriod) -> Event:
    e = deepcopy(event)
    e.timestamp = period.start
    e.duration = period.duration
    return e


def _intersecting_eventpairs(events1: List[Event], events2: List[Event]) -> Iterable[Tuple[Event, Event, TimePeriod]]:
    """A generator that yields each overlapping pair of events from two eventlists along with a TimePeriod of the intersection"""
    e1_i = 0
    e2_i = 0
    while e1_i < len(events1) and e2_i < len(events2):
        e1 = events1[e1_i]
        e2 = events2[e2_i]
        e1_p = _get_event_period(e1)
        e2_p = _get_event_period(e2)

        ip = e1_p.intersection(e2_p)
        if ip:
            # If events intersected, yield events
            yield (e1, e2, ip)
            if e1_p.end <= e2_p.end:
                e1_i += 1
            else:
                e2_i += 1
        else:
            # No intersection, check if event is before/after filterevent
            if e1_p.end <= e2_p.start:
                # Event ended before filter event started
                e1_i += 1
            elif e2_p.end <= e1_p.start:
                # Event started after filter event ended
                e2_i += 1
            else:
                logger.error("Should be unreachable, skipping period")
                e1_i += 1
                e2_i += 1


def filter_period_intersect(events: List[Event], filterevents: List[Event]) -> List[Event]:
    """
    Filters away all events or time periods of events in which a
    filterevent does not have an intersecting time period.

    Useful for example when you want to filter away events or
    part of events during which a user was AFK.

    Usage:
      windowevents_notafk = filter_period_intersect(windowevents, notafkevents)

    Example:
      events1   |   =======        ======== |
      events2   | ------  ---  ---   ----   |
      result    |   ====  =          ====   |

    A JavaScript version used to exist in aw-webui but was removed in `this PR <https://github.com/ActivityWatch/aw-webui/pull/48>`_.
    """

    events = sorted(events)
    filterevents = sorted(filterevents)

    return [_replace_event_period(e1, ip) for (e1, _, ip) in _intersecting_eventpairs(events, filterevents)]


def period_union(events1: List[Event], events2: List[Event]) -> List[Event]:
    """
    Takes a list of two events and returns a new list of events covering the union
    of the timeperiods contained in the eventlists with no overlapping events.

    WARNING: This function gives no guarantees about what will end up in the data
             attribute of returned events, only use it when the event data is irrelevant.

    Example:
      events1   |   =======       ========= |
      events2   | ------  ---  --    ----   |
      result    | -----------  -- ========= |
    """
    events = sorted(events1 + events2)
    merged_events = []
    if events:
        merged_events.append(events.pop(0))
    for e in events:
        last_event = merged_events[-1]

        e_p = _get_event_period(e)
        le_p = _get_event_period(last_event)

        if not e_p.gap(le_p):
            new_period = e_p.union(le_p)
            merged_events[-1] = _replace_event_period(last_event, new_period)
        else:
            merged_events.append(e)
    return merged_events


def union(events1: List[Event], events2: List[Event]) -> List[Event]:
    return sorted(events1 + events2)
