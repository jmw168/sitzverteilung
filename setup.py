"""Installationsdatei für das Paket sitzverteilung"""
from distutils.util import convert_path

from setuptools import setup

main_ns = {}
ver_path = convert_path('sitzverteilung/__init__.py')
with open(ver_path, encoding='utf8') as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name='sitzverteilung',
    version=main_ns['__version__'],
    packages=['sitzverteilung'],
    url='https://github.com/jmw168/sitzverteilung',
    license='',
    author='jmw168',
    author_email='76046615+jmw168@users.noreply.github.com',
    description='Programm zur Sitzverteilungsberechnung nach Art des Bundestages',
    install_requires=['requests', 'pyyaml', 'numpy', 'pandas']
)
