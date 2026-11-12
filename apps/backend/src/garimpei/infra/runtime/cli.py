import sys

from garimpei.config.env import ConfigurationError, load_config
from garimpei.infra.runtime.manifest import OperationError


def main(arguments: list[str]) -> int:
    try:
        return dispatch(arguments)
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 64
    except OperationError as error:
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        print(
            "Runtime operation failed (RUNTIME_ERROR); inspect owned private diagnostics",
            file=sys.stderr,
        )
        return 1


def dispatch(arguments: list[str]) -> int:
    from garimpei.infra.runtime.lifecycle import migrate, start, stop

    if not arguments:
        raise ConfigurationError("Expected init, stop, migrate or resolve")
    operation, *options = arguments
    config = load_config(require_secrets=operation not in {"stop", "resolve"})
    if operation == "init" and options in [[], ["--disposable"]]:
        start(config, disposable=options == ["--disposable"])
        return 0
    if operation == "stop" and options in [[], ["--clean"]]:
        stop(config, clean=options == ["--clean"])
        return 0
    if operation == "migrate":
        return migrate(config, options)
    if operation == "resolve" and not options:
        print(
            f"{config.environment_id} database={config.database} web={config.web_port} postgres={config.pg_port} waha={config.waha_port}"
        )
        return 0
    raise ConfigurationError(
        "Expected init [--disposable], stop [--clean], migrate (--check|--apply|--make NAME), resolve"
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
