"""Baselines that require accumulated history; no fabricated ML performance."""
import numpy as np
from .orbits import at, epoch


def features(row, age_days):
    return [1., age_days, float(row['MEAN_MOTION']) / 16, float(row['ECCENTRICITY']), float(row['INCLINATION']) / 180]


def train_forecaster(snapshots):
    """Ridge correction of later public element consistency, not ground truth.

    Chronological and disjoint-object holdout. Residual quantiles are empirical,
    not calibrated operational covariance.
    """
    samples = []
    for (_, first), (_, later) in zip(snapshots, snapshots[1:]):
        lookup = {int(r['NORAD_CAT_ID']): r for r in later}
        for old in first:
            key = int(old['NORAD_CAT_ID'])
            if key not in lookup:
                continue
            new = lookup[key]
            target = epoch(new['EPOCH'])
            age = (target - epoch(old['EPOCH'])).total_seconds() / 86400
            if not 0.1 <= age <= 10:
                continue
            delta = at(new, target) - at(old, target)
            if np.isfinite(delta).all():
                samples.append((target.timestamp(), key, features(old, age), delta))
    if len(samples) < 100 or len(snapshots) < 5:
        return {'status': 'collecting-history', 'samples': len(samples), 'minimumSnapshots': 5, 'minimumSamples': 100}
    samples.sort(key=lambda x: x[0])
    split_time = samples[int(len(samples)*.7)][0]
    train = [s for s in samples if s[0] < split_time and s[1] % 5 != 0]
    test = [s for s in samples if s[0] >= split_time and s[1] % 5 == 0]
    if len(train) < 20 or len(test) < 10:
        return {'status': 'insufficient-holdout', 'samples': len(samples)}
    x = np.array([s[2] for s in train]); y = np.array([s[3] for s in train])
    penalty = np.eye(x.shape[1])*.1; penalty[0, 0] = 0
    weights = np.linalg.solve(x.T@x+penalty, x.T@y)
    xt = np.array([s[2] for s in test]); yt = np.array([s[3] for s in test])
    baseline = np.linalg.norm(yt, axis=1); residual = np.linalg.norm(yt-xt@weights, axis=1)
    return {'status': 'evaluated', 'method': 'ridge TEME residual baseline', 'trainSamples': len(train), 'testSamples': len(test),
            'baselineRmseKm': float(np.sqrt(np.mean(baseline**2))), 'modelRmseKm': float(np.sqrt(np.mean(residual**2))),
            'heldoutResidualP90Km': float(np.quantile(residual, .9)), 'weights': weights.tolist(),
            'target': 'Consistency with later public elements; not measured position truth',
            'split': 'Earlier dates + IDs mod 5 != 0 train; later dates + IDs mod 5 == 0 test'}


def detect_manoeuvres(snapshots, threshold_km=5):
    """Element discontinuities are candidates; drag and fit changes are confounders."""
    if len(snapshots) < 2:
        return []
    old = {int(r['NORAD_CAT_ID']): r for r in snapshots[-2][1]}
    events = []
    for row in snapshots[-1][1]:
        key = int(row['NORAD_CAT_ID'])
        if key not in old:
            continue
        before = old[key]; age = (epoch(row['EPOCH'])-epoch(before['EPOCH'])).total_seconds()/86400
        if not .1 <= age <= 3:
            continue
        error = float(np.linalg.norm(at(row, epoch(row['EPOCH']))-at(before, epoch(row['EPOCH']))))
        if not np.isfinite(error) or error < threshold_km:
            continue
        change = float(row['MEAN_MOTION']) - float(before['MEAN_MOTION'])
        kind = 'lowering candidate' if change > .005 else 'raising candidate' if change < -.005 else 'unclassified discontinuity'
        events.append({'noradId': key, 'name': row.get('OBJECT_NAME'), 'epoch': row['EPOCH'], 'residualKm': error, 'classification': kind, 'validated': False})
    return sorted(events, key=lambda e: -e['residualKm'])[:100]


def dodge_estimate(miss_km, target_km, lead_seconds):
    """Optimistic straight-line impulse lower bound, NOT an orbital manoeuvre solution."""
    if lead_seconds <= 0 or miss_km < 0 or target_km <= 0:
        raise ValueError('Positive lead time and distances required')
    return {'deltaVLowerBoundMs': max(0, target_km-miss_km)*1000/lead_seconds,
            'leadSeconds': lead_seconds, 'targetKm': target_km, 'operational': False,
            'method': 'Straight-line displacement / lead time; no orbital response, direction, fuel, or secondary-conjunction constraints'}
