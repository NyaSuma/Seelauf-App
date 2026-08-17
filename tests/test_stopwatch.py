import os
import tempfile
import importlib
from types import SimpleNamespace

import pytest

from routen.stopwatch import Stopwatch
import db
from app import create_app


def test_stopwatch_lifecycle(monkeypatch):
    time_values = iter([1000.0, 1002.0, 1004.0, 1006.0, 1008.5])
    monkeypatch.setattr('routen.stopwatch.time.time', lambda: next(time_values))

    stopwatch = Stopwatch()
    stopwatch.start()

    assert stopwatch.is_running is True
    assert stopwatch.is_paused is False
    assert stopwatch.get_elapsed_time() == pytest.approx(2.0, abs=1e-6)

    stopwatch.pause()
    assert stopwatch.is_running is False
    assert stopwatch.is_paused is True
    assert stopwatch.get_elapsed_time() == pytest.approx(4.0, abs=1e-6)

    stopwatch.resume()
    assert stopwatch.is_running is True
    assert stopwatch.is_paused is False

    assert stopwatch.get_formatted_time(stopwatch.get_elapsed_time()) == '00:00:06.50'

    stopwatch.stop()
    assert stopwatch.get_elapsed_time() == 0
    assert stopwatch.get_status()['is_running'] is False
    assert stopwatch.get_status()['is_paused'] is False


@pytest.fixture
def client():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.environ['DATABASE_PATH'] = path
    importlib.reload(db)
    app = create_app({'TESTING': True, 'DATABASE_PATH': path})
    with app.test_client() as client:
        yield client
    try:
        os.unlink(path)
    except OSError:
        pass


def test_api_history_and_active_runs(client):
    # Create a sample student so record endpoint works.
    db.add_student('Lena Becker', '9B', '555')

    response = client.post('/api/stopwatch/start')
    assert response.status_code == 200
    assert response.json['is_running'] is True

    response = client.post('/api/stopwatch/pause')
    assert response.status_code == 200
    assert response.json['is_paused'] is True

    response = client.post('/api/stopwatch/record', json={'number': '555'})
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['time'] == '00:00:00.00'

    response = client.get('/api/stopwatch/history')
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 1
    assert response.json[0]['nummer'] == '555'

    response = client.get('/api/stopwatch/active_runs')
    assert response.status_code == 200
    assert isinstance(response.json, list)
