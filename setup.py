from setuptools import setup, find_packages

setup(
    name="ankidory",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "anki>=24.0",
        "aqt>=24.0",
        "openai>=1.3.0",
        "httpx>=0.25.0",
        "configparser>=5.3.0",
    ],
    entry_points={
        "console_scripts": [
            "ankidory=ankidory.main:main",
        ],
    },
)
