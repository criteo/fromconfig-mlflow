"""MlFlow Launcher."""

from pathlib import Path
from typing import Any
import json
import logging
import tempfile
import os

import fromconfig
import mlflow


LOGGER = logging.getLogger(__name__)


_RUN_ID_ENV_VAR = "MLFLOW_RUN_ID"
_MLFLOW_TRACKING_URI = "MLFLOW_TRACKING_URI"


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
    - `include_keys`: if given, only log flattened parameters that have
      one of these keys as substring. Also shorten the flattened
      parameter to start at the first match. For example, if the config
      is `{"foo": {"bar": 1}}` and `include_keys=("bar",)`, then the
      logged parameter will be `"bar"`.
    - `ignore_keys`: if given, parameters that have at least one of the
      keys as substring will be ignored.
    - `set_env_vars`: if given, mlflow environment variables are set, to
      propagate the mlflow run id and tracking uri

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
        launch = launches[0] if launches else {}
        log_artifacts = launch.get("log_artifacts", True)
        log_parameters = launch.get("log_parameters", True)
        path_config = launch.get("path_config", "config.json")
        path_command = launch.get("path_command", "launch.txt")
        include_keys = launch.get("include_keys")
        ignore_keys = launch.get("ignore_keys")
        set_env_vars = launch.get("set_env_vars", False)

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
            params = get_params(config, ignore_keys, include_keys)
            for idx in range(0, len(params), 100):
                mlflow.log_params(dict(params[idx : idx + 100]))

        # A bit risky as environment variables are global, risk conflicts with
        # another place that would set these env variables
        if set_env_vars:
            os.environ[_RUN_ID_ENV_VAR] = mlflow.active_run().info.run_id
            os.environ[_MLFLOW_TRACKING_URI] = mlflow.tracking.get_tracking_uri()

        # Update config (remove used params if successive launches)
        launches = launches[1:] if launches else []
        launches = launches if launches else [{}]
        launches[0] = fromconfig.utils.merge_dict({"log_artifacts": False, "log_parameters": False}, launches[0])
        config = fromconfig.utils.merge_dict(config, {"mlflow": {"launches": launches}})
        self.launcher(config=config, command=command)

        # Clean up the environment variables once not needed
        if set_env_vars:
            del os.environ[_RUN_ID_ENV_VAR]
            del os.environ[_MLFLOW_TRACKING_URI]


def get_params(config, ignore_keys=None, include_keys=None):
    """Log param if coherent with ignore keys and include keys."""
    params = []
    for key, value in fromconfig.utils.flatten(config):
        key = str(key).replace("[", ".").replace("]", "")
        if include_keys and not any(k in key for k in include_keys):
            continue
        if include_keys:
            for k in include_keys:
                index = key.find(k)
                if index != -1:
                    key = key[index:]
        if ignore_keys and any(k in key for k in ignore_keys):
            continue
        params.append((key, value))
    return params


def get_url(run) -> str:
    return f"{mlflow.get_tracking_uri()}/experiments/{run.info.experiment_id}/runs/{run.info.run_id}"
