from setuptools import setup, find_packages

setup(
    name='DRY',
    version='1.0',
    packages=find_packages(),
    install_requires=["ruamel.yaml", "flatdict", "melddict"],
    url='https://github.com/mhs-rajaei/DRY',
    license='MIT',
    author='MR',
    author_email='mrajaie1@gmail.com',
    description='DRY: Don’t Repeat Yourself (Merge, Extend and Override your configuration file)'
)
