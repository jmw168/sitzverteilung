"""Dieses Modul lädt Wahlergebnisdaten (bisher nur 2021) vom deutschen Bundeswahlleiter herunter und überführt die
aktuellsten Daten in ein yaml-Format für die Sitzverteilungsberechnung"""

from html.parser import HTMLParser

import pandas as pd
import requests
import yaml

from sitzverteilung.hilfsmittel import load_yaml

UNIONSMERGER = False


def download(pfad):
    """
    Lade die Rohdaten in den Ordner `daten` herunter und erstelle die entsprechenden Dateien im Arbeitsverzeichnis

    :param pfad: der Pfad des Arbeitsverzeichnisses
    :type pfad: pathlib.Path
    """
    lade_herunter(pfad)

    neuste_csv = sorted((pfad / "daten").glob("kerg2*.csv"))[-1]
    with open(neuste_csv, encoding="utf-8") as file:
        for _ in range(0, 6):
            inhalt = file.readline()
        print(inhalt.split(";")[:3])
    alle_ergebnisse = pd.read_csv(
        neuste_csv, delimiter=";", skiprows=9, encoding="utf8"
    )
    laender_yaml = load_yaml(pfad / "Länder.yaml")

    schreibe_zweitstimmen(alle_ergebnisse, laender_yaml, pfad)
    schreibe_erststimme(alle_ergebnisse, laender_yaml, pfad)

    kandidaten = pd.read_csv(
        pfad / "daten/btw21_kandidaturen_utf8.csv",
        delimiter=";",
        skiprows=8,
        encoding="utf8",
    )
    kandidaten = pd.DataFrame(kandidaten)
    schreibe_direktkandidaten(kandidaten, pfad)
    schreibe_listen(kandidaten, pfad)


def lade_herunter(pfad):
    """
    Lade alle Daten vom Bundeswahlleiter herunter

    :param pfad: Zielpfad des Ordners dateien
    :type pfad: pathlib.Path
    """
    ordner = pfad / "daten"
    if not ordner.exists():
        ordner.mkdir()
    url = "https://www.bundeswahlleiter.de/bundestagswahlen/2021/ergebnisse/opendata/daten/"
    bundeswahlleiter = requests.get(url)
    parser = MyHTMLParser(url, ordner)
    parser.feed(bundeswahlleiter.text)


def schreibe_zweitstimmen(alle_ergebnisse, laender_yaml, pfad):
    """
    Schreibe Zweitstimmenergebnisse in Zweitstimmen.yaml

        :param alle_ergebnisse: Daten des Bundeswahlleiters
        :type alle_ergebnisse: pd.DataFrame
        :param laender_yaml: Informationen zu den Bundesländern
        :type laender_yaml: dict
        :param pfad: Pfad des Arbeitsverzeichnisses
        :type pfad: pathlib.Path
    """
    gesamt_tabelle = pd.DataFrame()
    for land in laender_yaml.keys():
        ergebnis = alle_ergebnisse[
            (alle_ergebnisse["Gebietsname"] == land)
            & (alle_ergebnisse["Gruppenart"] == "Partei")
            & (alle_ergebnisse["Stimme"] == 2)
        ]
        ergebnis = ergebnis[["Gruppenname", "Anzahl"]]
        ergebnis = ergebnis.set_index("Gruppenname")
        if ergebnis["Anzahl"].sum() == 0:
            # raise Exception(f'Noch keine Zahlen aus {land}!')
            ergebnis["Anzahl"] = 1
        ergebnis = ergebnis.rename(columns={"Anzahl": land})
        gesamt_tabelle = pd.concat([gesamt_tabelle, ergebnis], axis=1)
    gesamt_tabelle = gesamt_tabelle.fillna(0)
    gesamt_tabelle = gesamt_tabelle.astype("int64")
    if UNIONSMERGER:
        gesamt_tabelle.loc["CDU"] += gesamt_tabelle.loc["CSU"]  # Unionsmerger
        gesamt_tabelle.loc["CSU"] = 0  # Unionsmerger
    with open(pfad / "Zweitstimme.yaml", "w", encoding="utf-8") as datei:
        yaml.dump(
            gesamt_tabelle.to_dict(),
            datei,
            sort_keys=False,
            encoding="utf-8",
            allow_unicode=True,
        )


