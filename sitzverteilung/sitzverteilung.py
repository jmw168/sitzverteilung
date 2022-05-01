"""Dieses Modul berechnet eine Sitzverteilung nach art des deutschen Bundestages"""

import numpy as np
import pandas as pd

# pylint: disable=no-name-in-module, import-error
from sitzverteilung.hilfsmittel import load_yaml
from sitzverteilung.rechner.sainte_lague import SainteLague, losentscheid

METHODE_STRING = "divisor"


def sitzverteilung(pfad):
    """
    Berechne die Sitzverteilung mit den Eingabedaten im Verzeichnis

        :param pfad: Verzeichnispfad
    """
    # initialisiere Sitzverteilungsrechner
    sainte_lague = SainteLague(METHODE_STRING)

    # Lade Daten aus Dateien
    laender_yaml = load_yaml(pfad / "Länder.yaml")
    laender = pd.DataFrame(
        index=laender_yaml.keys(), data={"Stimmen": laender_yaml.values()}
    )
    erststimmen = {
        key: pd.DataFrame(value)
        for key, value in load_yaml(pfad / "Erststimme.yaml").items()
    }
    zweitstimmen = pd.DataFrame(load_yaml(pfad / "Zweitstimme.yaml"))

    # Zur Übersichtlichkeit in Zukunft: Einstellungen zu dict umbauen
    einstellungen = setze_einstellungen(pfad)
    direktmandate, mehrheitssieger, zweitstimmen = ermittle_zulassung(
        einstellungen["hürde"], erststimmen, zweitstimmen
    )

    # Überprüfe, ob es "unabhängige" Wahlkreissieger gibt
    unabhaengige = direktmandate.drop(zweitstimmen.index).sum(axis=1)
    unabhaengige = unabhaengige[unabhaengige > 0]
    gesamtsitze = einstellungen["sitze_geplant"] - unabhaengige.sum()

    # Verteilung der Sitze auf die Länder
    print("Verteile Sitze auf Länder")
    laender, lose = sainte_lague(laender, gesamtsitze)
    if lose:
        laender = losentscheid(laender, lose, gesamtsitze)

    mindestsitze = bestimme_mindestsitze(
        direktmandate, laender, einstellungen["mindestsitze_methode"], zweitstimmen
    )

    # Verteilung der Gesamtsitzanzahl
    print("Oberverteilung")
    stimmen = pd.DataFrame({"Stimmen": zweitstimmen.sum(axis=1)})
    stimmen, lose = sainte_lague(stimmen, gesamtsitze)
    if lose:
        stimmen = losentscheid(stimmen, lose, gesamtsitze)
    differenz = mindestsitze - stimmen["Sitze"]
    differenz = differenz.where(differenz > 0, 0)
    print("Überhangsmandate\n", differenz)
    while differenz.sum() > einstellungen["ueberhang"] and gesamtsitze < (
        einstellungen["obergrenze"] - differenz.sum()
    ):
        gesamtsitze += differenz.sum() - einstellungen["ueberhang"]
        print(f"erhöhe Sitzanzahl auf {gesamtsitze}")
        if gesamtsitze >= (einstellungen["obergrenze"] - differenz.sum()):
            print(f'Obergrenze von {einstellungen["obergrenze"]} erreicht')
            gesamtsitze = einstellungen["obergrenze"] - differenz.sum()
        stimmen, lose = sainte_lague(stimmen, gesamtsitze)
        if lose:
            stimmen = losentscheid(stimmen, lose, gesamtsitze)
        differenz = mindestsitze - stimmen["Sitze"]
        differenz = differenz.where(differenz > 0, 0)
    stimmen["Sitze"] += differenz
    gesamtsitze += differenz.sum()
    print("Unausgeglichene Überhangsmandate\n", differenz)

    # Wenn eine Partei über 50 % der Stimmen gewinnt, stehen ihr über 50 % der Sitze zu
    if mehrheitssieger is not None:
        while stimmen.at[mehrheitssieger, "Sitze"] * 2 <= gesamtsitze:
            print(f"erhöhe Sitze von {mehrheitssieger} auf über 50%")
            stimmen.at[mehrheitssieger, "Sitze"] += 1
            gesamtsitze += 1
    stimmen = (
        pd.concat((stimmen, unabhaengige[unabhaengige > 0].to_frame(name="Sitze")))
        .fillna(-1)
        .astype("int64")
    )
    gesamtsitze += unabhaengige.sum()
    print("Gesamtanzahl Sitze: ", gesamtsitze)
    print("Sitzverteilung\n", stimmen)


