"""MlFlow Log Artifacts Launcher."""

from pathlib import Path
from typing import Any
import tempfile

import fromconfig
import mlflow


class LogArtifactsLauncher(fromconfig.launcher.Launcher):
    """Log artifacts if an MlFlow Run is active.

    Attributes
    ----------
    path_command : str, optional
        Name for the command file
    path_config : str, optional
        Name for the config file.
    """

    NAME = "log_artifacts"

    def __init__(
        self, launcher: fromconfig.launcher.Launcher, path_command: str = "launch.sh", path_config: str = "config.yaml",
    ):
        super().__init__(launcher=launcher)
        self.path_command = path_command
        self.path_config = path_config

    def __call__(self, config: Any, command: str = ""):
        if mlflow.active_run() is not None:
            dir_artifacts = tempfile.mkdtemp()
            if self.path_command:
                with Path(dir_artifacts, self.path_command).open("w") as file:
                    file.write(f"fromconfig {self.path_config} - {command}")
            if self.path_config:
                fromconfig.dump(config, Path(dir_artifacts, self.path_config))
            mlflow.log_artifacts(local_dir=dir_artifacts)

        self.launcher(config, command)
