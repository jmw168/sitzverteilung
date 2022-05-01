"""Einstiegsskript für den Sitzverteilungsrechner"""

import argparse
from pathlib import Path

from sitzverteilung.download import download
from sitzverteilung.sitzverteilung import sitzverteilung


def parse():
    """
    Argumentenparser

        :return: geparste Argumente
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b",
        "--beispiel",
        help="wähle ein Beispiel aus dem Ordner beispiele",
        nargs=2,
        default="",
    )
    return parser.parse_args()


def main():
    """
    Hauptroutine für die Sitzverteilung
    """
    args = parse()

    beispiel = args.beispiel

    # setze den Datenpfad
    pfad = Path(".")
    if beispiel:
        pfad = pfad / "beispiele"
    for ordner in beispiel:
        pfad = pfad / ordner
    if not pfad.exists():
        raise ValueError(f"Das angegebene Beispiel am Ort {pfad} existiert nicht")

    if beispiel:
        if beispiel[0] == "bundestag":
            download(pfad)

    sitzverteilung(pfad)


if __name__ == "__main__":
    main()
