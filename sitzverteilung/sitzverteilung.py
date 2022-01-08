import decimal
import random

import numpy as np
import pandas as pd

from sitzverteilung.hilfsmittel import load_yaml, nice_round, remove_exponent

METHODE_STRING = 'divisor'


def sainte_lague_rangzahl(sitze, dataframe):
    lose = []
    dataframe['Sitze'] = 0
    while dataframe['Sitze'].sum() < sitze:
        dataframe['Divisor'] = dataframe['Sitze'] + 0.5
        dataframe['Rangzahl'] = dataframe['Stimmen'] / dataframe['Divisor']
        anzahl_gewinner = dataframe['Rangzahl'][dataframe['Rangzahl'] == dataframe['Rangzahl'].max()].count()
        if anzahl_gewinner > (sitze - dataframe['Sitze'].sum()):
            lose = list(dataframe[dataframe['Rangzahl'] == dataframe['Rangzahl'].max()].index)
            break
        gewinner = dataframe['Rangzahl'].idxmax()
        dataframe.at[gewinner, 'Sitze'] += 1
    return dataframe.drop(['Divisor', 'Rangzahl'], axis=1), lose


def sainte_lague_divisor_iterativ(sitze, dataframe):
    lose = []
    divisor = dataframe['Stimmen'].sum() // sitze
    dataframe['Sitze'] = np.rint(dataframe['Stimmen'] / divisor)
    while dataframe['Sitze'].sum() < sitze:
        divisor -= 0.1
        dataframe['Sitze'] = np.rint(dataframe['Stimmen'] / divisor)
        # print('zu wenige Sitze, reduziere Divisor')
        if dataframe['Sitze'].sum() > sitze:
            dataframe['Sitze'], lose = losverfahren(dataframe, divisor + 1, divisor)
    while dataframe['Sitze'].sum() > sitze:
        divisor += 0.1
        dataframe['Sitze'] = np.rint(dataframe['Stimmen'] / divisor)
        if dataframe['Sitze'].sum() < sitze:
            dataframe['Sitze'], lose = losverfahren(dataframe, divisor, divisor - 1)
        # print('zu viele Sitze, erhöhe Divisor')
    return dataframe.astype({'Sitze': 'int64'}), lose


def sainte_lague_divisor(sitze, tabelle):
    # initiiere decimal-modul und übertrage Zahlen in decimal. Decimal ist hier notwendig für exaktes runden.
    decimal.setcontext(decimal.Context(rounding=decimal.ROUND_HALF_UP))
    tabelle = tabelle.applymap(decimal.Decimal)
    sitze = decimal.Decimal(str(sitze))
    halb = decimal.Decimal('0.5')

    # bestimme vorläufigen Divisor und ermittle die entsprechende Sitzanzahl
    divisor = tabelle['Stimmen'].sum() / sitze
    tabelle['Sitze'] = (tabelle['Stimmen'] / divisor).apply(lambda x: x.to_integral_value())
    erste_sitzverteilung = tabelle['Sitze'].copy()

    tabelle['höherer Divisor'] = (tabelle['Stimmen'] / (tabelle['Sitze'] - halb)).replace(0, decimal.Decimal('nan'))
    tabelle['niedriger Divisor'] = (tabelle['Stimmen'] / (tabelle['Sitze'] + halb)).replace(0, decimal.Decimal('nan'))

    # bestimme Divisorgrenzen
    differenz = tabelle['Sitze'].sum() - sitze
    if differenz > 0:
        index = tabelle['höherer Divisor'].drop_duplicates().astype(float).nsmallest(int(differenz)).idxmax()
        untergrenze = tabelle.at[index, 'höherer Divisor']
        index = tabelle['höherer Divisor'].drop_duplicates().astype(float).nsmallest(int(differenz + 1)).idxmax()
        obergrenze = tabelle.at[index, 'höherer Divisor']
    elif differenz < 0:
        index = tabelle['niedriger Divisor'].drop_duplicates().astype(float).nlargest(int(1 - differenz)).idxmin()
        untergrenze = tabelle.at[index, 'niedriger Divisor']
        index = tabelle['niedriger Divisor'].drop_duplicates().astype(float).nlargest(int(-differenz)).idxmin()
        obergrenze = tabelle.at[index, 'niedriger Divisor']
    else:  # difference == 0
        untergrenze = tabelle['höherer Divisor'].min()
        obergrenze = tabelle['niedriger Divisor'].max()
    divisor = decimal.Decimal(nice_round(remove_exponent(untergrenze), remove_exponent(obergrenze)))

    # endgültige Sitzberechnung
    tabelle['Sitze'] = (tabelle['Stimmen'] / divisor).apply(lambda x: x.to_integral_value())

    # überprüfe Sitzanzahl erneut
    differenz = tabelle['Sitze'].sum() - sitze
    lose = list(erste_sitzverteilung[(erste_sitzverteilung != tabelle['Sitze'])].index) if not differenz == 0 else []

    return tabelle.drop(['höherer Divisor', 'niedriger Divisor'], axis=1).astype('int64'), lose


