import os
import tempfile
import pytest
from db import save_measurement, get_measurements, clear_measurements

@pytest.fixture
def temp_db():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    os.environ['DATABASE_PATH'] = db_path
    # Re-import the db module to pick up the new DATABASE_PATH
    import importlib
    import db
    importlib.reload(db)
    yield db
    # Teardown: close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)

def test_save_and_get_measurement(temp_db):
    # Save a measurement
    temp_db.save_measurement("123", "00:05:32.10")
    # Retrieve measurements
    measurements = temp_db.get_measurements()
    assert len(measurements) == 1
    assert measurements[0]['nummer'] == "123"
    assert measurements[0]['zeit'] == "00:05:32.10"
    # Check that timestamp is present and in ISO format
    assert 'timestamp' in measurements[0]
    # Clear measurements
    temp_db.clear_measurements()
    measurements_after_clear = temp_db.get_measurements()
    assert len(measurements_after_clear) == 0

def test_get_measurements_empty(temp_db):
    measurements = temp_db.get_measurements()
    assert len(measurements) == 0

def test_get_measurement_by_number(temp_db):
    # Save two measurements for the same number and one for a different number
    temp_db.save_measurement("123", "00:05:32.10")
    temp_db.save_measurement("123", "00:04:45.20")
    temp_db.save_measurement("456", "00:06:10.00")
    # Get measurements for number 123
    measurements_123 = temp_db.get_measurement_by_number("123")
    assert len(measurements_123) == 2
    # They should be in descending order by id (most recent first)
    assert measurements_123[0]['zeit'] == "00:04:45.20"  # The second one saved
    assert measurements_123[1]['zeit'] == "00:05:32.10"  # The first one saved
    # Get measurements for number 456
    measurements_456 = temp_db.get_measurement_by_number("456")
    assert len(measurements_456) == 1
    assert measurements_456[0]['zeit'] == "00:06:10.00"
    # Get measurements for a non-existent number
    measurements_789 = temp_db.get_measurement_by_number("789")
    assert len(measurements_789) == 0