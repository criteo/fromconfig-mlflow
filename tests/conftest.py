"""Setup tests."""

import os


def pytest_runtest_setup(item):
    """Before test runs, make sure no MlFlow ENV variable is set.

    Parameters
    ----------
    item : test function
    """
    # pylint: disable=unused-argument,protected-access
    if "MLFLOW_RUN_ID" in os.environ:
        del os.environ["MLFLOW_RUN_ID"]
    if "MLFLOW_TRACKING_URI" in os.environ:
        del os.environ["MLFLOW_TRACKING_URI"]
