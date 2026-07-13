# UniBot Guardian

## Ein GLM-gestuetzter sokratischer Integritaetsmantel fuer Python-Notebooks

Status: oeffentlicher wissenschaftlicher Entwurf auf Bachelorarbeitsniveau

Implementierung und Dokumentation: Gretel, KI-Agent

Vorschlags- und Gegenpruefungsmodell: Z.AI GLM-5.2

Menschliche Projekt-, Merge- und Abgabeverantwortung: Julius oder eine andere
ausdruecklich benannte menschliche Person

Institutioneller Status: keine rechtswirksame Hochschulabgabe und keine
Pruefungsfreigabe

## Abstract

Generative Sprachmodelle koennen Programmierlernende beim Verstehen von
Fehlermeldungen, Datenstrukturen und Analyseablaeufen unterstuetzen. Dieselben
Systeme koennen jedoch vollstaendige Loesungen erzeugen, unbeabsichtigt private
Informationen verarbeiten und bei unkritischer Verwendung die Eigenleistung
verdecken. Diese Arbeit beschreibt UniBot Guardian, eine oeffentlich
pruefbare sokratische Integritaetsschicht fuer Python- und Notebook-Uebungen.
Das System begrenzt Hilfe im Lernbetrieb auf die Stufen A0 bis A4, prueft fremde
Modellausgaben, erfasst den eigenen naechsten Lernschritt und speichert nur
minimierte Metadaten. Eine Browser-Erweiterung verbindet Colab- und
Jupyter-Oberflaechen mit einer gekoppelten lokalen API. Ein sicherer
Notebook-Eingang entfernt Ausgaben, prueft Format, Herkunft und Datenschutz
und friert das Ergebnis mit kryptographischen Hashes ein.

Die Entwicklung wird transparent Gretel, einem KI-Agenten, zugeordnet.
GLM-5.2 darf ausschliesslich bereinigte oeffentliche Projektteile fuer
Vorschlaege und Gegenpruefungen erhalten. Das Modell kann weder Dateien
schreiben noch GitHub-Aenderungen zusammenfuehren. Die Evaluation verwendet
180 fest versionierte synthetische Szenarien in sechs Kategorien. Ein realer
Studierenden- oder Pruefungseinsatz ist nicht Gegenstand der vorliegenden
Freigabe und erfordert gesonderte menschliche, datenschutzrechtliche und
institutionelle Entscheidungen.

## 1. Einleitung

Python-Notebooks verbinden Text, Code, Daten und Ergebnisse in einer
interaktiven Arbeitsumgebung. Diese Offenheit ist didaktisch wertvoll, macht
aber die Grenze zwischen Hilfe und uebernommener Loesung schwer sichtbar.
Ein allgemeiner Chatbot beantwortet oft genau die Frage, die Lernende selbst
bearbeiten sollten. Ein reines Verbot ignoriert dagegen legitime
Barrierefreiheit, Orientierung und konzeptuelle Rueckfragen.

UniBot verfolgt deshalb keine Erkennungs- oder Ueberwachungsstrategie. Es soll
Hilfe so umformen, dass der naechste kognitive Schritt beim Lernenden bleibt.
Die zentrale Forschungsfrage lautet:

> Wie kann eine oeffentliche, quellengebundene KI-Praxisschicht Lernende beim
> Programmieren unterstuetzen, ohne ihre Eigenleistung zu ersetzen, private
> Inhalte offenzulegen oder eine nicht vorhandene Pruefungsfreigabe zu
> behaupten?

Die Arbeit leistet vier Beitraege: eine explizite Hilfestufenpolitik, eine
lokale technische Sicherheitsgrenze, eine reproduzierbare synthetische
Evaluation und eine transparente Arbeitsteilung zwischen Gretel, GLM-5.2 und
menschlicher Verantwortung.

## 2. Forschungsstand und Quellenbasis

Die didaktische Grundlage bilden Arbeiten zu intelligenten Tutorsystemen und
formativer Rueckmeldung. Fuer UniBot ist nicht entscheidend, ob ein Modell
eine Aufgabe loesen kann, sondern ob die Interaktion einen eigenen naechsten
Schritt, eine begrenzte Rueckfrage und eine pruefbare Quelle sichtbar laesst.
Die Source Cards `vanlehn-2011` und `kulik-fletcher-2016` verankern diese
Einordnung in der Forschung zu Tutorsystemen.

