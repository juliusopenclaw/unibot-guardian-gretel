# UniBot RegulatoryProfileV1

Status: **Vorbereitung für menschliche Prüfung; nicht freigegeben**.

Dieses Profil ist die kompakte, versionierte Übersicht für Prüfungsamt,
Inklusionsbüro, Datenschutz, IT/SZI, Lehreinheit und
Bachelorarbeitsbetreuung. Es ist kein Rechtsgutachten, keine
Datenschutzfreigabe und keine Erlaubnis für einen Prüfungseinsatz.

## Zweck

UniBot soll zunächst eine lokale Lern- und Übungshilfe für Python-Notebooks
sein. Die deterministische Tutorlogik fragt nach dem eigenen nächsten Schritt,
ordnet Fehler ein und verweist auf geprüfte Quellen. Sie benotet nicht,
überwacht nicht und erkennt keine KI-Nutzung.

Der aktuelle Einsatzstatus bleibt `not_cleared`. Konkrete Modul-, Fakultäts- und
Prüfungsordnungen haben Vorrang.

Für eine universitäre Bereitstellung wird der konkrete Zweck mit dem KI-Office
beziehungsweise CIO-Board und einer namentlich benannten fachverantwortlichen
Person geklärt. Diese Vorlage nimmt keine Positivlistenaufnahme vor und ersetzt
keine menschliche Letztverantwortung.

Im lokalen Übungsbetrieb unterstützt der aktuelle Mantel A0 bis A4 nach einem
unveränderlichen Lernvertrag. Ein möglicher kontrollierter Prüfungstrack ist
davon getrennt, bleibt auf einen möglichen A0-A2-Rahmen begrenzt und benötigt
vorher eine schriftliche Entscheidung der zuständigen Stellen.

## Datenfluss

- Zelltext und eigener Versuch werden nur flüchtig lokal verarbeitet.
- Persistiert werden ausschließlich Vertragshash, Hilfestufe, Quellen-IDs,
  Ereignis-/Versuchshashes, Zeitpunkte sowie Kosten- und Löschmetadaten.
- Zelltext, Versuchstext, Tutortranskript, Notebook-Token, Gesundheitsdaten,
  private Kursunterlagen und lokale Pfade gehören nicht in GitHub, iCloud oder
  einen Modellprovider.
- Der lokale Tutor arbeitet ohne Provider. GLM bleibt für die Entwicklung
  separat begrenzt und erhält keinen Lernenden- oder Notebookinhalt.
- Der Chrome-Mantel nimmt eine allowlistete öffentliche HTTPS-Quelle oder eine
  lokale `.ipynb`-Datei an. Bei der lokalen Auswahl wird kein Dateipfad an den
  Companion weitergegeben; gespeichert wird nur die bereinigte lokale
  Übungskopie. Für die institutionelle Demonstration wird ausschließlich ein
  öffentliches synthetisches Notebook verwendet.
- Ein Export ist freiwillig und wird vorab als Vorschau angezeigt. Er enthält
  nur pseudonyme Metadaten und Quellen-IDs.

Aufbewahrung, Zugriff, Löschbeleg und ein möglicher Pilot mit echten Personen
bleiben offene Entscheidungen der zuständigen menschlichen Stellen.

## Inklusion und Barrierefreiheit

Der Mantel soll vollständig per Tastatur bedienbar sein, sichtbaren Fokus,
Statusansagen, ausreichenden Kontrast, 200-Prozent-Zoom und ein schmales
Sidepanel ab 280 Pixeln unterstützen. Eine manuelle Zellwahl bleibt verfügbar,
wenn die Erkennung unsicher ist. Barrierefreie Unterstützung bleibt
kostenneutral und wird weder in eine Note noch in eine automatische
Nachteilsausgleich-Entscheidung umgerechnet.

Die öffentliche Browserprüfung belegt derzeit semantische Statusbereiche,
Tab-/Panel-Beziehungen, Pfeiltasten-/Home-/Ende-Navigation, sichtbaren
Tastaturfokus und einen schmalen Mantel ohne horizontalen Überlauf. Das ist
technische Evidenz für die weitere Prüfung, aber keine WCAG-Zertifizierung und
keine Entscheidung des Servicezentrums Inklusion.

Der maschinenlesbare Review-Vertrag `AccessibilityReviewV1` trennt acht
reproduzierbare Prüfungen von der menschlichen Konformitätsentscheidung: reine
Tastaturbedienung, Screenreader-Status, 200-Prozent-Zoom und Reflow, Kontrast
und Fokus, unsichere Zellwahl, verständliche Sprache, Ausfall des Companions und
datensparsame Nicht-Offenlegung. Kritische Fehler blockieren den jeweiligen
Einsatzumfang. Die Source Cards `wcag-22`, `bgg-nrw-10` und `bitv-nrw` sind
technische beziehungsweise rechtliche Prüfgrundlagen, keine automatische
Freigabe.

Das Inklusionsbüro entscheidet, welche Unterstützung im jeweiligen Modul und
Prüfungsformat zulässig ist. UniBot ersetzt keine individuelle Entscheidung.

## Ausgeschlossene Funktionen

- automatische Benotung, Zulassungs- oder Eignungsentscheidungen
- Proctoring, Überwachung oder Täuschungsüberwachung
- KI-Erkennung als Beweis oder Disziplinarmaßnahme
- automatische Nachteilsausgleich- oder sonstige Unterstützungsentscheidungen
- Ausgabe einer fertigen Lösung oder eines Endergebnisses
- Freigabe eines Prüfungseinsatzes oder eine rechtliche Freigabe

