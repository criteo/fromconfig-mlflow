"""MlFlow fromconfig plugin."""

__author__ = "Guillaume Genthial"
__version__ = "0.1.0"

import logging
import tempfile
from pathlib import Path
import json
from typing import Any
import os

import mlflow
import fromconfig


LOGGER = logging.getLogger(__name__)


class MlFlowLauncher(fromconfig.launcher.LogLauncher):
    """MlFlow Launcher."""

    def log(self, config: Any, command: str = "", parsed: Any = None):
        # Retrieve params for MlFlow
        mlflow_config = parsed.get("mlflow", {})
        run_id = mlflow_config.get("run_id")
        run_name = mlflow_config.get("run_name")
        tracking_uri = mlflow_config.get("tracking_uri")
        experiment_name = mlflow_config.get("experiment_name")
        artifact_location = mlflow_config.get("artifact_location")

        # Setup experiment and general MlFlow parameters
        if tracking_uri is not None:
            mlflow.set_tracking_uri(tracking_uri)
            os.environ["MLFLOW_TRACKING_URI"] = tracking_uri
        if experiment_name is not None:
            if mlflow.get_experiment_by_name(experiment_name) is None:
                mlflow.create_experiment(self.experiment_name, artifact_location=artifact_location)
            mlflow.set_experiment(experiment_name)

        # Start MlFlow run, log information and launch
        with mlflow.start_run(run_id=run_id, run_name=run_name) as run:
            # Log run information and set environment variable
            os.environ["MLFLOW_RUN_ID"] = run.info.run_id
            url = f"{mlflow.get_tracking_uri()}/experiments/{run.info.experiment_id}/runs/{run.info.run_id}"
            LOGGER.info(f"MlFlow URL: {url}")

            # Save merged and parsed config to MlFlow
            dir_artifacts = tempfile.mkdtemp()
            with Path(dir_artifacts, "config.json").open("w") as file:
                json.dump(config, file, indent=4)
            with Path(dir_artifacts, "parsed.json").open("w") as file:
                json.dump(parsed, file, indent=4)
            with Path(dir_artifacts, "launch.txt").open("w") as file:
                file.write(f"fromconfig config.json - {command}")
            mlflow.log_artifacts(local_dir=dir_artifacts)

            # Log flattened parameters
            def _sanitize(s):
                return s.replace("[", ".__").replace("]", "__.")

            for key, value in fromconfig.utils.flatten(parsed):
                mlflow.log_param(key=_sanitize(key), value=value)

            self.launcher(config=config, parsed=parsed, command=command)