def losverfahren(dataframe, divisor_max, divisor_min):
    series_max = np.rint(dataframe['Stimmen'] / divisor_min)
    series_min = np.rint(dataframe['Stimmen'] / divisor_max)
    return series_min, list(series_min.compare(series_max).index)


def sainte_lague(sitze, stimmen, methode='divisor'):
    stimmen = stimmen.copy()
    methode.lower()
    if methode == 'divisor alt':
        dataframe, lose = sainte_lague_divisor_iterativ(sitze, stimmen)
    elif methode == 'divisor':
        dataframe, lose = sainte_lague_divisor(sitze, stimmen)
    elif methode == 'rangzahl':
        dataframe, lose = sainte_lague_rangzahl(sitze, stimmen)
    elif methode == 'debug':
        dataframe, lose = sainte_lague_divisor(sitze, stimmen)
        dataframe2, lose2 = sainte_lague_rangzahl(sitze, stimmen)
        if not (dataframe.equals(dataframe2) and lose == lose2):
            print(dataframe.compare(dataframe2))
            raise Exception("Fehler in der Berechnung nach sainte-lague")
    else:
        raise ValueError(f"Methode {methode} nicht existent. Mögliche Optionen sind 'divisor' und 'rangzahl'")
    if not lose == []:
        liste = []
        while len(liste) < int(sitze - dataframe['Sitze'].sum()):
            lose = pd.Series(['Zufall'] + lose)
            los = input(f'Lose zwischen:\n{lose}\n')
            try:
                los = int(los)
            except ValueError:
                print('Wähle eine Zahl')
                continue
            if los == 0:
                liste.extend(random.sample(list(lose.values[1:]), k=int(sitze - dataframe['Sitze'].sum())))
            else:
                try:
                    liste.append(lose[los])
                    lose = lose.drop(los)
                except KeyError:
                    print(f'{los} ist keine wählbare Option')
        print(f'Lose an {liste}')
        for partei in liste:
            dataframe.at[partei, 'Sitze'] += 1
    return dataframe