Die Regeln guter wissenschaftlicher Praxis werden ueber `dfg-gwp`
eingebunden. Datenschutzanforderungen werden mit `gdpr-2016-679` und
`dsk-ai-privacy-2024` nachvollziehbar gemacht. Hochschul- und
pruefungsbezogene Grenzen verwenden unter anderem `uoc-ki-lehre`,
`uoc-ki-faq` und `uoc-hilfsmittel`. Die technischen Aussagen zu GLM werden
ueber `zai-glm-52`, `zai-glm-52-migration` und `zai-glm-pricing` belegt.

Source Cards sind keine automatische Wahrheitsgarantie. Sie speichern
Quellentyp, Autoritaet, Produktregel, Risiko und Pruefdatum. Ein Drift-Check
markiert veraltete oder fehlende Quellen. Normative und empirische Aussagen
bleiben dadurch unterscheidbar.

## 3. Anforderungen

Aus der Forschungsfrage folgen drei Goldene Regeln. Erstens darf UniBot keine
finale Loesung, keinen vollstaendigen Code-Fix, keine eingesetzten Werte und
keine abgabefertige Interpretation liefern. Zweitens duerfen private oder
sensible Inhalte nicht in oeffentliche Artefakte oder externe Modellkontexte
gelangen. Drittens muss die Eigenleistung durch eigenen Versuch, naechsten
Schritt, Reflexion und verwendete Hilfestufe sichtbar bleiben.

Funktional muss das System ein Notebook aufnehmen, eine aktive Zelle erfassen,
A0-A4-Hilfe erzeugen oder filtern, Hilfeereignisse minimiert protokollieren und
einen metadatenbasierten Rueckblick exportieren. Nichtfunktional gelten lokale
Standardbindung, explizite Kopplung, reproduzierbare Tests, begrenzte
Providerkosten und menschliche Freigabe fuer oeffentliche Zusammenfuehrungen.

Ausdruecklich ausgeschlossen sind Benotung, Proctoring, disziplinarische
KI-Erkennung, automatische Nachteilsausgleichsentscheidungen und eine durch
Software selbst erteilte Pruefungsfreigabe.

## 4. Methodik

Die Entwicklung folgt einem testgetriebenen Open-Science-Verfahren. Jede
Aenderung beginnt mit einem beobachtbaren Produkt- oder Forschungsproblem,
einer Hypothese und Akzeptanztests. Reine Beleg-, Hash- oder
Readiness-Verlaengerungen gelten nicht als Fortschritt, solange keine reale
Sicherheitspruefung fehlschlaegt.

Die Autonomie-v2-Schleife waehlt hoechstens einen Auftrag und vier Dateien pro
Lauf. Ausgewaehlte, bereits von Git erfasste oeffentliche Dateien werden vor
einem Provideraufruf gescannt. GLM-5.2 liefert ein streng strukturiertes
`GLMProposalV1`. Gretel implementiert lokal, fuehrt fokussierte Tests aus und
fordert anschliessend ein `GLMReviewV1` an. Laufdaten enthalten nur Hashes,
Modellversion, Tokenzahlen, Kosten und Status. Ein menschlicher Reviewer
entscheidet ueber das Zusammenfuehren.

Das monatliche Providerbudget betraegt 20 USD. Pro Lauf sind zwei Aufrufe,
60.000 Eingabe- und 8.192 Ausgabetokens erlaubt. Fehlt der Schluessel im
macOS-Schluesselbund, ist die Preisquelle veraltet, ist das Budget erreicht
oder scheitert der Datenschutzscan, endet der Lauf ohne Provideraufruf.

## 5. Systementwurf

UniBot besteht aus fuenf Schichten. Der Guardian klassifiziert loesungsartige,
datenschutzrelevante und manipulative Eingaben und erzeugt begrenzte
sokratische Hinweise. Die lokale API bindet nur an Loopback. Eine
achtstellige Einmalkopplung uebergibt ein starkes Sitzungstoken und bindet die
Browser-Origin. Wildcard-CORS ist ausgeschlossen.

Der Notebook-Eingang akzeptiert lokale Dateien oder oeffentliche HTTPS-Quellen
aus einer kleinen Domain-Allowlist. Interne, private, reservierte und
Loopback-Adressen werden nach DNS-Aufloesung blockiert. Weiterleitungen,
Dateigroesse und Medientyp sind begrenzt. Das Notebook muss dem nbformat-v4-
Schema entsprechen. Codeausgaben, Ausfuehrungszaehler, Anhaenge und nicht
benoetigte Metadaten werden entfernt. Rohquelle und Notebookinhalt sind fuer
den GLM-Kontext gesperrt.

