"""MlFlow Log Params Launcher."""

from typing import Any, Iterable, List, Tuple
import re

import fromconfig
import mlflow


class LogParamsLauncher(fromconfig.launcher.Launcher):
    """Log params if an MlFlow Run is active.

    To configure, add a `mlflow` entry to your config and set the
    following parameters

    - ignore_keys : Iterable[str], optional
        If given, don't log some parameters that have some substrings.
    - include_keys : Iterable[str], optional
        If given, only log some parameters that have some substrings.
        Also shorten the flattened parameter to start at the first
        match. For example, if the config is `{"foo": {"bar": 1}}` and
        `include_keys=("bar",)`, then the logged parameter will be
        `"bar"`.
    """

    NAME = "log_params"

    def __call__(self, config: Any, command: str = ""):
        if mlflow.active_run() is not None:
            params = (config.get("mlflow") or {}) if fromconfig.utils.is_mapping(config) else {}  # type: ignore
            ignore_keys = params.get("ignore_keys", ["mlflow"])
            include_keys = params.get("include_keys")
            params = flatten(config, ignore_keys, include_keys)
            for idx in range(0, len(params), 100):
                mlflow.log_params(dict(params[idx : idx + 100]))
        self.launcher(config, command)


# log_params only accepts alphanumerics, period, space, dash, underscore
_FORBIDDEN = re.compile(r"[^0-9a-zA-Z_\. \-/]+")


def flatten(config, ignore_keys: Iterable[str] = None, include_keys: Iterable[str] = None) -> List[Tuple[str, Any]]:
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
