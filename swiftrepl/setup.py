from setuptools import setup

setup(
    name="swiftrepl",
    author="Mark Bergsma",
    author_email="mark@wikimedia.org",
    version="0.0.3",
    long_description=__doc__,
    py_modules=['swiftrepl'],
    install_requires=['python-cloudfiles'],
    entry_points={
        'console_scripts': [
            ['swiftrepl = swiftrepl:main'],
        ],
    }
)
