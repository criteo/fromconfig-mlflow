"""MlFlow Launcher."""

from pathlib import Path
from typing import Any, Iterable
import logging
import os
import re
import tempfile

import fromconfig
import mlflow


LOGGER = logging.getLogger(__name__)


_RUN_ID_ENV_VAR = "MLFLOW_RUN_ID"
_TRACKING_URI_ENV_VAR = "MLFLOW_TRACKING_URI"


class MlFlowLauncher(fromconfig.launcher.Launcher):
    """MlFlow Launcher.

    To configure MlFlow, add a `mlflow` entry to your config and set the
    following parameters

    - `run_id`: if you wish to restart an existing run
    - `run_name`: if you wish to give a name to your new run
    - `tracking_uri`: to configure the tracking remote
    - `experiment_name`: to use a different experiment than the custom
      experiment
    - `artifact_location`: the location of the artifacts (config files)

    Attributes
    ----------
    log_artifacts : bool, optional
        If True, save config and command as artifacts.
    log_params : bool, optional
        If True, log flattened config as parameters.
    path_command : str, optional
        Name for the command file
    path_config : str, optional
        Name for the config file.
    set_env_vars : bool, optional
        If True, set MlFlow environment variables.
    set_run_id : bool, optional
        If True, the run_id is overridden in the config.
    ignore_keys : Iterable[str], optional
        If given, don't log some parameters that have some substrings.
    include_keys : Iterable[str], optional
        If given, only log some parameters that have some substrings.
        Also shorten the flattened parameter to start at the first
        match. For example, if the config is `{"foo": {"bar": 1}}` and
        `include_keys=("bar",)`, then the logged parameter will be
        `"bar"`.
    """

    def __init__(
        self,
        launcher: fromconfig.launcher.Launcher,
        log_artifacts: bool = True,
        log_params: bool = True,
        path_command: str = "launch.sh",
        path_config: str = "config.yaml",
        set_env_vars: bool = False,
        set_run_id: bool = True,
        ignore_keys: Iterable[str] = None,
        include_keys: Iterable[str] = None,
    ):
        super().__init__(launcher=launcher)
        self.ignore_keys = ignore_keys
        self.include_keys = include_keys
        self.log_artifacts = log_artifacts
        self.log_params = log_params
        self.path_command = path_command
        self.path_config = path_config
        self.set_env_vars = set_env_vars
        self.set_run_id = set_run_id

    def __call__(self, config: Any, command: str = ""):
        if mlflow.active_run() is not None:
            print(f"Active run found: {get_url(mlflow.active_run())}")
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
                print(f"Started run: {get_url(run)}")
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
        # Log artifacts
        if self.log_artifacts:
            LOGGER.info(f"Logging artifacts {self.path_config} and {self.path_command}")
            dir_artifacts = tempfile.mkdtemp()
            fromconfig.dump(config, Path(dir_artifacts, self.path_config))
            with Path(dir_artifacts, self.path_command).open("w") as file:
                file.write(f"fromconfig {self.path_config} - {command}")
            mlflow.log_artifacts(local_dir=dir_artifacts)

        # Log parameters by batches of 100
        if self.log_params:
            LOGGER.info("Logging params")
            params = get_params(config, self.ignore_keys, self.include_keys)
            for idx in range(0, len(params), 100):
                mlflow.log_params(dict(params[idx : idx + 100]))

        # A bit risky as ENV variables are global, risk conflicts with
        # another place that would set / use these
        if self.set_env_vars:
            LOGGER.info(f"Setting ENV variables {_RUN_ID_ENV_VAR} and {_TRACKING_URI_ENV_VAR}")
            os.environ[_RUN_ID_ENV_VAR] = mlflow.active_run().info.run_id
            os.environ[_TRACKING_URI_ENV_VAR] = mlflow.tracking.get_tracking_uri()

        # Update run_id to override config for future launches
        if self.set_run_id:
            LOGGER.info("Setting mlflow.run_id in config")
            run_id = mlflow.active_run().info.run_id
            config = fromconfig.utils.merge_dict(config, {"mlflow": {"run_id": run_id}})

        # Launch
        self.launcher(config=config, command=command)

        # Clean up the environment variables once not needed
        if self.set_env_vars:
            LOGGER.info(f"Cleaning ENV variables {_RUN_ID_ENV_VAR} and {_TRACKING_URI_ENV_VAR}")
            del os.environ[_RUN_ID_ENV_VAR]
            del os.environ[_TRACKING_URI_ENV_VAR]


# log_params only accepts alphanumerics, period, space, dash, underscore
_FORBIDDEN = re.compile(r"[^0-9a-zA-Z_\. \-/]+")


def get_params(config, ignore_keys=None, include_keys=None):
    """Log param if coherent with ignore keys and include keys."""
    params = []
    for key, value in fromconfig.utils.flatten(config):
        if include_keys and not any(k in key for k in include_keys):
            continue
        if include_keys:
            for k in include_keys:
                index = key.find(k)
                if index != -1:
                    key = key[index:]
        if ignore_keys and any(k in key for k in ignore_keys):
            continue
        params.append((_FORBIDDEN.sub("_", key), value))
    return params


def get_url(run) -> str:
    return f"{mlflow.get_tracking_uri()}/experiments/{run.info.experiment_id}/runs/{run.info.run_id}"
