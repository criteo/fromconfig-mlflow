"""MlFlow fromconfig plugin."""

import logging
import tempfile
from pathlib import Path
import json
from typing import Any

import mlflow
import fromconfig


LOGGER = logging.getLogger(__name__)


_RUN_ID_ENV_VAR = "MLFLOW_RUN_ID"


class MlFlowLauncher(fromconfig.launcher.Launcher):
    """MlFlow Launcher.

    To configure MlFlow, add a `mlflow` entry to your config.

    You can set the following parameters

    - `run_id`: if you wish to restart an existing run
    - `run_name`: if you wish to give a name to your new run
    - `tracking_uri`: to configure the tracking remote
    - `experiment_name`: to use a different experiment than the custom
      experiment
    - `artifact_location`: the location of the artifacts (config files)

    Additionally, if you wish to call the `mlflow` launcher multiple
    times during the launch (for example once before the parser, and
    once after), you need to configure the different launches with the
    special `launches` key (otherwise only the first launch will
    actually log artifacts and parameters).

    The `launches` key should be a list of dictionaries with the
    following parameters

    - `log_artifacts`: if `True` (default), will log the artifacts (the
      config and command given to the launcher)
    - `log_parameters`: if `True` (default) will log a flattened view of
      the parameters
    - `path_config`: if given, will write the config as an artifact with
      that name (default is `config.json`)
    - `path_command`: if given, will write the command as an artifact
      with that name (default is `launch.txt`, using the `.txt`
      extension because you can preview it on MlFlow).

    Example
    -------
    >>> import fromconfig
    >>> config = {
    ...     "run": None,
    ...     "launcher": {"log": ["logging", "mlflow"]},
    ...     "mlflow": {"run_name": "test"}
    ... }
    >>> launcher = fromconfig.launcher.Launcher.fromconfig(config["launcher"])
    >>> launcher(config, "run")
    """

    def __init__(self, launcher: fromconfig.launcher.Launcher):
        super().__init__(launcher=launcher)

    def __call__(self, config: Any, command: str = ""):
        if mlflow.active_run() is not None:
            LOGGER.info(f"Active run found: {get_url(mlflow.active_run())}")
            self.log_and_launch(config=config, command=command)
        else:
            # Create run from params in config
            params = config.get("mlflow") or {}
            run_id = params.get("run_id")
            run_name = params.get("run_name")
            tracking_uri = params.get("tracking_uri")
            experiment_name = params.get("experiment_name")
            artifact_location = params.get("artifact_location")

            # Setup experiment and general MlFlow parameters
            if tracking_uri is not None:
                mlflow.set_tracking_uri(tracking_uri)
            if experiment_name is not None:
                if mlflow.get_experiment_by_name(experiment_name) is None:
                    mlflow.create_experiment(experiment_name, artifact_location=artifact_location)
                mlflow.set_experiment(experiment_name)

            # Start MlFlow run, log information and launch
            with mlflow.start_run(run_id=run_id, run_name=run_name) as run:
                LOGGER.info(f"Started run: {get_url(run)}")
                config = fromconfig.utils.merge_dict(config, {"mlflow": {"run_id": run.info.run_id}})
                self.log_and_launch(config=config, command=command)

    def log_and_launch(self, config: Any, command: str = ""):
        """Log and launch config

        Parameters
        ----------
        config : Any
            Config
        command : str, optional
            Command
        """
        # Extract params for this launch
        params = config.get("mlflow") or {}
        launches = params.get("launches") or []
        launches = [launches] if not isinstance(launches, list) else launches
        launch = launches.pop(0) if launches else {}
        log_artifacts = launch.get("log_artifacts", True)
        log_parameters = launch.get("log_parameters", True)
        path_config = launch.get("path_config", "config.json")
        path_command = launch.get("path_command", "launch.txt")

        # Log artifacts
        if log_artifacts:
            LOGGER.info(f"Logging artifacts {path_config} and {path_command}")
            dir_artifacts = tempfile.mkdtemp()
            with Path(dir_artifacts, path_config).open("w") as file:
                json.dump(config, file, indent=4)
            with Path(dir_artifacts, path_command).open("w") as file:
                file.write(f"fromconfig {path_config} - {command}")
            mlflow.log_artifacts(local_dir=dir_artifacts)

        # Log parameters
        if log_parameters:
            LOGGER.info("Logging parameters")

            def _sanitize(s):
                return s.replace("[", ".__").replace("]", "__.")

            for key, value in fromconfig.utils.flatten(config):
                mlflow.log_param(key=_sanitize(key), value=value)

        # Update config (remove used params if successive launches)
        launches = launches if launches else [{}]
        launches[0] = fromconfig.utils.merge_dict({"log_artifacts": False, "log_parameters": False}, launches[0])
        config = fromconfig.utils.merge_dict(config, {"mlflow": {"launches": launches}})
        self.launcher(config=config, command=command)


def get_url(run) -> str:
    return f"{mlflow.get_tracking_uri()}/experiments/{run.info.experiment_id}/runs/{run.info.run_id}"
