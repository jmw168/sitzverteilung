# sitzverteilung
Dieses kleine Programm dient der Sitzverteilungsberechnung nach Art des deutschen Bundestages.
Da es sich primär an eine deutsche Zielgruppe, teilweise ohne umfassende Englischkenntnisse richtet, ist es bewusst auf Deutsch gehalten.
Eine Internationalisierung/ internationale Lokalisierung könnte in Zukunft irgendwann angestrebt werden.

Um das Programm benutzen zu können, ist eine funktionierende Python-Umgebung erforderlich.
Erforderliche Pakete finden sich in requirements.txt.
Eine verfügbare Online-Anwendung ohne das Erfordernis von Python-Kenntnissen soll demnächst angeboten werden.

Um das Programm im vollen Umfang zu nutzen, kann man es ganz einfach ausführen: 
`python sitzverteilungsrechner.py`
Die erforderlichen Daten müssen in den Dateien
``Einstellungen.yaml Direkandidaten.yaml Listenkandidaten.yaml Erststimme.yaml Zweitstimme.yaml`` vorliegen.
Weitere Informationen zu den Dateien folgen unten.

Um die enthaltenen Beispiele zu nutzen, kann man auch problemlos die Kommandozeilenoption `-b` benutzen.
Mit `python sitzverteilungsrechner.py -b bundestag 2021` wird das Beispiel der Bundestagswahl 2021 ausgeführt.
Zusätzlich zur reinen Sitzverteilungsberechnung werden hier die Daten vom Bundeswahlleiter heruntergeladen und die
Eingabedateien ggf. aktualisiert.

Beispiele aus der Politiksimulation vBundesrepublik sind über `python sitzverteilungsrechner.py -b vb 9` verfügbar, wobei die Zahl durch die entsprechende Wahl in der Simulation ersetzt werden muss.
Derzeit ist nur die 9. Wahl verfügbar, wer zusätzliche Beispiele einpflegen mag, darf dies gerne tun. 

## Die Eingabedateien
### Einstellungen.yaml

`Sitze:` Anzahl der Sitze (als Ganzzahl)

`Hürde:` Alle informationen zur Hürde, die überschritten werden muss, um bei der Sitzverteilung berücksichtigt zu
werden. Mögliche Optionen sind:
- `Prozent:` Prozenthürde an Zweitstimmen in Prozent
- `Direkt:` Anzahl an Direktmandaten, die zu einer Zulassung führen
- `Ausnahmen:` Auflistung von Parteien, für die eine Ausnahme existiert, zum Beispiel der SSW als Partei einer nationalen Minderheit 

`Mindestsitze:` Wie sich die Mindestsitzanzahl für die 2. Oberverteilung ergibt. Mögliche Optionen sind:
- `Keine` Die Sitzverteilung aus der Unterverteilung wird ignoriert, die Mindestsitze ergibt sich aus den Direktmandaten (zum Beispiel in Fällen ohne Unterverteilung wie der Simulation vBundesrepublik)
- `Pur` Die Mindessitzanzahl ergibt sich als Maximum aus Direktmandaten und Sitzen der 1. Unterverteilung für jedes Bundesland (Bundestagswahlrecht bis 2020)
- `Mittelwert` Die Mindessitzanzahl ergibt sich als Maximum aus Direktmandaten und dem aufgerundeten Mittelwert aus den Sitzen der 1. Unterverteilung und den Direktmandaten für jedes Bundesland (teilweiser Ausgleich zwischen Bundesländern, Bundestagswahlrecht ab 2020)

`Überhang:` Anzahl an Überhangmandaten, die nicht ausgeglichen werden

̀̀̀`Obergrenze:` Maximale Anzahl an Sitzen