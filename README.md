# FromConfig MlFlow
[![pypi](https://img.shields.io/pypi/v/fromconfig-mlflow.svg)](https://pypi.python.org/pypi/fromconfig-mlflow)
[![ci](https://github.com/guillaumegenthial/fromconfig-mlflow/workflows/Continuous%20integration/badge.svg)](https://github.com/guillaumegenthial/fromconfig-mlflow/actions?query=workflow%3A%22Continuous+integration%22)

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

Given the following module

```python
class Model:
    def __init__(self, learning_rate: float):
        self.learning_rate = learning_rate

    def train(self):
        print(f"Training model with learning_rate {self.learning_rate}")
```

and config files

```yaml
# config.yaml
model:
  _attr_: foo.Model
  learning_rate: "@params.learning_rate"

# params.yaml
params:
  learning_rate: 0.001

# launcher.yaml
mlflow:
  tracking_uri: "http://127.0.0.1:5000"
logging:
  level: 20
launcher:
  log:
    - logging
    - mlflow
```

Run

```bash
fromconfig config.yaml params.yaml launcher.yaml - model - train
```

which prints

```
INFO:fromconfig.launcher.logger:- launcher.log[0]: logging
INFO:fromconfig.launcher.logger:- launcher.log[1]: mlflow
INFO:fromconfig.launcher.logger:- params.learning_rate: 0.001
INFO:fromconfig.launcher.logger:- mlflow.tracking_uri: http://127.0.0.1:5000
INFO:fromconfig.launcher.logger:- logging.level: 20
INFO:fromconfig.launcher.logger:- model._attr_: foo.Model
INFO:fromconfig.launcher.logger:- model.learning_rate: 0.001
INFO:fromconfig_mlflow.launcher:Started new run: http://127.0.0.1:5000/experiments/0/runs/e5ae42827da041fc989aca024040c725
INFO:fromconfig_mlflow.launcher:Logging artifacts config.json and launch.txt
INFO:fromconfig_mlflow.launcher:Logging parameters
Training model with learning_rate 0.001
```

If you navigate to `http://127.0.0.1:5000/experiments/0/runs/40ea35e951e942bc9f0b9c792c4ce1e7` you should see your parameters and configs.

This example can be found in [`docs/examples/quickstart`](docs/examples/quickstart).

<a id="usage-reference"></a>
## Usage Reference

<a id="options"></a>
### Options

To configure MlFlow, add a `mlflow` entry to your config.

You can set the following parameters

- `run_id`: if you wish to restart an existing run
- `run_name`: if you wish to give a name to your new run
- `tracking_uri`: to configure the tracking remote
- `experiment_name`: to use a different experiment than the custom experiment
- `artifact_location`: the location of the artifacts (config files)

Additionally, if you wish to call the `mlflow` launcher multiple times during the launch (for example once before the parser, and once after), you need to configure the different launches with the special `launches` key (otherwise only the first launch will actually log artifacts and parameters).

The `launches` key should be a list of dictionaries with the following parameters

- `log_artifacts`: if `True` (default), will log the artifacts (the config and command given to the launcher)
- `log_parameters`: if `True` (default) will log a flattened view of the parameters
- `path_config`: if given, will write the config as an artifact with that name (default is `config.json`)
- `path_command`: if given, will write the command as an artifact with that name (default is `launch.txt`, using the `.txt` extension because you can preview it on MlFlow).
- `include_keys`: if given, only log flattened parameters that have one of these keys as substring. Also shorten the flattened parameter to start at the first match. For example, if the config is `{"foo": {"bar": 1}}` and `include_keys=("bar",)`, then the logged parameter will be `"bar"`.
- `ignore_keys`: if given, parameters that have at least one of the keys as substring will be ignored.

See [the multi example](#multi).


<a id="examples"></a>
## Examples

<a id="multi"></a>
### Multi

Re-using the [quickstart](#quickstart) code, modify the `launcher.yaml` file

```yaml
mlflow:
  tracking_uri: "http://127.0.0.1:5000"
  launches:
    -
      log_artifacts: true
      log_parameters: false
      path_config: "config.json"
      path_command: "launch_config.txt"
    -
      log_artifacts: true
      log_parameters: true
      path_config: "parsed.json"
      path_command: "launch_parsed.json"
logging:
  level: 20
launcher:
  parse:
    - mlflow
    - parser
  log:
    - logging
    - mlflow
```

and run

```bash
fromconfig config.yaml params.yaml launcher.yaml - model - train
```

If you navigate to the MlFlow run, you should see
- the parameters, a flattened version of the *parsed* config (`model.learning_rate` is `0.001` and not `@params.learning_rate`)
- the original config, saved as `config.json`
- the parsed config, saved as `parsed.json`
