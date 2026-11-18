import gzip
import json
from pathlib import Path
from datetime import datetime, timezone

URL = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json'


def download(group='active'):
    if group not in {'active'}:
        raise ValueError('Only the documented active group is supported; use --input for a broader OMM catalogue')
    url = URL.replace('GROUP=active', f'GROUP={group}')
    # curl is present on GitHub runners and avoids inconsistent urllib TLS/UA handling.
    import subprocess
    response = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                               '--retry', '2', '--max-time', '120', url],
                              capture_output=True, text=True, check=True)
    try:
        rows = json.loads(response.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError('CelesTrak returned a non-JSON response; last snapshot is preserved') from exc
    validate(rows)
    return rows, url


def validate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Empty or malformed catalogue')
    required = {'NORAD_CAT_ID', 'EPOCH', 'MEAN_MOTION', 'ECCENTRICITY', 'INCLINATION', 'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY'}
    ids = set()
    for row in rows:
        if not required <= row.keys():
            raise ValueError('Missing OMM fields')
        key = int(row['NORAD_CAT_ID'])
        if key in ids:
            raise ValueError('Duplicate catalogue ID')
        ids.add(key)


def snapshot(rows, root, now):
    path = Path(root) / f'{now:%Y-%m-%d}.json.gz'
    path.parent.mkdir(parents=True, exist_ok=True)
    # A daily immutable snapshot, not a silent overwrite of the training history.
    if not path.exists():
        with gzip.open(path, 'wt') as file:
            json.dump(rows, file, separators=(',', ':'))
    return path


def history(root):
    result = []
    for path in sorted(Path(root).glob('*.json.gz')):
        with gzip.open(path, 'rt') as file:
            result.append((path.stem.split('.')[0], json.load(file)))
    return result
