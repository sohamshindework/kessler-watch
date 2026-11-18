"""Coarse KD-tree screening followed by continuous local TCA refinement.

A finite sampling grid cannot guarantee discovery of every conjunction.
"""
from datetime import timedelta
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import minimize_scalar
from .orbits import positions, at


def screen(rows, start, days=7, step_seconds=120, threshold_km=10, candidates_km=150, max_events=100):
    if days <= 0 or step_seconds <= 0 or threshold_km <= 0 or candidates_km < threshold_km:
        raise ValueError('Invalid screening configuration')
    steps = int(days * 86400 / step_seconds) + 1
    candidates = {}
    failed = 0
    # Bounded memory: one propagation time and tree at a time.
    for k in range(steps):
        time = start + timedelta(seconds=k * step_seconds)
        pos = positions(rows, [time])[:, 0, :]
        valid = np.isfinite(pos).all(axis=1)
        failed += int((~valid).sum())
        indices = np.flatnonzero(valid)
        tree = cKDTree(pos[valid])
        for a, b in tree.query_pairs(candidates_km):
            i, j = int(indices[a]), int(indices[b])
            distance = float(np.linalg.norm(pos[i] - pos[j]))
            if (i, j) not in candidates or distance < candidates[i, j][0]:
                candidates[i, j] = (distance, k * step_seconds)
    events = []
    shared_elements = 0
    keys = ("EPOCH", "MEAN_MOTION", "ECCENTRICITY", "INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY", "BSTAR")
    for (i, j), (_, offset) in candidates.items():
        if all(rows[i].get(key) == rows[j].get(key) for key in keys):
            shared_elements += 1
            continue
        def separation(seconds):
            time = start + timedelta(seconds=float(seconds))
            p, q = at(rows[i], time), at(rows[j], time)
            value = float(np.linalg.norm(p - q))
            return value if np.isfinite(value) else 1e12
        lo, hi = max(0, offset - step_seconds), min(days * 86400, offset + step_seconds)
        fit = minimize_scalar(separation, bounds=(lo, hi), method='bounded', options={'xatol': .01})
        options = [(float(fit.fun), float(fit.x)), (separation(lo), lo), (separation(hi), hi)]
        miss, seconds = min(options)
        if miss > threshold_km:
            continue
        tca = start + timedelta(seconds=seconds)
        p, q = at(rows[i], tca), at(rows[j], tca)
        dt = timedelta(seconds=.5)
        velocity = (at(rows[i], tca + dt) - at(rows[i], tca - dt)) - (at(rows[j], tca + dt) - at(rows[j], tca - dt))
        events.append({'id': f'{rows[i]["NORAD_CAT_ID"]}-{rows[j]["NORAD_CAT_ID"]}',
                       'primary': int(rows[i]['NORAD_CAT_ID']), 'secondary': int(rows[j]['NORAD_CAT_ID']),
                       'primaryName': rows[i].get('OBJECT_NAME', 'Unknown'), 'secondaryName': rows[j].get('OBJECT_NAME', 'Unknown'),
                       'tca': tca.isoformat(), 'missDistanceKm': round(miss, 5),
                       'relativeSpeedKms': round(float(np.linalg.norm(velocity)), 4),
                       'collisionProbability': None, 'positionTemeKm': ((p+q)/2).tolist()})
    events.sort(key=lambda e: e['missDistanceKm'])
    return events[:max_events], {'steps': steps, 'stepSeconds': step_seconds, 'candidateRadiusKm': candidates_km,
                                'thresholdKm': threshold_km, 'failedObjectSamples': failed, 'candidatePairs': len(candidates),
                                'excludedSharedElementPairs': shared_elements, 'qualifyingPairs': len(events), 'complete': False,
                                'method': 'Sampled SGP4 / TEME KD-tree; bounded scalar TCA refinement; one closest encounter per pair. Not exhaustive.'}
