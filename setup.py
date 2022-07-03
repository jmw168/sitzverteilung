"""Installationsdatei für das Paket sitzverteilung"""

from setuptools import setup, find_packages

setup(
    name="sitzverteilung",
    version="0.1.1",
    packages=find_packages(),
    url="https://github.com/jmw168/sitzverteilung",
    license="",
    author="jmw168",
    author_email="76046615+jmw168@users.noreply.github.com",
    description="Programm zur Sitzverteilungsberechnung nach Art des Bundestages",
    install_requires=["requests", "pyyaml", "numpy", "pandas"],
)
