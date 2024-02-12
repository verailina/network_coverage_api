from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["network_coverage_api/settings.toml"],
)
