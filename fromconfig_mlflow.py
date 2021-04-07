"""MlFlow fromconfig plugin."""

__author__ = "Guillaume Genthial"
__version__ = "0.1.0"

from typing import Any
import logging
import tempfile
from pathlib import Path
import json

import mlflow
import fromconfig


LOGGER = logging.getLogger(__name__)


class MlFlowPlugin(fromconfig.plugin.LoggingPlugin):
    """MlFlow fromconfig plugin."""

    def __init__(
        self,
        run_name: str = None,
        run_id: str = None,
        tracking_uri: str = None,
        experiment_name: str = None,
        artifact_location: str = None,
    ):
        self.run_name = run_name
        self.run_id = run_id
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.artifact_location = artifact_location

    def log(self, config: Any, parsed: Any):
        """Create new MlFlow run and Log config and parsed config.

        Parameters
        ----------
        config : Any
            Non-parsed config.
        parsed : Any
            Parsed config.
        """
        # Configure MlFlow
        if self.tracking_uri is not None:
            mlflow.set_tracking_uri(self.tracking_uri)
        if self.experiment_name is not None:
            if mlflow.get_experiment_by_name(self.experiment_name) is None:
                mlflow.create_experiment(name=self.experiment_name, artifact_location=self.artifact_location)
            mlflow.set_experiment(self.experiment_name)

        # Start run (cannot use context because of python Fire)
        run = mlflow.start_run(run_id=self.run_id, run_name=self.run_name)

        # Log run information
        url = f"{mlflow.get_tracking_uri()}/experiments/{run.info.experiment_id}/runs/{run.info.run_id}"
        LOGGER.info(f"MlFlow URL: {url}")

        # Save merged and parsed config to MlFlow
        dir_artifacts = tempfile.mkdtemp()
        with Path(dir_artifacts, "config.json").open("w") as file:
            json.dump(config, file, indent=4)
        with Path(dir_artifacts, "parsed.json").open("w") as file:
            json.dump(parsed, file, indent=4)
        mlflow.log_artifacts(local_dir=dir_artifacts)

        # Log flattened parameters
        for key, value in fromconfig.utils.flatten(parsed):
            mlflow.log_param(key=key, value=value)
