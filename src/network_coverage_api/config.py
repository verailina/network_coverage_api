from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=[
        "src/network_coverage_api/settings.toml",
        "network_coverage_api/settings.toml",
    ],
)
