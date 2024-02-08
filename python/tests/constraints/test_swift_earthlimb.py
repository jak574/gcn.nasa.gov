import numpy as np


def test_swift_earthconstraint(swiftapi_visibility, swift_windows):
    errors = np.ravel(abs(swift_windows - swiftapi_visibility))
    # Check that visibility windows match to within 60 seconds
    assert max(errors) == 60
    # Make sure < 5% of the start/stop times are off by +/-60 seconds
    assert len(np.where(errors != 0)) / len(errors) < 0.05