def schreibe_erststimme(alle_ergebnisse, laender_yaml, pfad):
    """
    Schreibe Erststimmenergebnisse in Erststimmen.yaml

    :param alle_ergebnisse: Daten des Bundeswahlleiters
    :type alle_ergebnisse: pd.DataFrame
    :param laender_yaml: Informationen zu den Bundesländern
    :type laender_yaml: dict
    :param pfad: Pfad des Arbeitsverzeichnisses
    :type pfad: pathlib.Path
    """
    ergebnis = alle_ergebnisse[
        (alle_ergebnisse["Gebietsart"] == "Wahlkreis")
        & (alle_ergebnisse["Gruppenart"] == "Partei")
        & (alle_ergebnisse["Stimme"] == 1)
    ]
    if UNIONSMERGER:
        ergebnis = ergebnis.replace("CSU", "CDU")  # Unionsmerger
    bundesergebnis = {}
    for land in laender_yaml:
        landesergebnis = pd.DataFrame()
        nummer = (
            alle_ergebnisse[alle_ergebnisse["Gebietsname"] == land]
            .head(1)["Gebietsnummer"]
            .values[0]
        )
        teilergebnis = ergebnis[ergebnis["UegGebietsnummer"] == nummer]
        wahlkreise = teilergebnis.drop_duplicates(subset="Gebietsnummer")["Gebietsname"]
        for kreis in wahlkreise:
            kreisergebnis = teilergebnis[teilergebnis["Gebietsname"] == kreis][
                ["Gruppenname", "Anzahl"]
            ]
            kreisergebnis = kreisergebnis.set_index("Gruppenname")
            kreisergebnis = kreisergebnis.rename(columns={"Anzahl": kreis})
            landesergebnis = pd.concat([landesergebnis, kreisergebnis], axis=1)
        landesergebnis = landesergebnis.fillna(0)
        landesergebnis = landesergebnis.astype("int64")
        bundesergebnis.update({land: landesergebnis.to_dict()})
    with open(pfad / "Erststimme.yaml", "w", encoding="utf-8") as datei:
        yaml.dump(
            bundesergebnis, datei, sort_keys=False, encoding="utf-8", allow_unicode=True
        )


def schreibe_direktkandidaten(kandidaten, pfad):
    """
    Schreibe Direktkandidaten in Direktkandidaten.yaml

    :param kandidaten: Informationen zu allen Kandidaten
    :type kandidaten: pd.DataFrame
    :param pfad: Pfad des Arbeitsverzeichnisses
    :type pfad: pathlib.Path
    """
    direkt = kandidaten.loc[kandidaten["Gebietsart"] == "Wahlkreis"]
    kandidaten_dict = {}
    for wahlkreis in direkt["Gebietsname"].drop_duplicates():
        wahlkreis_dict = {}
        for _, kandidat in direkt[direkt["Gebietsname"] == wahlkreis].iterrows():
            wahlkreis_dict.update(
                {
                    kandidat["Gruppenname"]: ", ".join(
                        [kandidat["Nachname"], kandidat["Vornamen"]]
                    )
                }
            )
        kandidaten_dict.update({wahlkreis: wahlkreis_dict})
    with open(pfad / "Direktkandidaten.yaml", "w", encoding="utf-8") as datei:
        yaml.dump(
            kandidaten_dict,
            datei,
            sort_keys=False,
            encoding="utf-8",
            allow_unicode=True,
        )


def schreibe_listen(kandidaten, pfad):
    """
    Schreibe Listenkandidaten in Listenkandidaten.yaml

    :param kandidaten: Informationen zu allen Kandidaten
    :type kandidaten: pd.DataFrame
    :param pfad: Pfad des Arbeitsverzeichnisses
    :type pfad: pathlib.Path
    """
    liste = kandidaten.loc[kandidaten["Gebietsart"] == "Land"]
    kandidaten_dict = {}
    for land in liste["Gebietsname"].drop_duplicates():
        land_dict = {}
        for partei in liste[liste["Gebietsname"] == land][
            "Gruppenname"
        ].drop_duplicates():
            partei_list = []
            for _, kandidat in liste[
                (liste["Gebietsname"] == land) & (liste["Gruppenname"] == partei)
            ].iterrows():
                partei_list.append(
                    ", ".join([kandidat["Nachname"], kandidat["Vornamen"]])
                )
            land_dict.update({partei: partei_list})
        kandidaten_dict.update({land: land_dict})
    with open(pfad / "Listenkandidaten.yaml", "w", encoding="utf-8") as datei:
        yaml.dump(
            kandidaten_dict,
            datei,
            sort_keys=False,
            encoding="utf-8",
            allow_unicode=True,
        )


class MyHTMLParser(HTMLParser):
    """Der hier verwendete HTML-Parser"""

    def __init__(self, url, directory):
        super().__init__()
        self.flag = False
        self.url = url
        self.directory = directory

    def error(self, message):  # pylint: disable=missing-function-docstring, no-self-use
        print("Encountered an error:", message)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.flag = True

    def handle_endtag(self, tag):
        if tag == "a":
            self.flag = False

    def handle_data(self, data):
        if self.flag:
            datei = self.directory / data
            if not datei.exists():
                inhalt = requests.get(self.url + data)
                datei.write_bytes(inhalt.content)
