"""Test launcher."""

import collections
import functools

import pytest
import fromconfig

import fromconfig_mlflow
from fromconfig_mlflow.launcher import get_params


def test_launcher_is_discovered():
    """Test that the Launcher is discovered as fromconfig extension."""
    fromconfig.utils.testing.assert_launcher_is_discovered("mlflow", fromconfig_mlflow.MlFlowLauncher)


@pytest.mark.parametrize(
    "launcher, params, expected, counts",
    [
        pytest.param(
            {"log": "mlflow"},
            {},
            {"start_run": {"kwargs": {"run_name": None}}},
            {"start_run": 1, "log_artifacts": 1},
            id="default",
        ),
        pytest.param(
            {"log": "mlflow"},
            {"experiment_name": "test"},
            {"start_run": {"kwargs": {"run_name": None}}},
            {"start_run": 1, "log_artifacts": 1},
            id="default",
        ),
        pytest.param(
            {"log": "mlflow"},
            {"run_name": "test"},
            {"start_run": {"kwargs": {"run_name": "test"}}},
            {"start_run": 1, "log_artifacts": 1},
            id="run_name",
        ),
        pytest.param(
            {"log": ["mlflow", "mlflow"]},
            {"run_name": "test"},
            {"start_run": {"kwargs": {"run_name": "test"}}},
            {"start_run": 1, "log_artifacts": 1},
            id="no-duplicate",
        ),
        pytest.param(
            {"log": ["mlflow", "mlflow"]},
            {"run_name": "test", "launches": [{"log_artifacts": True}, {"log_artifacts": True}]},
            {"start_run": {"kwargs": {"run_name": "test"}}},
            {"start_run": 1, "log_artifacts": 2},
            id="duplicate-with-launches-param",
        ),
        pytest.param(
            {"log": ["mlflow", "mlflow"]},
            {"run_name": "test", "launches": [{"log_parameters": True}, {"log_parameters": True, "set_env_vars": True}]},
            {"start_run": {"kwargs": {"run_name": "test"}}},
            {"start_run": 1, "log_artifacts": 1},
            id="no-duplicate-log-artifacts",
        ),
    ],
)
def test_launcher(launcher, params, expected, counts, monkeypatch):
    """Test cli.main."""
    import mlflow  # pylint: disable=import-outside-toplevel

    # Setup monkey patching to track MlFlow calls
    got = {}
    counter = collections.Counter()
    names = ["log_artifacts", "log_params", "start_run"]
    for name in names:
        func = getattr(mlflow, name)

        def _func(*args, f=None, n=None, **kwargs):
            got.update({n: {"args": args, "kwargs": kwargs}})
            counter.update([n])
            return f(*args, **kwargs)

        monkeypatch.setattr(mlflow, name, functools.partial(_func, n=name, f=func))

    # Create config, launcher, and launch
    config = {"run": None, "launcher": launcher, "mlflow": params}
    launcher = fromconfig.launcher.Launcher.fromconfig(config["launcher"])
    launcher(config, "run")

    def _check_expected(left, right):
        if isinstance(left, dict):
            for key, value in left.items():
                _check_expected(value, right[key])
        else:
            assert left == right

    # Check that all MlFlow functions were called
    assert all(name in got for name in names)

    # Check that number of calls matches expectations
    assert all(counter[key] == count for key, count in counts.items()), counter

    # Check that kwargs / args match expectations
    _check_expected(expected, got)


@pytest.mark.parametrize(
    "params, ignore_keys, include_keys, expected",
    [
        pytest.param({"foo": 0}, None, None, [("foo", 0)], id="default"),
        pytest.param({"foo": 0, "bar": 1}, None, None, [("foo", 0), ("bar", 1)], id="default-multi"),
        pytest.param({"foo": 0}, (), (), [("foo", 0)], id="default-empty-tuple"),
        pytest.param({"foo": 0}, (), ("foo",), [("foo", 0)], id="include"),
        pytest.param({"foo": 0, "bar": 1}, (), ("foo",), [("foo", 0)], id="include-multi"),
        pytest.param({"foo": 0}, ("foo",), (), [], id="ignore"),
        pytest.param({"foo": 0, "bar": 1}, ("foo",), (), [("bar", 1)], id="ignore-multi"),
        pytest.param(
            {"foo": {"bar": {"bar": 0}}, "bar": 1}, (), ("bar",), [("bar.bar", 0), ("bar", 1)], id="include-conflict"
        ),
    ],
)
def test_get_params(params, ignore_keys, include_keys, expected):
    """Test log param."""
    assert get_params(params, ignore_keys, include_keys) == expected
