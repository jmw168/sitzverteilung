"""Gesammelte Methoden für die Berechnung von Divisormethoden. Derzeit nur Standardrundung."""

import decimal

import numpy as np
import pandas as pd

from sitzverteilung.hilfsmittel import nice_round, remove_exponent, sort_two

HALB = decimal.Decimal("0.5")


def sainte_lague_divisor(
    tabelle: pd.DataFrame, sitze: int
) -> tuple[pd.DataFrame, list]:
    """
    Nutze das Sainte-Laguë-Divisorverfahren zur Sitzberechnung

        :param sitze: Anzahl zu verteilender Sitze
        :param pd.DataFrame tabelle: Dataframe mit Stimmenverteilung
        :return: Dataframe erweitert um Sitzverteilung, Liste für Verlosung
    """
    # initiiere decimal-modul und übertrage Zahlen in decimal. Decimal ist hier notwendig für exaktes runden.
    decimal.setcontext(decimal.Context(rounding=decimal.ROUND_HALF_UP))
    tabelle = tabelle.applymap(decimal.Decimal)
    lose = []

    # bestimme vorläufigen Divisor und ermittle die entsprechende Sitzanzahl
    divisor = tabelle["Stimmen"].sum() / sitze
    tabelle["Sitze"] = (tabelle["Stimmen"] / divisor).map(
        decimal.Decimal.to_integral_value
    )

    # Differenz zwischen zu verteilenden Sitzen und verteilten Sitzen
    differenz = tabelle["Sitze"].sum() - sitze

    # wenn nötig: Diskrepanzabbaumethode
    if not differenz == 0:
        # versuche zunächst diskrepanz einfach abzubauen
        tabelle_neu = diskrepanzabbaumethode(tabelle, int(differenz), divisor)

        # wenn diskrepanz nicht auflösbar → Losentscheid notwendig
        if isinstance(tabelle_neu, int):
            los_kandidaten = tabelle_neu
            # bestimme Untergrenze, für die Sitze problemlos verteilt werden können
            tabelle_neu, _ = sainte_lague_divisor(tabelle, sitze - 1)
            # bestimme Obergrenze
            tabelle_ueberschuss, _ = sainte_lague_divisor(
                tabelle, tabelle_neu["Sitze"].sum() + los_kandidaten
            )
            # wenn eine Tabelle zurückgegeben wurde, kann ermittelt werden, wer die Lose erhält
            if not isinstance(tabelle_neu, int):
                lose = tabelle.index[
                    (tabelle_ueberschuss["Sitze"] - tabelle_neu["Sitze"]) == 1
                ].to_list()
        tabelle: pd.DataFrame = tabelle_neu

    # wähle "schönen" Zitierdivisor
    divisor = bestimme_zitierdivisor(tabelle)

    # endgültige Sitzberechnung
    tabelle["Sitze"] = (tabelle["Stimmen"] / divisor).apply(
        lambda x: x.to_integral_value()
    )

    return tabelle.astype("int64"), lose


def bestimme_zitierdivisor(tabelle: pd.DataFrame) -> decimal.Decimal:
    """
    bestimme einen "schönen" divisor für die gegebene Sitzverteilung

        :param tabelle: Tabelle mit Sitzverteilung
        :return: "schöner" Divisor
    """
    # Stelle sicher, dass die äußere Tabelle unbeeinträchtigt bleibt
    tabelle = tabelle.copy()

    # bestimme neue Divisorgrenzen
    for schritt in [-1, 1]:
        rundung = decimal.ROUND_UP if schritt > 0 else decimal.ROUND_DOWN
        decimal.setcontext(decimal.Context(rounding=rundung))
        tabelle[f"Divisor {- schritt * HALB}"] = bestimme_divisoren(tabelle, schritt)

    # setze Rundung zurück
    rundung = decimal.ROUND_HALF_UP
    decimal.setcontext(decimal.Context(rounding=rundung))

    # ermittle Grenzen
    untergrenze = tabelle[f"Divisor {HALB}"].max()
    obergrenze = tabelle[f"Divisor {- HALB}"].min()

    # wähle "schönen" Divisor
    divisor = decimal.Decimal(
        nice_round(remove_exponent(untergrenze), remove_exponent(obergrenze))
    )
    return divisor


def bestimme_divisoren(tabelle: pd.DataFrame, schritt: int) -> pd.Series:
    """
    bestimme Tabellenspalten mit möglichen Divisoren
    :param tabelle: Tabelle mit bisheriger Sitzverteilung
    :param schritt: Schrittweite
    :return: Spalte mit Divisoren
    """
    return (tabelle["Stimmen"] / (tabelle["Sitze"] - schritt * HALB)).where(
        lambda x: x > 0, decimal.Decimal("nan")
    )


def diskrepanzabbaumethode(
    tabelle: pd.DataFrame, differenz: int, divisor: decimal.Decimal
) -> pd.DataFrame | int:
    """
    Algorithmus um Diskrepanz zwischen zuerst verteilten Sitzen und tatsächlich zu verteilenden Sitzen zu eliminieren
    :param tabelle: Tabelle mit Sitzen
    :param differenz: Differenz zwischen zu verteilenden Sitzen und tatsächlich verteilten Sitzen
    :param divisor: für die gegebene Sitzverteilung verwendeter Divisor
    :return: Tabelle mit korrigierter Sitzverteilung
    """
    tabelle = tabelle.copy()

    # Bestimme Vorzeichen für Richtung
    vorzeichen = np.sign(differenz)

    # Ergänze Tabelle um Divisorspalten
    for schritt in range(vorzeichen, (differenz + vorzeichen) * 2, vorzeichen * 2):
        tabelle[f"Divisor {- schritt * HALB}"] = (
            tabelle["Stimmen"] / (tabelle["Sitze"] - schritt * HALB)
        ).replace(0, decimal.Decimal("nan"))

    # erstelle gesamte Divisorliste
    divisorliste = (
        pd.concat(
            [tabelle[zeile] for zeile in tabelle.columns if zeile.startswith("Divisor")]
        )
        .dropna()
        .sort_values()
    )

    # finde index des Divisors
    divisorpointer = divisorliste.searchsorted(divisor)

    # Handling falls Losentscheid notwendig
    if (
        divisorliste.iloc[divisorpointer + differenz - 1]
        == divisorliste.iloc[divisorpointer + differenz]
    ):
        return int(
            divisorliste.value_counts()[divisorliste.iloc[divisorpointer + differenz]]
        )

    # tatsächliche diskrepanzabbaumethode: bestimme betroffenen Indexbereich
    untergrenze, obergrenze = sort_two(divisorpointer, divisorpointer + differenz)

    # bestimme In-/Dekrementierungskandidaten
    diskrepanz = divisorliste.index[untergrenze:obergrenze]

    # in-/dekrementiere Kandidaten
    for partei in diskrepanz:
        tabelle.at[partei, "Sitze"] = tabelle.at[partei, "Sitze"] - vorzeichen

    # gebe Tabelle mit angepasster Sitzanzahl zurück
    return tabelle.drop(
        [zeile for zeile in tabelle.columns if zeile.startswith("Divisor")], axis=1
    )
