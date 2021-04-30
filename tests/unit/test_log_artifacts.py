"""Test log_artifacts."""

from pathlib import Path

import mlflow
import fromconfig
import pytest

import fromconfig_mlflow


def test_log_artifacts_is_discovered():
    """Test that the Launcher is discovered as fromconfig extension."""
    fromconfig.utils.testing.assert_launcher_is_discovered(
        "mlflow.log_artifacts", fromconfig_mlflow.LogArtifactsLauncher
    )


@pytest.mark.parametrize(
    "path_command, path_config",
    [
        pytest.param("launch.sh", "config.yaml", id="default"),
        pytest.param("launch.sh", "config.json", id="default-json"),
        pytest.param(None, "config.yaml", id="config-only"),
        pytest.param("launch.sh", None, id="command-only"),
    ],
)
def test_log_artifacts(path_command, path_config, monkeypatch):
    """Test log artifacts."""

    config = {}

    def _log_artifacts(local_dir):
        assert Path(local_dir, path_command or "launch.sh").is_file() == (path_command is not None)
        assert Path(local_dir, path_config or "config.yaml").is_file() == (path_config is not None)

    monkeypatch.setattr(mlflow, "log_artifacts", _log_artifacts)
    launcher = fromconfig_mlflow.StartRunLauncher(
        fromconfig_mlflow.LogArtifactsLauncher(
            fromconfig.launcher.DryLauncher(), path_command=path_command, path_config=path_config
        )
    )
    launcher(config)