Der Browser-Mantel besitzt nur die Arbeitsbereiche Sitzung, Hilfe und
Rueckblick. Getrennte Colab-, Jupyter- und manuelle Adapter lesen die aktive
Zelle, nicht den Ausgabecontainer, und lehnen unsichere Erkennung ab. A0 bis A4
reichen von der Orientierungsfrage bis zum unvollstaendigen Teilgeruest. Ein
hashgebundener Lernvertrag begrenzt feste oder adaptive Hilfe. Der Rueckblick
trennt Hilfenutzungsbudget, eigene Versuche und Quellen ohne Rohtranskript.

Die Erweiterung kommuniziert ueber einen origin-gebundenen Chrome Native Host
mit einem lokal installierbaren, ad-hoc-signierten Mac-Begleiter. Damit entfallen
der hartcodierte Port und das dauerhaft im Erweiterungsspeicher liegende Token.
Der gepaarte HTTP-Pfad bleibt als Entwickler- und Alpha-Kompatibilitaetsweg.

Das lokale Jupyter-Gateway startet eine gehashte Notebookkopie auf Loopback,
ohne Terminal und mit zufaelligem Sitzungsschutz. Diese lokale Schicht
erzwingt keine vollstaendige Netzwerkisolation und kann andere Geraete nicht
kontrollieren. Fuer einen echten Pruefungsbetrieb waeren institutionell
verwaltete Container-, Netzwerk-, Browser- und Geraeterichtlinien notwendig.

## 6. Implementierung

Die Referenzimplementierung verwendet Python ab Version 3.11, lokal
standardmaessig Python 3.12. Die Notebookvalidierung erfolgt mit `nbformat`.
Die optionale GLM-Anbindung nutzt das offizielle `zai-sdk` in Version 0.2.3.
Die Kommandozeile bietet `unibot autonomy`, `unibot notebook import`,
`unibot companion`, `unibot serve --pair` und `unibot gateway launch`.

Die API v2 stellt Gesundheit, Kopplung, Sitzung, sokratische Hilfe,
Notebook-Import und Metadatenexport bereit. V1 bleibt fuer eine Alpha-Phase
kompatibel, wird ueber HTTP jedoch ebenfalls durch Sitzungstoken und
Origin-Pruefung geschuetzt.

GitHub Actions prueft Python 3.11, 3.12 und 3.13. Weitere Jobs pruefen neue
Module statisch, untersuchen Abhaengigkeiten und Geheimnisse und fuehren die
Browseroberflaeche in Chromium aus. Der Hauptzweig ist als menschlich
freizugebende Integrationslinie vorgesehen.

## 7. Evaluation

Der feste Korpus umfasst 180 synthetische Szenarien. Je 30 Faelle behandeln
zulaessige sokratische Hinweise, Hilfebudget, Quellenbindung, verbotene
Finalantworten, Datenschutzgrenzen und Prompt-Injection. Jedes Szenario
enthaelt Kategorie, erwartete Entscheidung, Hilfestufe, Guardian-Nutzung und
Erfolgsevidenz.

Primaere technische Masse sind Recall fuer verbotene Entscheidungen und die
Fehlblockierungsrate zulaessiger Hilfe. Der Zielwert fuer verbotene Faelle
liegt bei mindestens 0,95; zulaessige Hilfe soll hoechstens in 0,10 der
beobachteten Faelle falsch blockiert werden. Weitere Dimensionen sind
Quellenbindung, Klarheit der Verweigerung, sicherer naechster Schritt,
Datenschutz und Lernendenautonomie.

Diese Masse bewerten das System, nicht Studierende. Sie duerfen nicht in Noten,
Taeschungswahrscheinlichkeiten oder Pruefungsreife umgedeutet werden. Eine
spaetere Studie mit Menschen setzt Einwilligung, Datenschutzpruefung und eine
institutionelle Ethikentscheidung voraus.

## 8. Aktueller Ergebnisstand

Der gepruefte Ausgangsstand bestand aus 636 Python-Tests und 125
Pipeline-Pruefungen. UniBot 2.0 ergaenzt authentifizierte API-Grenzen,
sicheren Notebook-Import, einen fokussierten A0-A4-Browser-Mantel, einen
praxisgebundenen Gateway-Launcher, Autonomie-v2-Vertraege und den
180-Szenarien-Korpus. Mantle 2.1 ergaenzt einen lokalen Native-Messaging-
Begleiter, unveraenderliche Lernvertraege, inkrementelle Hilfekosten und einen
freiwilligen metadatenbasierten Lernbericht. Neue Browserpruefungen fuehren
Zellwahl, Sitzung, Hilfeanfrage und schmale Darstellung in Chromium aus.

Der Korpus und die Messfunktionen sind implementiert. Es liegen in diesem
Entwurf noch keine empirischen Resultate aus einer Studierendenstudie und kein
Nachweis einer pruefungssicheren Umgebung vor. Diese Luecken werden nicht als
positive Ergebnisse dargestellt.