def bestimme_mindestsitze(direktmandate, laender, mindestsitze_methode, zweitstimmen):
    """
    Bestimme die Mindestsitze je Partei

        :param pd.DataFrame direktmandate:
        :param pd.DataFrame laender:
        :param str mindestsitze_methode: 'Keine', 'Pur' oder 'Mittelwert', siehe Dokumentation
        :param pd.DataFrame zweitstimmen:
        :return: Mindestsitze
        :rtype: pd.DataFrame
    """
    # initialisiere Sitzverteilungsrechner
    sainte_lague = SainteLague(METHODE_STRING)

    # erste Unterverteilung auf die Landeslisten
    erste_unterverteilung = pd.DataFrame()
    for land in laender.index:
        print(f"erste Unterverteilung in {land}")
        tabelle = pd.DataFrame({"Stimmen": zweitstimmen[land]})
        sitze, lose = sainte_lague(tabelle, laender.at[land, "Sitze"])
        if lose:
            sitze = losentscheid(sitze, lose, laender.at[land, "Sitze"])
        erste_unterverteilung[land] = sitze["Sitze"]
    # Bestimmung der Mindestsitze
    if mindestsitze_methode == "Keine":
        mindestsitze = direktmandate
    elif mindestsitze_methode == "Pur":
        mindestsitze = erste_unterverteilung.where(
            erste_unterverteilung > direktmandate.loc[zweitstimmen.index], direktmandate
        )
    elif mindestsitze_methode == "Mittelwert":
        mittelwert = pd.concat(
            [direktmandate.loc[zweitstimmen.index], erste_unterverteilung]
        )
        mittelwert = (
            mittelwert.groupby(level=0, sort=False)
            .mean()
            .apply(np.ceil)
            .astype("int64")
        )
        mindestsitze = mittelwert.where(
            mittelwert > direktmandate.loc[zweitstimmen.index], direktmandate
        )
    else:
        raise ValueError(
            f"Methode {mindestsitze_methode} für Mindestsitze nicht bekannt"
        )
    mindestsitze = mindestsitze.sum(axis=1)
    return mindestsitze


def ermittle_zulassung(huerde, erststimmen, zweitstimmen):
    """
    Bestimme, welche Parteien zur Sitzzuteilung zugelassen sind, beinhaltet Berechnung der Direktmandate
    :param dict erststimmen:
    :param dict huerde:
    :param pd.DataFrame zweitstimmen:
    :return: Gibt die Direktmandate, einen möglichen Mehrheitssieger und die Zweitstimmen der zugelassenen Parteien aus
    :rtype: (pd.DataFrame, str or None, pd.DataFrame)
    """
    # Überprüfe, welche Parteien bei der Sitzverteilung berücksichtigt werden
    zulassung = pd.DataFrame()
    stimmen = zweitstimmen.sum(axis=1)
    zulassung["Prozent"] = 100 * stimmen / stimmen.sum()

    # Stelle fest, ob eine Partei über 50 % der Stimmen erhalten hat (später wichtig)
    try:
        mehrheitssieger = zulassung[zulassung["Prozent"] > 50].index[0]
    except IndexError:
        mehrheitssieger = None

    # Zähle die Direktmandate der Parteien
    direktmandate = pd.DataFrame(index=zweitstimmen.index)
    for land, tabelle_land in erststimmen.items():
        direktmandate[land] = 0
        # pylint: disable=fixme
        # TODO: vektorisieren statt iterieren
        for _, stimmen in tabelle_land.items():
            if not stimmen.max() == 0:
                sieger = stimmen.idxmax()
                # sieger = 'DIE LINKE'
                direktmandate.at[sieger, land] += 1
    zulassung["Direkt"] = direktmandate.sum(axis=1)

    # Initialisiere Spalte für mögliche Ausnahmen von der Hürde (z.B. nationale Minderheiten)
    zulassung["Ausnahmen"] = False

    # Prüfung, welche Kriterien erfüllt sind
    if "Prozent" in huerde.keys():
        zulassung["Prozent"] = zulassung["Prozent"] >= huerde["Prozent"]
    else:
        zulassung["Prozent"] = False
    if "Direkt" in huerde.keys():
        zulassung["Direkt"] = zulassung["Direkt"] >= huerde["Direkt"]
    else:
        zulassung["Direkt"] = False
    if "Ausnahmen" in huerde.keys():
        for partei in huerde["Ausnahmen"]:
            zulassung.at[partei, "Ausnahmen"] = True
    zweitstimmen = zweitstimmen.loc[
        zulassung["Prozent"] | zulassung["Direkt"] | zulassung["Ausnahmen"]
    ]
    return direktmandate, mehrheitssieger, zweitstimmen


def setze_einstellungen(pfad):
    """
    Parse die Einstellungen aus Einstellungen.yaml

        :param pfad: Verzeichnis
        :return: Einstellungen
        :rtype: dict
    """
    # Setze Variablen aus Einstellungen
    settings_yaml = load_yaml(pfad / "Einstellungen.yaml")
    sitze_geplant = settings_yaml["Sitze"]  # erforderlich, kein default
    try:
        huerde = settings_yaml["Hürde"]
    except KeyError:
        huerde = {}
    try:
        mindestsitze_methode = settings_yaml["Mindestsitze"]
    except KeyError:
        mindestsitze_methode = "Keine"
    try:
        ueberhang = settings_yaml["Überhang"]
    except KeyError:
        ueberhang = 0
    try:
        obergrenze = settings_yaml["Obergrenze"]
    except KeyError:
        obergrenze = np.inf
    return {
        "sitze_geplant": sitze_geplant,
        "hürde": huerde,
        "mindestsitze_methode": mindestsitze_methode,
        "ueberhang": ueberhang,
        "obergrenze": obergrenze,
    }
