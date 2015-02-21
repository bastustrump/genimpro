# GenImpro

##Analysemethodik

1. Erkennung von Einsätzen (*onset detection*)
2. Merkmalsextraktion (*feature extraction*)
3. [Vergleich der Merkmalsvektoren verschiedener Beispielklänge](http://nbviewer.ipython.org/github/bastustrump/genimpro/blob/master/notebooks/compare%20feature%20plots.ipynb)
4. Gruppierung in Klangfolgen
  1. [Nähe](http://nbviewer.ipython.org/github/bastustrump/genimpro/blob/master/notebooks/grouping%201.ipynb)
  2. Ähnlichkeit
5. Phänotyp-Definition
6. Genotyp-Definition
7. Strukturelle Analyse der Genotypen
  1. Data-Mining
  2. ...

Quellenverzeichnis

##Voraussetzungen

Die Beschreibung der Analysemethodik besteht aus mehreren IPython notebooks. [IPython](http://ipython.org/) ist eine interaktive, Browser-basierte Shell der Programmiersprache [Python](http://www.python.org/) mit vielfältigen Möglichkeiten zur Datenvisualisierung.

#####Python Libraries

Die folgenden Erweiterungen zu Python werden zum Ausführen der Skripte benötigt:

- [Numpy](http://www.numpy.org/): Array- und Statistikfunktionen
- [Scipy](http://scipy.org): Weitere Funktionen zur Signalverarbeitung
- SQLite3: Datenbank zur Metadatenverwaltung
- [aubio](http://aubio.org): Onset detection
- [essentia](http://essentia.upf.edu): Klanganalyse, MIR

##Danksagung
Das Forschungsprojekt "Genetische Improvisation" an der Hochschule für Musik Nürnberg wird gefördert durch die [STAEDTLER Stiftung](http://www.staedtler.de/de/unternehmen/staedtler-stiftung/)