def sitzverteilung(pfad):
    # Lade Daten aus Dateien
    settings_yaml = load_yaml(pfad / 'Einstellungen.yaml')
    laender_yaml = load_yaml(pfad / 'Länder.yaml')
    laender = pd.DataFrame(index=laender_yaml.keys(), data={'Stimmen': laender_yaml.values()})
    erststimmen = {key: pd.DataFrame(value) for key, value in load_yaml(pfad / 'Erststimme.yaml').items()}
    zweitstimmen = pd.DataFrame(load_yaml(pfad / 'Zweitstimme.yaml'))

    # Setze Variablen aus Einstellungen
    sitze_geplant = settings_yaml['Sitze']  # erforderlich, kein default
    try:
        huerde = settings_yaml['Hürde']
    except KeyError:
        huerde = {}
    try:
        mindestsitze_methode = settings_yaml['Mindestsitze']
    except KeyError:
        mindestsitze_methode = 'Keine'
    try:
        ueberhang = settings_yaml['Überhang']
    except KeyError:
        ueberhang = 0

    # Überprüfe, welche Parteien bei der Sitzverteilung berücksichtigt werden
    zulassung = pd.DataFrame()

    stimmen = zweitstimmen.sum(axis=1)
    zulassung['Prozent'] = 100 * stimmen / stimmen.sum()
    # Stelle fest, ob eine Partei über 50 % der Stimmen erhalten hat (später wichtig)
    try:
        mehrheitssieger = zulassung[zulassung['Prozent'] > 50].index[0]
    except IndexError:
        mehrheitssieger = None

    # Zähle die Direktmandate der Parteien
    direktmandate = pd.DataFrame(index=zweitstimmen.index)
    for land, tabelle_land in erststimmen.items():
        direktmandate[land] = 0
        for kreis, stimmen in tabelle_land.items():
            if not stimmen.max() == 0:
                sieger = stimmen.idxmax()
                # sieger = 'DIE LINKE'
                direktmandate.at[sieger, land] += 1
    zulassung['Direkt'] = direktmandate.sum(axis=1)

    # Initialisiere Spalte für mögliche Ausnahmen von der Hürde (z.B. nationale Minderheiten)
    zulassung['Ausnahmen'] = False

    # Prüfung, welche Kriterien erfüllt sind
    if 'Prozent' in huerde.keys():
        zulassung['Prozent'] = zulassung['Prozent'] >= huerde['Prozent']
    else:
        zulassung['Prozent'] = False
    if 'Direkt' in huerde.keys():
        zulassung['Direkt'] = zulassung['Direkt'] >= huerde['Direkt']
    else:
        zulassung['Direkt'] = False
    if 'Ausnahmen' in huerde.keys():
        for partei in huerde['Ausnahmen']:
            zulassung.at[partei, 'Ausnahmen'] = True
    zweitstimmen = zweitstimmen.loc[zulassung['Prozent'] | zulassung['Direkt'] | zulassung['Ausnahmen']]

    # Überprüfe, ob es "unabhängige" Wahlkreissieger gibt
    unabhaengige = direktmandate.drop(zweitstimmen.index).sum(axis=1)
    unabhaengige = unabhaengige[unabhaengige > 0]
    gesamtsitze = sitze_geplant - unabhaengige.sum()

    # Verteilung der Sitze auf die Länder
    print('Verteile Sitze auf Länder')
    laender = sainte_lague(gesamtsitze, laender, methode=METHODE_STRING)

    # erste Unterverteilung auf die Landeslisten
    erste_unterverteilung = pd.DataFrame()
    for land in laender_yaml.keys():
        print(f'erste Unterverteilung in {land}')
        tabelle = pd.DataFrame({'Stimmen': zweitstimmen[land]})
        erste_unterverteilung[land] = sainte_lague(laender.at[land, 'Sitze'], tabelle, methode=METHODE_STRING)['Sitze']

    # Bestimmung der Mindestsitze
    if mindestsitze_methode == 'Keine':
        mindestsitze = direktmandate
    elif mindestsitze_methode == 'Pur':
        mindestsitze = erste_unterverteilung.where(erste_unterverteilung > direktmandate.loc[zweitstimmen.index],
                                                   direktmandate)
    elif mindestsitze_methode == 'Mittelwert':
        mittelwert = pd.concat([direktmandate.loc[zweitstimmen.index], erste_unterverteilung])
        mittelwert = mittelwert.groupby(level=0, sort=False).mean().apply(np.floor).astype('int64')
        mindestsitze = mittelwert.where(mittelwert > direktmandate.loc[zweitstimmen.index], direktmandate)
    else:
        raise ValueError(f'Methode {mindestsitze_methode} für Mindestsitze nicht bekannt')
    mindestsitze = mindestsitze.sum(axis=1)

    # Verteilung der gesamtsitzanzahl
    print('Oberverteilung')
    stimmen = pd.DataFrame({'Stimmen': zweitstimmen.sum(axis=1)})
    stimmen = sainte_lague(gesamtsitze, stimmen, methode=METHODE_STRING)
    differenz = mindestsitze - stimmen['Sitze']
    differenz = differenz.where(differenz > 0, 0)
    print('Überhangsmandate\n', differenz)
    while differenz.sum() > ueberhang:
        gesamtsitze += differenz.sum() - ueberhang
        print(f'erhöhe Sitzanzahl auf {gesamtsitze}')
        stimmen = sainte_lague(gesamtsitze, stimmen, methode=METHODE_STRING)
        differenz = mindestsitze - stimmen['Sitze']
        differenz = differenz.where(differenz > 0, 0)
    stimmen['Sitze'] += differenz
    gesamtsitze += differenz.sum()

    # Wenn eine Partei über 50 % der Stimmen gewinnt, stehen ihr über 50 % der Sitze zu
    if mehrheitssieger is not None:
        while stimmen.at[mehrheitssieger, 'Sitze'] * 2 <= gesamtsitze:
            print(f'erhöhe Sitze von {mehrheitssieger} auf über 50%')
            stimmen.at[mehrheitssieger, 'Sitze'] += 1
            gesamtsitze += 1
    print('Unausgeglichene Überhangsmandate\n', differenz)
    stimmen = stimmen.append(unabhaengige[unabhaengige > 0].to_frame(name='Sitze')).fillna(-1).astype('int64')
    gesamtsitze += unabhaengige.sum()
    print('Gesamtanzahl Sitze: ', gesamtsitze)
    print('Sitzverteilung\n', stimmen)
