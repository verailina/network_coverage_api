from setuptools import setup, find_packages

setup_params = dict(
    name="network_coverage_api",
    version="0.1",
    description="Network coverage API",
    url="https://https://github.com/verailina/network_coverage_api",
    author="Vera Ilina",
    author_email="vilina.develop@gmail.com",
    keywords="network_coverage_api",
    package_dir={"": "src"},
    packages=find_packages("src"),
    extras_require={
        "test": ["pytest"],
    },
)

if __name__ == "__main__":
    setup(**setup_params)
