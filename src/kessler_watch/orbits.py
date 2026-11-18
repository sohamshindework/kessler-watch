from datetime import datetime, timezone
import numpy as np
from sgp4.api import Satrec, WGS72, jday


def epoch(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)


def from_omm(row):
    from sgp4.omm import initialize
    sat = Satrec()
    initialize(sat, row, WGS72)
    return sat


def positions(rows, times):
    """TEME km; failed propagations remain NaN, never silently become valid."""
    jd, fr = [], []
    for t in times:
        a, b = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
        jd.append(a)
        fr.append(b)
    result = np.full((len(rows), len(times), 3), np.nan)
    for i, row in enumerate(rows):
        try:
            err, pos, _ = from_omm(row).sgp4_array(np.array(jd), np.array(fr))
            result[i] = np.where((err == 0)[:, None], pos, np.nan)
        except (ValueError, KeyError):
            continue
    return result


def at(row, time):
    return positions([row], [time])[0, 0]
