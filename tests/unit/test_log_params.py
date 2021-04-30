"""Test log_params."""

import pytest
import fromconfig
import mlflow

import fromconfig_mlflow
from fromconfig_mlflow.log_params import flatten


def test_log_params_is_discovered():
    """Test that the Launcher is discovered as fromconfig extension."""
    fromconfig.utils.testing.assert_launcher_is_discovered("mlflow.log_params", fromconfig_mlflow.LogParamsLauncher)


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
def test_flatten(params, ignore_keys, include_keys, expected):
    """Test log param."""
    assert flatten(params, ignore_keys, include_keys) == expected


def test_log_params(monkeypatch):
    """Test log params."""

    config = {"foo": {"bar": 1}}

    def _log_params(params):
        assert params == {"foo.bar": 1}

    monkeypatch.setattr(mlflow, "log_params", _log_params)
    launcher = fromconfig_mlflow.StartRunLauncher(
        fromconfig_mlflow.LogParamsLauncher(fromconfig.launcher.DryLauncher())
    )
    launcher(config)
