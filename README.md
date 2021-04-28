# FromConfig MlFlow
[![pypi](https://img.shields.io/pypi/v/fromconfig-mlflow.svg)](https://pypi.python.org/pypi/fromconfig-mlflow)
[![ci](https://github.com/criteo/fromconfig-mlflow/workflows/Continuous%20integration/badge.svg)](https://github.com/criteo/fromconfig-mlflow/actions?query=workflow%3A%22Continuous+integration%22)

A [fromconfig](https://github.com/criteo/fromconfig) `Launcher` for [MlFlow](https://www.mlflow.org) support.

<!-- MarkdownTOC -->

- [Install](#install)
- [Quickstart](#quickstart)
- [Usage Reference](#usage-reference)
  - [Options](#options)
- [Examples](#examples)
  - [Multi](#multi)

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

If you navigate to `http://127.0.0.1:5000/experiments/0/runs/7fe650dd99574784aec1e4b18fceb73f` you should see your parameters and configs.

This example can be found in [`docs/examples/quickstart`](docs/examples/quickstart).

You can also use a `launcher.yaml` file

```yaml
# Configure mlflow
mlflow:
  # tracking_uri: "http://127.0.0.1:5000"
  # experiment_name: "test-experiment"
  # run_name: test
  # artifact_location: "path/to/artifacts"

# Configure launcher (only change the log step)
launcher:
  log: mlflow
```

by running

```bash
fromconfig config.yaml params.yaml launcher.yaml - model - train
```

<a id="usage-reference"></a>
## Usage Reference

<a id="options"></a>
### Options
To configure MlFlow, add a `mlflow` entry to your config and set the following parameters

- `run_id`: if you wish to restart an existing run
- `run_name`: if you wish to give a name to your new run
- `tracking_uri`: to configure the tracking remote
- `experiment_name`: to use a different experiment than the custom
  experiment
- `artifact_location`: the location of the artifacts (config files)

You can also set the following attributes

- log_artifacts : bool, optional
      If True, save config and command as artifacts.
- log_parameters : bool, optional
      If True, log flattened config as parameters.
- path_command : str, optional
      Name for the command file
- path_config : str, optional
      Name for the config file.
- set_env_vars : bool, optional
      If True, set MlFlow environment variables.
- set_run_id : bool, optional
      If True, the run_id is overridden in the config.
- ignore_keys : Iterable[str], optional
      If given, don't log some parameters that have some substrings.
- include_keys : Iterable[str], optional
      If given, only log some parameters that have some substrings.
      Also shorten the flattened parameter to start at the first
      match. For example, if the config is `{"foo": {"bar": 1}}` and
      `include_keys=("bar",)`, then the logged parameter will be
      `"bar"`.


<a id="examples"></a>
## Examples

<a id="multi"></a>
### Multi

In this example, we show how to call and configure multiple launches of the `MlFlowLauncher`. We first log the non-parsed configs, then parse, then log both the parsed configs and the flattened parameters.

Re-using the [quickstart](#quickstart) code, modify the `launcher.yaml` file

```yaml
# Configure logging
logging:
  level: 20

# Configure mlflow
mlflow:
  # tracking_uri: "http://127.0.0.1:5000"
  # experiment_name: "test-experiment"
  # run_name: test
  # artifact_location: "path/to/artifacts"

launcher:
  parse:
    - _attr_: fromconfig_mlflow.MlFlowLauncher  # Log non-parsed config
      log_artifacts: true
      log_params: false
      path_config: "config.yaml"
      path_command: "config_launch.sh"
    - parser  # Parse config
    - _attr_: fromconfig_mlflow.MlFlowLauncher  # Log parsed config and parameters
      log_artifacts: true
      log_params: true
      path_config: "parsed.yaml"
      path_command: "parsed_launch.sh"
      include_keys:  # Only parameters that start with model will be logged as parameters
        - model

```

and run

```bash
fromconfig config.yaml params.yaml launcher.yaml - model - train
```

If you navigate to the MlFlow run, you should see
- the parameters, a flattened version of the *parsed* config (`model.learning_rate` is `0.001` and not `${params.learning_rate}`)
- the original config, saved as `config.yaml`
- the parsed config, saved as `parsed.yaml`
