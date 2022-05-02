"""Dieses Modul stellt die Methoden der Sainte-Lague-Methode bereit"""
import inspect
import random
from typing import Callable

import pandas as pd

from sitzverteilung.rechner.divisor import sainte_lague_divisor

Sitzverteilungsrechner = Callable[[pd.DataFrame, int], tuple[pd.DataFrame, list]]


def sainte_lague_rangzahl(
    tabelle: pd.DataFrame, sitze: int
) -> tuple[pd.DataFrame, list]:
    """
    Nutze das Sainte-Laguë-Rangzahlverfahren zur Sitzberechnung

        :param int sitze: Anzahl zu verteilender Sitze
        :param pd.DataFrame tabelle: Dataframe mit Stimmenverteilung
        :return: Dataframe erweitert um Sitzverteilung, Liste für Verlosung
    """
    lose = []
    tabelle["Sitze"] = 0
    while tabelle["Sitze"].sum() < sitze:
        tabelle["Divisor"] = tabelle["Sitze"] + 0.5
        tabelle["Rangzahl"] = tabelle["Stimmen"] / tabelle["Divisor"]
        anzahl_gewinner = tabelle["Rangzahl"][
            tabelle["Rangzahl"] == tabelle["Rangzahl"].max()
        ].count()
        if anzahl_gewinner > (sitze - tabelle["Sitze"].sum()):
            lose = list(tabelle[tabelle["Rangzahl"] == tabelle["Rangzahl"].max()].index)
            break
        gewinner = tabelle["Rangzahl"].idxmax()
        tabelle.at[gewinner, "Sitze"] += 1
    return tabelle.drop(["Divisor", "Rangzahl"], axis=1), lose


def losentscheid(dataframe: pd.DataFrame, lose: list, sitze: int) -> pd.DataFrame:
    """
    Führe einen Losentscheid durch. Die Sitze können mit pseudo-Zufall (Option 0) oder mit externen Methode zugelost
    werden. Die pandas Tabelle wird mit den zusätzlichen Sitzen zurückgegeben.
        :param dataframe: Tabelle mit Sitzverteilung vor der Verlosung
        :param lose: Liste mit Losen für den Lostopf
        :param sitze: Soll-Anzahl Sitze (implizit Anzahl Lose)
        :return: Tabelle mit Sitzverteilung nach der Verlosung
    """
    dataframe = dataframe.copy()
    liste = []
    anzahl_lose = int(sitze - dataframe["Sitze"].sum())
    while len(liste) < anzahl_lose:
        lose = pd.Series(["Zufall"] + lose)
        los = input(f"Lose zwischen:\n{lose}\n")
        try:
            los = int(los)
        except ValueError:
            print("Wähle eine Zahl")
            continue
        if los == 0:
            liste.extend(
                random.sample(list(lose.values[1:]), k=anzahl_lose - len(liste))
            )
        else:
            try:
                liste.append(lose[los])
                lose = lose.drop(los)
            except KeyError:
                print(f"{los} ist keine wählbare Option")
    print(f"Lose an {liste}")
    for partei in liste:
        dataframe.at[partei, "Sitze"] += 1
    return dataframe


def SainteLague(  # pylint: disable=invalid-name
    methode: str = "divisor",
) -> Sitzverteilungsrechner:
    """
    Fabrik um die passende Sainte-Lague-Methode zu erhalten
        :param methode: welcher Algorithmus verwendet wird. Entweder "divisor" oder "rangzahl"
        :return: gewünschte Sainte-Lague-Methode
    """
    methoden: dict = {
        "divisor": sainte_lague_divisor,
        "rangzahl": sainte_lague_rangzahl,
    }
    if methode not in methoden:
        raise ValueError(
            f"{methode} ist keine gültige Methode für {inspect.stack()[0][3]}, "
            f"wähle aus {list(methoden.keys())}"
        )
    return methoden.get(methode)
