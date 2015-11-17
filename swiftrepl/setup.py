from setuptools import setup

setup(
    name="swiftrepl",
    version="0.0.1",
    long_description=__doc__,
    py_modules=['swiftrepl'],
    install_requires=['python-cloudfiles'],
    entry_points={
        'console_scripts': [
            ['swiftrepl = swiftrepl:main'],
        ],
    }
)
