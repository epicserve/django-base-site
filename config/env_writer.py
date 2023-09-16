import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import environs


class EnvWriter:
    var_data: dict[str, Any]
    write_dot_env_file: bool = False
    base_dir: Path

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        read_dot_env_file: bool = True,
        eager: bool = True,
        expand_vars: bool = False,
    ):
        self.var_data = {}
        self._env = environs.Env(eager=eager, expand_vars=expand_vars)
        self.write_dot_env_file = self._env.bool("WRITE_DOT_ENV_FILE", default=False)
        self._env = environs.Env(eager=eager, expand_vars=expand_vars)
        self.base_dir = environs.Path(__file__).parent if base_dir is None else base_dir  # type: ignore
        if read_dot_env_file is True and self.write_dot_env_file is False:
            self._env.read_env(str(self.base_dir.joinpath(".env")))

    def _get_var(
        self,
        environs_instance,
        var_type: str,
        environ_args: tuple[Any, ...],
        environ_kwargs: Optional[dict[str, Any]] = None,
    ):
        environ_kwargs = environ_kwargs or {}
        help_text = environ_kwargs.pop("help_text", None)
        initial = environ_kwargs.pop("initial", None)

        if self.write_dot_env_file is True:
            self.var_data[environ_args[0]] = {
                "type": var_type,
                "default": environ_kwargs.get("default"),
                "help_text": help_text,
                "initial": initial,
            }

        try:
            return getattr(environs_instance, var_type)(*environ_args, **environ_kwargs)
        except environs.EnvError as e:
            if self.write_dot_env_file is False:
                raise e

    def __call__(self, *args, **kwargs):
        return self._get_var(self._env, var_type="str", environ_args=args, environ_kwargs=kwargs)

    def __getattr__(self, item):
        allowed_methods = [
            "int",
            "bool",
            "str",
            "float",
            "decimal",
            "list",
            "dict",
            "json",
            "datetime",
            "date",
            "time",
            "path",
            "log_level",
            "timedelta",
            "uuid",
            "url",
            "enum",
            "dj_db_url",
            "dj_email_url",
            "dj_cache_url",
        ]
        if item not in allowed_methods:
            return AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")

        def _get_var(*args, **kwargs):
            return self._get_var(self._env, var_type=item, environ_args=args, environ_kwargs=kwargs)

        return _get_var

    def write_env_file(self, env_file_path: Optional[Path] = None, overwrite_existing: bool = False):
        if env_file_path is None:
            env_file_path = self.base_dir.joinpath(".env")

        if env_file_path.exists() is True and overwrite_existing is False:
            backup_path = f"{env_file_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.copy(env_file_path, backup_path)

        with open(env_file_path, "w") as f:
            env_str = (
                f"# This is an initial .env file generated on {datetime.now(timezone.utc).isoformat()}. Any environment variable with a default\n"  # noqa: E501
                "# can be safely removed or commented out. Any variable without a default must be set.\n\n"
            )
            for key, data in self.var_data.items():
                initial = data.get("initial", None)
                val = ""

                if data["help_text"] is not None:
                    env_str += f"# {data['help_text']}\n"
                env_str += f"# type: {data['type']}\n"

                if data["default"] is not None:
                    env_str += f"# default: {data['default']}\n"

                if initial is not None and val == "":
                    val = initial()

                if val == "" and data["default"] is not None:
                    env_str += f"# {key}={val}\n\n"
                else:
                    env_str += f"{key}={val}\n\n"

            f.write(env_str)
