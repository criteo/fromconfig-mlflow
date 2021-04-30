# FromConfig MlFlow
[![pypi](https://img.shields.io/pypi/v/fromconfig-mlflow.svg)](https://pypi.python.org/pypi/fromconfig-mlflow)
[![ci](https://github.com/criteo/fromconfig-mlflow/workflows/Continuous%20integration/badge.svg)](https://github.com/criteo/fromconfig-mlflow/actions?query=workflow%3A%22Continuous+integration%22)

A [fromconfig](https://github.com/criteo/fromconfig) `Launcher` for [MlFlow](https://www.mlflow.org) support.

<!-- MarkdownTOC -->

- [Install](#install)
- [Quickstart](#quickstart)
- [Artifacts and Parameters](#artifacts-and-parameters)
- [Usage-Reference](#usage-reference)
  - [`StartRunLauncher`](#startrunlauncher)
  - [`LogArtifactsLauncher`](#logartifactslauncher)
  - [`LogParamsLauncher`](#logparamslauncher)

<!-- /MarkdownTOC -->

<a id="install"></a>
## Install

```bash
pip install fromconfig_mlflow
```

<a id="quickstart"></a>
## Quickstart

Once installed, the launcher is available with the name `mlflow`.

Start a local MlFlow server with

```bash
mlflow server
```

You should see

```
[INFO] Starting gunicorn 20.0.4
[INFO] Listening at: http://127.0.0.1:5000
```

We will assume that the tracking URI is `http://127.0.0.1:5000` from now on.

Set the `MLFLOW_TRACKING_URI` environment variable

```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
```

Given the following module

```python
import mlflow


class Model:
    def __init__(self, learning_rate: float):
        self.learning_rate = learning_rate

    def train(self):
        print(f"Training model with learning_rate {self.learning_rate}")
        if mlflow.active_run():
            mlflow.log_metric("learning_rate", self.learning_rate)
```

and config files

`config.yaml`

```yaml
model:
  _attr_: foo.Model
  learning_rate: "${params.learning_rate}"
```

`params.yaml`

```yaml
params:
  learning_rate: 0.001
```

Run

```bash
fromconfig config.yaml params.yaml --launcher.log=mlflow - model - train
```

which prints

```
Started run: http://127.0.0.1:5000/experiments/0/runs/7fe650dd99574784aec1e4b18fceb73f
Training model with learning_rate 0.001
```

If you navigate to `http://127.0.0.1:5000/experiments/0/runs/7fe650dd99574784aec1e4b18fceb73f` you should the logged metric `learning_rate`.

You can also use a `launcher.yaml` file

```yaml
# Configure mlflow
mlflow:
  # tracking_uri: "http://127.0.0.1:5000"  # Or set env variable MLFLOW_TRACKING_URI
  # experiment_name: "test-experiment"  # Which experiment to use
  # run_id: 12345  # To restore a previous run
  # run_name: test  # To give a name to your new run
  # artifact_location: "path/to/artifacts"  # Used only when creating a new experiment

launcher:
  log: mlflow  # Start run
```

by running

```bash
fromconfig config.yaml params.yaml launcher.yaml - model - train
```

This example can be found in [`docs/examples/quickstart`](docs/examples/quickstart).

<a id="artifacts-and-parameters"></a>
## Artifacts and Parameters

In this example, we add logging of the config and parameters.

Re-using the [quickstart](#quickstart) code, modify the `launcher.yaml` file

```yaml
# Configure logging
logging:
  level: 20

# Configure mlflow
mlflow:
  # tracking_uri: "http://127.0.0.1:5000"  # Or set env variable MLFLOW_TRACKING_URI
  # experiment_name: "test-experiment"  # Which experiment to use
  # run_id: 12345  # To restore a previous run
  # run_name: test  # To give a name to your new run
  # artifact_location: "path/to/artifacts"  # Used only when creating a new experiment
  # include_keys:  # Only log params that match *model*
  #   - model

# Configure launcher
launcher:
  log:
    - logging
    - mlflow  # Start run
  parse:
    - mlflow_log_artifacts  # Log config.yaml and launch.sh
    - parser  # Parse config
    - mlflow_log_params  # Log flattened config as run parameters
```

and run

```bash
fromconfig config.yaml params.yaml launcher.yaml - model - train
```

If you navigate to the MlFlow run, you should see
- the original config (before parsing), saved as `config.yaml`, logged by `mlflow_log_artifacts`
- the parameters, a flattened version of the *parsed* config (`model.learning_rate` is `0.001` and not `${params.learning_rate}`) logged by `mlflow_log_params`.

This example can be found in [`docs/examples/artifacts-params`](docs/examples/artifacts-params).

<a id="usage-reference"></a>
## Usage-Reference

<a id="startrunlauncher"></a>
### `StartRunLauncher`

To configure MlFlow, add a `mlflow` entry to your config and set the following parameters

- `run_id`: if you wish to restart an existing run
- `run_name`: if you wish to give a name to your new run
- `tracking_uri`: to configure the tracking remote
- `experiment_name`: to use a different experiment than the custom
  experiment
- `artifact_location`: the location of the artifacts (config files)

Additionally, the launcher can be initialized with the following attributes

- `set_env_vars`: if True (default), set `MLFLOW_RUN_ID` and `MLFLOW_TRACKING_URI`
- `set_run_id`: if True (default), set `mlflow.run_id` in config.


For example

```yaml
# Configure mlflow
mlflow:
  # tracking_uri: "http://127.0.0.1:5000"  # Or set env variable MLFLOW_TRACKING_URI
  # experiment_name: "test-experiment"  # Which experiment to use
  # run_id: 12345  # To restore a previous run
  # run_name: test  # To give a name to your new run
  # artifact_location: "path/to/artifacts"  # Used only when creating a new experiment

launcher:
  log:
    - logging
    - _attr_: mlflow
      set_env_vars: true
      set_run_id: true
```

<a id="logartifactslauncher"></a>
### `LogArtifactsLauncher`

The launcher can be initialized with the following attributes

- `path_command`: Name for the command file. If `None`, don't log the command.
- `path_config`: Name for the config file. If `None`, don't log the config.

For example,

```yaml
launcher:
  log:
    - logging
    - mlflow
  parse:
    - _attr_: mlflow_log_artifacts
      path_command: launch.sh
      path_config: config.yaml
    - parser
    - _attr_: mlflow_log_artifacts
      path_command: null
      path_config: parsed.yaml
```


<a id="logparamslauncher"></a>
### `LogParamsLauncher`

The launcher will use `include_keys` and `ignore_keys`  if present in the config in the `mlflow` key.

- `ignore_keys` : If given, don't log some parameters that have some substrings.
- `include_keys` : If given, only log some parameters that have some substrings. Also shorten the flattened parameter to start at the first match. For example, if the config is `{"foo": {"bar": 1}}` and `include_keys=("bar",)`, then the logged parameter will be `"bar"`.
