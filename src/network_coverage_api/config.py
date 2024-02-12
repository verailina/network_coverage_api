from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="Network_Coverage_API",
    settings_files=["settings.toml"],
    environments=False,
    load_dotenv=True,
)
