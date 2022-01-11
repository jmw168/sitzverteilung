"""Installationsdatei für das Paket sitzverteilung"""
from setuptools import setup

import sitzverteilung

setup(
    name='sitzverteilung',
    version=sitzverteilung.__version__,
    packages=['sitzverteilung'],
    url='https://github.com/jmw168/sitzverteilung',
    license='',
    author='jmw168',
    author_email='76046615+jmw168@users.noreply.github.com',
    description='Programm zur Sitzverteilungsberechnung nach Art des Bundestages',
    install_requires=['requests', 'pyyaml', 'numpy', 'pandas']
)
