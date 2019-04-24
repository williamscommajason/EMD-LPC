#!/usr/bin/env python3

VERSION="0.1.1"

DESCRIPTION= "Integer encoding through Empirical Mode Decomposition (EMD) and Linear Predictive Coding (LPC)"

def main():
    import io
    from setuptools import setup


    with io.open('README.md', encoding="utf8") as f:
        long_description = f.read().strip()

    with open('requirement.txt') as fd:
        required = fd.read().splitlines()

    setup_params = dict(
        name="EMD-LPC",
        version=VERSION,
        description=DESCRIPTION,
        long_description=long_description,
        url="https://github.com/williamscommajason/EMD-LPC",
        author="Jason Williams",
        author_email="williaje@usc.edu",
        keyboards"integer encoding signal decomposition",
        packages=["EMD-LPC"],
        install_requires=required,
        python_requires='>=3.5, <4'

    )

    dist = setup(**setup_params)

if __name__ == '__main__':
    main()

