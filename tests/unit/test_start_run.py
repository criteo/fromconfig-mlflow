"""Test launcher."""

import os

import fromconfig
import mlflow
import pytest

import fromconfig_mlflow


def test_start_run_is_discovered():
    """Test that the Launcher is discovered as fromconfig extension."""
    fromconfig.utils.testing.assert_launcher_is_discovered("mlflow", fromconfig_mlflow.StartRunLauncher)


@pytest.mark.parametrize(
    "config",
    [pytest.param({"foo": "bar"}, id="dict"), pytest.param(None, id="none"), pytest.param(["foo"], id="list")],
)
def test_launcher_start_run_simple(config):
    """Simple test."""
    launcher = fromconfig_mlflow.StartRunLauncher(fromconfig.launcher.LocalLauncher())
    launcher(config)


def test_launcher_start_run_experiment_name():
    """Test experiment name configuration."""
    config = {"mlflow": {"experiment_name": "test"}}

    def _capture(config, command):  # pylint: disable=unused-argument
        assert mlflow.get_experiment(mlflow.active_run().info.experiment_id).name == "test"

    launcher = fromconfig_mlflow.StartRunLauncher(_capture)
    launcher(config)


def test_launcher_start_run_run_name():
    """Test run name configuration."""
    config = {"mlflow": {"run_name": "test"}}

    def _capture(config, command):  # pylint: disable=unused-argument
        assert mlflow.active_run().data.tags["mlflow.runName"] == "test"

    launcher = fromconfig_mlflow.StartRunLauncher(_capture)
    launcher(config)


def test_launcher_start_run_reactivate():
    """Test reactivation."""

    def check_active(config, command):  # pylint: disable=unused-argument
        if not mlflow.active_run():
            raise ValueError("Run is not active")

    launcher = fromconfig_mlflow.StartRunLauncher(fromconfig_mlflow.StartRunLauncher(check_active))
    launcher(None)


def test_launcher_start_run_env_variables_state():
    """Test state preservation of environment variables."""
    default_uri = mlflow.tracking.get_tracking_uri()
    os.environ["MLFLOW_TRACKING_URI"] = "127.0.0.1:5000"
    config = {"mlflow": {"tracking_uri": default_uri}}
    launcher = fromconfig_mlflow.StartRunLauncher(fromconfig.launcher.DryLauncher(), set_env_vars=True)
    launcher(config)
    assert os.environ["MLFLOW_TRACKING_URI"] == "127.0.0.1:5000"


@pytest.mark.parametrize(
    "params, expected",
    [
        pytest.param({}, ["MLFLOW_RUN_ID", "MLFLOW_TRACKING_URI"], id="default"),
        pytest.param({"set_env_vars": False, "set_run_id": False}, [], id="set-env-vars-false"),
        pytest.param(
            {"set_env_vars": True, "set_run_id": False},
            ["MLFLOW_RUN_ID", "MLFLOW_TRACKING_URI"],
            id="set-env-vars-true",
        ),
        pytest.param({"set_env_vars": False, "set_run_id": True}, ["run_id"], id="set-run-id-true"),
        pytest.param({"set_env_vars": False, "set_run_id": False}, [], id="set-run-id-false"),
    ],
)
def test_launcher_start_run_params(params, expected):
    """Test launcher."""

    got = {}

    def _capture(config, command):
        # pylint: disable=unused-argument
        got.update(
            {
                "MLFLOW_RUN_ID": os.environ.get("MLFLOW_RUN_ID"),
                "MLFLOW_TRACKING_URI": os.environ.get("MLFLOW_TRACKING_URI"),
                "run_id": config.get("mlflow", {}).get("run_id"),
            }
        )

    launcher = fromconfig_mlflow.StartRunLauncher(_capture, **params)
    launcher({})

    # Check that expected is a match
    for key in ["MLFLOW_RUN_ID", "MLFLOW_TRACKING_URI", "run_id"]:
        assert (got.get(key) is not None) == (key in expected), key
