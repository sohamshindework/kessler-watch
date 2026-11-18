import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from .catalogue import download, snapshot, history, validate
from .screen import screen
from .orbits import positions
from .research import train_forecaster, detect_manoeuvres
import numpy as np


def main():
    parser = argparse.ArgumentParser(description='Kessler Watch public catalogue research pipeline')
    parser.add_argument('--group', choices=['active'], default='active')
    parser.add_argument('--input', type=Path, help='Use a local OMM JSON catalogue instead of downloading')
    parser.add_argument('--output', type=Path, default=Path('web/public/data'))
    parser.add_argument('--history', type=Path, default=Path('data/history'))
    parser.add_argument('--days', type=float, default=7)
    parser.add_argument('--step-seconds', type=int, default=120)
    parser.add_argument('--limit', type=int, default=500, help='Bound screening workload; 0 screens all downloaded objects')
    args = parser.parse_args()
    if args.limit < 0:
        parser.error('--limit must be nonnegative')
    now = datetime.now(timezone.utc)
    if args.input:
        rows = json.loads(args.input.read_text()); validate(rows); source = 'local-file'
    else:
        rows, source = download(args.group)
    snapshot(rows, args.history, now)
    subset = sorted(rows, key=lambda r: int(r['NORAD_CAT_ID']))
    if args.limit:
        subset = subset[:args.limit]
    events, coverage = screen(subset, now, args.days, args.step_seconds)
    pos = positions(rows, [now])[:, 0, :]
    objects = []
    for row, xyz in zip(rows, pos):
        if np.isfinite(xyz).all():
            objects.append({'id': int(row['NORAD_CAT_ID']), 'name': row.get('OBJECT_NAME', 'Unknown'),
                            'positionTemeKm': xyz.tolist(), 'omm': row})
    snapshots = history(args.history)
    data = {'mode': 'public-catalogue', 'generatedAt': now.isoformat(), 'source': source,
            'catalogueGroup': 'local OMM' if args.input else args.group, 'catalogueCount': len(rows), 'screenedCount': len(subset),
            'horizonDays': args.days, 'objects': objects, 'events': events, 'coverage': coverage,
            'forecast': train_forecaster(snapshots), 'manoeuvres': detect_manoeuvres(snapshots),
            'disclaimer': 'Research only. Public elements are not precision ephemerides. No covariance, collision probability, or validated manoeuvre recommendation.'}
    args.output.mkdir(parents=True, exist_ok=True)
    # Atomic replacement prevents partial dashboard data after interrupted writes.
    temp = args.output/'latest.tmp'
    temp.write_text(json.dumps(data, separators=(',', ':'), allow_nan=False))
    temp.replace(args.output/'latest.json')
    print(f'Published {len(objects)} objects, {len(events)} candidate encounters; screened {len(subset)}/{len(rows)}.')


if __name__ == '__main__':
    main()
