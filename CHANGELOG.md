# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org).


## [0.3.0] - 2021-04-30

### Added
### Changed
- split launcher into `StartRunLauncher`, `LogParamsLauncher`, and `LogArtifactsLauncher`

### Deprecated
### Removed
### Fixed
### Security


## [0.2.0] - 2021-04-27

### Added
### Changed
- "behavioral" parameters now in the init
- `print` instead of `LOGGER.info` for run URL

### Deprecated
### Removed
- `launches` mechanism to configure multi-launches.

### Fixed
### Security


## [0.1.4] - 2021-04-23

### Added
- Parameter sanitation for mlflow
- Add set_run_id option in parameters

### Changed
- Moved repo to Criteo org

### Deprecated
### Removed
### Fixed
### Security


## [0.1.3] - 2021-04-22

### Added
- `set_env_vars` option
- `include_keys` and ignore_keys options to log parameters

### Changed
### Deprecated
### Removed
### Fixed
### Security


## [0.1.1] - 2021-04-20

### Added
- `sanitize` keys for parameters: now changes `a[0].b` into `a.0.b` instead of `a.__0__.b`

### Changed
### Deprecated
### Removed
### Fixed
### Security


## [0.1.0] - 2021-04-07

### Added
- Initial commit

### Changed
### Deprecated
### Removed
### Fixed
### Security
