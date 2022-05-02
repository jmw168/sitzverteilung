"""Dieses Modul stellt verschiedene Hilfsfunktionen für die Sitzverteilungsberechnung zur Verfügung"""
import decimal
from pathlib import Path

import yaml


def remove_exponent(zahl):
    """Wandle eine Dezimalzahl mit Exponent in eine Dezimalzahl ohne Exponent um

    :param zahl: Umzuwandelnde Zahl
    :type zahl: decimal.Decimal
    :return: Umgewandelte Zahl
    :rtype: decimal.Decimal
    """
    return (
        zahl.quantize(decimal.Decimal(1))
        if zahl == zahl.to_integral()
        else zahl.normalize()
    )


def nice_round(first, second) -> str:
    """
    Gibt die "schönste" Zahl die zwischen den beiden Parametern liegt, zurück

    :param first: untere Grenze
    :param second: obere Grenze
    :return: "schöne" Zahl als string
    :rtype: str
    """
    # check if arguments are floats and bring them in correct order. just return the value if both are identical
    if not isinstance(first, (float, int, decimal.Decimal)) or not isinstance(
        second, (float, int, decimal.Decimal)
    ):
        raise TypeError(
            "nice_round() arguments must be convertable to floats"
        ) from None
    if first == second:
        return str(first)
    first, second = sorted((first, second))

    # make them strings and compare dimensions
    first = str(first)
    second = str(second)
    first = first if "." in first else f"{first}."
    second = second if "." in second else f"{second}."
    pre_decimal = len(first.split(".")[0]) - len(second.split(".")[0])
    post_decimal = len(first.split(".")[1]) - len(second.split(".")[1])

    if pre_decimal < 0:
        first = "".join(["0" * abs(pre_decimal), first])
    elif pre_decimal > 0:
        second = "".join(["0" * abs(pre_decimal), second])

    if post_decimal < 0:
        first = "".join([first, "0" * abs(post_decimal)])
    elif pre_decimal > 0:
        second = "".join([second, "0" * abs(post_decimal)])

    # finally, compare numbers digit-wise
    resulting_number = ""
    for first_digit, second_digit in zip(first, second):
        if first_digit == second_digit:
            resulting_number = "".join([resulting_number, first_digit])
        else:
            for nice_digit in [5, 8, 6, 4, 2, 9, 7, 5, 3, 1, 0]:
                if nice_digit in range(int(first_digit) + 1, int(second_digit) + 1):
                    resulting_number = "".join([resulting_number, str(nice_digit)])
                    if "." not in resulting_number:
                        adding_zeros = len(first.split(".")[0]) - len(resulting_number)
                        resulting_number = "".join(
                            [resulting_number, "0" * adding_zeros]
                        )
                    break
            break
    return resulting_number


def load_yaml(filename: str | Path):
    """
    Wrapper um .yaml Datei zu laden

    :param filename: Dateiname
    :return: Daten aus Datei
    """
    with open(filename, "r", encoding="utf8") as file:
        yaml_data = yaml.load(file, Loader=yaml.SafeLoader)
    return yaml_data


def sort_two(eins: int, zwei: int) -> [int, int]:
    """
    Hilfsfunktion: Sortiere zwei Ganzzahlen
    :param eins: erste Ganzzahl
    :param zwei: zweite Ganzzahl
    :return: [min, max]
    """
    list_ = [eins, zwei]
    list_.sort()
    return list_
