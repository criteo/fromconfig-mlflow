"""MlFlow Launcher."""

from typing import Any, Optional
import logging
import os

import fromconfig
import mlflow


LOGGER = logging.getLogger(__name__)


_RUN_ID_ENV_VAR = "MLFLOW_RUN_ID"
_TRACKING_URI_ENV_VAR = "MLFLOW_TRACKING_URI"


class StartRunLauncher(fromconfig.launcher.Launcher):
    """MlFlow Start Run.

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
    set_env_vars : bool, optional
        If True, set MlFlow environment variables.
    set_run_id : bool, optional
        If True, the run_id is overridden in the config.
    """

    def __init__(
        self, launcher: fromconfig.launcher.Launcher = None, set_env_vars: bool = True, set_run_id: bool = False,
    ):
        super().__init__(launcher=launcher)
        self.set_env_vars = set_env_vars
        self.set_run_id = set_run_id

    def __call__(self, config: Any, command: str = ""):
        if mlflow.active_run() is not None:
            print(f"Active run found: {get_url(mlflow.active_run())}")
            self.launch(config=config, command=command)
        else:
            # Create run from params in config
            params = (config.get("mlflow") or {}) if fromconfig.utils.is_mapping(config) else {}  # type: ignore
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
                self.launch(config=config, command=command)

    def launch(self, config: Any, command: str = ""):
        """Log and launch config

        Parameters
        ----------
        config : Any
            Config
        command : str, optional
            Command
        """
        # Store existing environment variables
        previous_run_id_env_var = os.environ.get(_RUN_ID_ENV_VAR)
        previous_tracking_uri_env_var = os.environ.get(_TRACKING_URI_ENV_VAR)

        # Override or set environment variables for this run
        if self.set_env_vars:
            LOGGER.debug(f"Setting ENV variables {_RUN_ID_ENV_VAR} and {_TRACKING_URI_ENV_VAR}")
            os.environ[_RUN_ID_ENV_VAR] = mlflow.active_run().info.run_id
            os.environ[_TRACKING_URI_ENV_VAR] = mlflow.tracking.get_tracking_uri()

        # Update run_id to override config for future launches
        if self.set_run_id:
            LOGGER.debug("Setting mlflow.run_id in config")
            run_id = mlflow.active_run().info.run_id
            config = fromconfig.utils.merge_dict(config, {"mlflow": {"run_id": run_id}})

        # Launch
        self.launcher(config=config, command=command)

        # Restore environment variable as they were prior to the launch
        if self.set_env_vars:

            def _restore(name: str, previous: Optional[str]):
                if previous is None:
                    del os.environ[name]
                else:
                    os.environ[name] = previous

            _restore(_RUN_ID_ENV_VAR, previous_run_id_env_var)
            _restore(_TRACKING_URI_ENV_VAR, previous_tracking_uri_env_var)


def get_url(run) -> str:
    return f"{mlflow.get_tracking_uri()}/experiments/{run.info.experiment_id}/runs/{run.info.run_id}"