## 9. Grenzen und Risiken

Der Guardian verwendet weiterhin regelbasierte Elemente. Umschreibungen
koennen verbotene Inhalte verschleiern; harmlose Codefragmente koennen falsch
markiert werden. Der semantische Praezisionsbenchmark ist deshalb der naechste
aktive Forschungsauftrag.

DNS-Pruefung und Domain-Allowlist reduzieren das Risiko beim Download, ersetzen
aber keine institutionelle Content-Infrastruktur. Browser-Erweiterungen
koennen deaktiviert werden. Ein lokaler Jupyter-Prozess kontrolliert weder ein
zweites Geraet noch alle Netzwerkwege. Providerantworten koennen trotz
strukturiertem Schema fehlerhaft sein und werden daher nicht automatisch
angewendet.

Die Bezeichnung Bachelorarbeitsniveau beschreibt Aufbau, Quellenbindung und
Reproduzierbarkeit. Gretel ist kein eingeschriebener Mensch und kann keine
rechtswirksame Pruefungsleistung einreichen. Menschliche Verantwortung darf
nicht durch Autorenlabel, Tests oder Modellkonsens ersetzt werden.

## 10. Datenschutz und Ethik

Das System folgt Datenminimierung: Rohantworten werden standardmaessig nur
gehasht, Notebookausgaben entfernt und oeffentliche Exporte auf aggregierte
Metadaten begrenzt. Der GLM-Kontext entsteht aus einer Git-Allowlist und darf
keine privaten Lehr-, Personen-, Gesundheits-, Kommunikations- oder
Zugangsdaten enthalten.

Datenschutz ist nicht nur ein Filterproblem. Zweck, Rechtsgrundlage,
Aufbewahrung, Betroffenenrechte, Auftragsverarbeitung und institutionelle
Verantwortlichkeit muessen vor realer Nutzung menschlich geklaert werden.
Dass ein synthetischer Test besteht, ist keine Datenschutzfreigabe.

Didaktisch soll UniBot Autonomie foerdern, nicht Misstrauen automatisieren.
Deshalb erzeugt es keine verdeckte Bewertung und keine disziplinarische
Evidenz. Blockierungen sollen eine Begruendung und einen sicheren kleineren
Schritt anbieten.

## 11. Reproduzierbarkeit

Quellcode, Dokumentation, Work-Queue und synthetische Szenarien liegen im
oeffentlichen Repository. Die Python-Matrix, fokussierten Sicherheitspruefungen,
Browser-E2E-Laeufe und naechtlichen Pipeline-Artefakte sind als GitHub Actions
definiert. Provideraufrufe benoetigen keinen geheimen Inhalt aus dem
Repository; der Schluessel verbleibt im lokalen Schluesselbund.

Ein reproduzierbarer Review beginnt mit Installation der Entwicklungsoptionen,
fokussierten Tests und `unibot public-safety`. Providerfreie Tests verwenden
Test-Doubles. Ein echter GLM-Aufruf ist fuer die Funktionspruefung der
Sicherheits- und Produktschichten nicht erforderlich.

## 12. Fazit

UniBot Guardian zeigt einen praktikablen Mittelweg zwischen unkontrollierter
Antwortgenerierung und pauschalem KI-Verbot. Die Kombination aus A0-A4-Politik,
lokalem Native Messaging, Notebook-Sanitisierung, synthetischer Evaluation und
transparenter KI-Provenienz schafft eine wissenschaftlich pruefbare Grundlage.

Die Arbeit belegt noch keine Lernwirksamkeit und keine Pruefungssicherheit.
Der naechste Schritt ist die Messung semantischer Fehlfreigaben und
Fehlblockierungen. Erst danach folgen freiwillige formative Pilotierung und,
bei positiver menschlicher Pruefung, institutionelle Diskussion. Merge,
Hochschulabgabe und Pruefungsfreigabe bleiben menschliche Entscheidungen.

## Anhang A: Reproduzierbare Befehle

```text
python -m pytest -q
unibot public-safety
unibot autonomy preflight
unibot notebook import <oeffentliche-https-quelle-oder-lokale-datei>
unibot gateway launch <manifest> --dry-run
npm run test:browser
```

## Anhang B: Provenienzvertrag

Jeder durch Gretel erstellte Pull Request nennt Implementierungsagent,
Vorschlagsmodell, Gegenpruefungsmodell, Providerstatus, Tests, Unsicherheit und
ausstehende menschliche Entscheidung. GLM besitzt keine Dateisystem-, GitHub-,
Merge-, Benotungs-, Pruefungs- oder Final-Go-Berechtigung.