## Menschliche Prüffragen

Vor einem institutionellen Pilot müssen Zweck, Datenarten, Aufbewahrung,
Zugriffsrollen, Löschung, Notfallweg, Hilfestufen, Barrierefreiheit und die
Trennung von Übung und Prüfung schriftlich bewertet werden. Ein echter
Prüfungstrack benötigt zusätzlich eine separate Entscheidung der zuständigen
Prüfungs- und Hochschulstellen sowie IT- und Datenschutzprüfung.

## Quellenbasis

Die maschinenlesbare Version bindet die offiziellen Source Cards
`uoc-ki-policy-2026`, `uoc-ki-pruefungsrecht`,
`uoc-medfak-ki-doku-2026`, `uoc-medfak-ki-lehre-2026`, `uoc-ki-lehre`, `uoc-hilfsmittel`,
`uoc-nachteilsausgleich`, `uoc-szi-klausurunterstuetzung-2026`,
`uoc-szi-inclusive-teaching-2026`, `uoc-szi-wegweiser-2026`, `gdpr-2016-679`, `dsk-ai-privacy-2024`,
`eu-ai-act-2024`, `hg-nrw-64`, `dfg-gwp` und `jupyter-ai`.
Zusätzlich bindet der Accessibility-Review `wcag-22`, `bgg-nrw-10` und
`bitv-nrw`.

Wichtige Referenzen:

- [KI-Richtlinie der Universität zu Köln, AM 2/2026](https://am.uni-koeln.de/e45267/data/records54900/AM_2026-02_KI_RL_ger.pdf)
- [Universität zu Köln: KI und Prüfungsrecht](https://verwaltung.uni-koeln.de/stabsstelle02.1/content/allgemeine_informationen/aktuelles/kuenstliche_intelligenz_und_pruefungsrecht/index_ger.html)
- [Medizinische Fakultät: KI-Dokumentationsrichtlinie](https://medfak.uni-koeln.de/sites/MedFakDekanat/Forschung/Promotion/KI-Richtlinie_MedFak.pdf)
- [Medizinische Fakultät: KI im Studium](https://medfak.uni-koeln.de/studium-lehre/ueberblick/ki-in-der-lehre)
- [Servicezentrum Inklusion: Nachteilsausgleich](https://inklusion.uni-koeln.de/informationen/nachteilsausgleich/index_ger.html)
- [Servicezentrum Inklusion: Klausurunterstützung](https://inklusion.uni-koeln.de/service/klausurunterstuetzung/index_ger.html)
- [Servicezentrum Inklusion: Wegweiser für Studierende mit Behinderung und chronischer Erkrankung](https://inklusion.uni-koeln.de/wegweiser/index_ger.html)
- [Servicezentrum Inklusion: inklusive Lehre und Barrierefreiheit](https://inklusion.uni-koeln.de/informationen/inklusive_lehre/schritte_inklusive_lehre/index_ger.html)
- [EU-KI-Verordnung 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng)

Diese Quellen begründen keine automatische Einstufung des konkreten Produkts.
Die zuständigen Menschen entscheiden über den tatsächlichen institutionellen
Anwendungsfall.

## Präsentation starten

Für eine Review-Sitzung erzeugt der lokale CLI-Weg ein kompaktes Paket aus
RegulatoryProfileV1, Clearance-Board, Readiness und Release-Runbook:

```text
unibot institution profile
unibot institution presentation
unibot institution presentation --markdown
unibot institution decision-template --markdown
unibot institution bundle --output ./unibot-institution-review
```

Der Bundle-Befehl schreibt `institutional-presentation.json`,
`institutional-presentation.md`, ein leeres
`institutional-review-decision-template.md` und ein Hash-Manifest in ein owner-lesbares
Verzeichnis. Er schreibt nur bei grüner Public-Safety-Prüfung und enthält keine
Notebook-, Personen- oder lokalen Pfadinhalte. Das Paket darf nur mit einem
öffentlichen synthetischen Notebook demonstriert werden. Es ist zur
menschlichen Prüfung vorbereitet, aber keine automatische Veröffentlichungs-,
Prüfungs- oder Inklusionsfreigabe.

Die reproduzierbare öffentliche Demo-Fixture liegt unter
`fixtures/public/synthetic_python_practice.ipynb`. Sie enthält nur eine
synthetische Python-Aufgabe ohne Lernenden-, Kurs-, Gesundheits- oder
Prüfungsdaten.

Das Ergebnisformular sieht ausschließlich kontrollierte Ergebnis-, Rollen-,
Bedingungen-, Fragen- und Evidenz-IDs sowie Hashes vor. Gesprächsnotizen,
Namen, Gesundheits- oder Nachteilsausgleichdaten und Notebookinhalte werden
nicht als öffentliche Entscheidungsdaten vorgesehen.

## Transparente Autorenschaft

Implementierung und Dokumentation: **Gretel / Codex**.

GLM-5.2: in dieser geparkten Etappe kein Beitrag; bei späterer Aktivierung nur
Vorschlag und Gegenprüfung mit öffentlichen, bereinigten Projektdateien.

Julius: menschlicher Projektverantwortlicher sowie alleiniger Freigeber für
Zusammenführung und Veröffentlichung.
