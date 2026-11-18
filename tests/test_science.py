from datetime import datetime, timezone, timedelta
import numpy as np
import pytest
from sgp4.api import Satrec
from kessler_watch.orbits import positions, from_omm, epoch
from kessler_watch.catalogue import validate, snapshot, history
from kessler_watch.screen import screen
from kessler_watch.research import dodge_estimate, train_forecaster, detect_manoeuvres

@pytest.fixture
def row():
    return {'OBJECT_NAME': 'VANGUARD 1', 'NORAD_CAT_ID': 5, 'OBJECT_ID': '1958-002B', 'CLASSIFICATION_TYPE': 'U',
            'EPOCH': '2000-06-27T18:50:19.733568', 'MEAN_MOTION': 10.82419157, 'ECCENTRICITY': .1859667,
            'INCLINATION': 34.2682, 'RA_OF_ASC_NODE': 348.7242, 'ARG_OF_PERICENTER': 331.7664,
            'MEAN_ANOMALY': 19.3264, 'BSTAR': .000028098, 'MEAN_MOTION_DOT': .00000023,
            'MEAN_MOTION_DDOT': 0., 'EPHEMERIS_TYPE': 0, 'ELEMENT_SET_NO': 475, 'REV_AT_EPOCH': 41366}


def test_vallado_reference_vector(row):
    # Vallado SGP4 verification case 00005, at epoch, published TEME km.
    actual = positions([row], [epoch(row['EPOCH'])])[0, 0]
    np.testing.assert_allclose(actual, [7022.46529266, -1400.08296755, .03995155], atol=.001)


def test_nearby_orbit_is_screened(row):
    copy = dict(row, NORAD_CAT_ID=6, OBJECT_NAME='COPY', MEAN_ANOMALY=row['MEAN_ANOMALY']+.0001)
    events, coverage = screen([row, copy], epoch(row['EPOCH']), days=.001, step_seconds=30)
    assert len(events) == 1
    assert events[0]['missDistanceKm'] < .1
    assert events[0]['collisionProbability'] is None
    assert coverage['complete'] is False


def test_invalid_configuration(row):
    with pytest.raises(ValueError):
        screen([row], epoch(row['EPOCH']), step_seconds=0)
    with pytest.raises(ValueError):
        dodge_estimate(1, 10, 0)


def test_snapshot_immutable_and_validated(row, tmp_path):
    validate([row])
    with pytest.raises(ValueError):
        validate([row, row])
    time=epoch(row['EPOCH'])
    path=snapshot([row],tmp_path,time)
    original=path.read_bytes()
    snapshot([dict(row, MEAN_MOTION=15)],tmp_path,time)
    assert path.read_bytes()==original
    assert len(history(tmp_path))==1


def test_no_fabricated_research(row):
    assert train_forecaster([])['status']=='collecting-history'
    assert detect_manoeuvres([('2000-06-27',[row])]) == []
    assert dodge_estimate(1,10,9000)['deltaVLowerBoundMs']==1
    assert dodge_estimate(12,10,9000)['deltaVLowerBoundMs']==0


def test_shared_elements_excluded(row):
    events, coverage = screen([row, dict(row, NORAD_CAT_ID=6)], epoch(row['EPOCH']), days=.001, step_seconds=30)
    assert events == []
    assert coverage['excludedSharedElementPairs'] == 1
