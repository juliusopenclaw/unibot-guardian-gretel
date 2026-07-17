# UniBot Guardian

## Eine lokal ausgefuehrte sokratische Integritaetsschicht fuer Python-Notebooks

Status: oeffentlicher wissenschaftlicher Entwurf auf Bachelorarbeitsniveau

Implementierung und Dokumentation: Gretel, KI-Agent

Vorschlags- und Gegenpruefungsmodell: Z.AI GLM-5.2

Rolle: vorgesehen fuer eine spaetere oeffentliche Vorschlags- und
Gegenpruefung; in dieser Version geparkt

Providerstatus dieser Version: GLM geparkt; 0 Provideraufrufe und 0 GLM-Beitrag
zur Implementierung oder Dokumentation dieser Version

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
GLM-5.2 ist fuer eine spaetere, ausschliesslich oeffentliche Vorschlags- und
Gegenpruefungsphase vorgesehen; in dieser Version wurde es nicht aufgerufen.
Der wissenschaftliche Forschungskorpus umfasst 180 fest versionierte
synthetische Szenarien. Der aktuelle Guardian-Releasebenchmark ist davon
getrennt und verwendet 60 fuer den Provider gesperrte Held-out-Faelle.
Ein realer
Studierenden- oder Pruefungseinsatz ist nicht Gegenstand der vorliegenden
Freigabe und erfordert gesonderte menschliche, datenschutzrechtliche und
institutionelle Entscheidungen.

Als naechster technischer Zwischenschritt bildet eine kontrollierte
Pruefungssimulation den vollstaendigen Ablauf mit genau einem oeffentlichen,
synthetischen Notebook ab. Sie versiegelt den Ausgangszustand, verlangt einen
offline geschalteten Mac, isoliert Jupyter auf Loopback, begrenzt Hilfe auf A0
bis A2 und exportiert Notebook und Metadatenbeleg atomar. Ihr Status
`ready_for_institutional_rehearsal_review` ist ein Reviewstatus und keine
Pruefungsfreigabe; `exam_deployment_status` bleibt `not_cleared`.

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
Evaluation und eine transparente Arbeitsteilung zwischen Gretel/Codex,
GLM-5.2 in einer geparkten Entwicklungsrolle und menschlicher Verantwortung.

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

Die Autonomie-v3-Schleife waehlt hoechstens einen Auftrag und vier Dateien pro
Lauf. Ausgewaehlte, bereits von Git erfasste oeffentliche Dateien werden vor
einem Provideraufruf gescannt. In der vorliegenden Version bleibt der Provider
geparkt; die lokalen Tests und die Implementierung benoetigen GLM nicht. Fuer
eine spaetere Aktivierung ist vorgesehen, dass GLM ein streng strukturiertes
`GLMProposalV1` und eine daran gebundene Gegenpruefung liefert. Gretel/Codex
implementiert lokal, prueft den tatsaechlichen Diff und ein menschlicher
Reviewer entscheidet ueber das Zusammenfuehren. Laufdaten enthalten nur
Hashwerte, Modellversion, Tokenzahlen, Kosten und Status.

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

Die Browser-Erweiterung uebergibt lokale Dateien nicht als Pfad. Stattdessen
werden sie in 32-KiB-Abschnitten ueber Native Messaging an den lokalen
Companion gesendet. Eine aktive Uebertragung, 10 MiB, ein 60-Sekunden-
In-Memory-Timeout, ein pfadfreier Dateiname und ein SHA-256-Abgleich begrenzen
den Transport. Erst nach vollstaendiger Validierung und Bereinigung wird die
temporaere lokale Uebungskopie geschrieben; abgebrochene Rohdaten werden
verworfen.

Der Browser-Mantel besitzt nur die Arbeitsbereiche Sitzung, Hilfe und
Rueckblick. Getrennte Colab-, Jupyter- und manuelle Adapter lesen die aktive
Zelle, nicht den Ausgabecontainer, und lehnen unsichere Erkennung ab. A0 bis A4
reichen von der Orientierungsfrage bis zum unvollstaendigen Teilgeruest. Ein
hashgebundener Lernvertrag begrenzt feste oder adaptive Hilfe. Der Rueckblick
trennt Hilfenutzungsbudget, eigene Versuche und Quellen ohne Rohtranskript. Nach
dem Ende kann eine synthetische Transferaufgabe freiwillig und ohne UniBot-Hilfe
bearbeitet werden. Fuer diese Aufgabe werden nur Status, Antwort-Hash,
Zeichenanzahl und Zeit erfasst; es gibt weder Bewertung noch automatische
Eigenleistungs- oder Lernerfolgsbehauptung.

Die Erweiterung kommuniziert ueber einen origin-gebundenen Chrome Native Host
mit einem lokal installierbaren, ad-hoc-signierten Mac-Begleiter. Damit entfallen
der hartcodierte Port und das dauerhaft im Erweiterungsspeicher liegende Token.
Der gepaarte HTTP-Pfad bleibt als Entwickler- und Alpha-Kompatibilitaetsweg.

Das lokale Jupyter-Gateway startet eine gehashte Notebookkopie auf Loopback,
ohne Terminal und mit zufaelligem Sitzungsschutz. Diese lokale Schicht
erzwingt keine vollstaendige Netzwerkisolation und kann andere Geraete nicht
kontrollieren. Fuer einen echten Pruefungsbetrieb waeren institutionell
verwaltete Container-, Netzwerk-, Browser- und Geraeterichtlinien notwendig.

Die getrennte kontrollierte Pruefungssimulation v1 haertet diesen Demonstrator:
Sie akzeptiert nur die fest gehashte oeffentliche Fixture. Nach Download und
Bereinigung bindet `ExamRehearsalContractV1` Ausgangs- und Bereinigungshash,
Tutor- und Regelversion, A0-A2, Netzwerkregel und Aufbewahrung. Jupyter und
Kernel laufen unter einer macOS-Sandbox ohne externe Netzberechtigung; ein
zweiter lokaler Waechter bricht beim Wiederauftreten einer externen Route ab.
Der Jupyter-Prozess erbt keine Provider-Schluessel oder normale
Benutzerkonfiguration; Serverwurzel, Cache, Konfiguration und Laufzeit werden
in getrennte private Verzeichnisse gebunden. Dies ist keine vollstaendige
Dateisystem-Isolation des angemeldeten macOS-Kontos und bleibt deshalb fuer
echte Pruefungen eine institutionelle Infrastrukturaufgabe.
Der Abschluss stoppt Kernel und Gateway vor der Validierung und dem atomaren
Export. `ExamSubmissionManifestV1` enthaelt nur Hashes, Zeitpunkte,
Zellanzahlen und Grenzen, keine Zelltexte, Namen oder lokalen Pfade. SHA-256
belegt Integritaet, aber weder Identitaet noch Eigenleistung.

## 6. Implementierung

Die Referenzimplementierung verwendet Python ab Version 3.11, lokal
standardmaessig Python 3.12. Die Notebookvalidierung erfolgt mit `nbformat`.
Die optionale, derzeit geparkte GLM-Anbindung nutzt das offizielle `zai-sdk` in
Version 0.2.3.
Die Kommandozeile bietet `unibot autonomy`, `unibot notebook import`,
`unibot companion`, `unibot serve --pair`, `unibot gateway launch` und
`unibot rehearsal start|status|finish|verify|delete`.

Die API v2 stellt Gesundheit, Kopplung, Sitzung, sokratische Hilfe,
Notebook-Import und Metadatenexport bereit. V1 bleibt fuer eine Alpha-Phase
kompatibel, wird ueber HTTP jedoch ebenfalls durch Sitzungstoken und
Origin-Pruefung geschuetzt.

GitHub Actions prueft Python 3.11, 3.12 und 3.13. Weitere Jobs pruefen neue
Module statisch, untersuchen Abhaengigkeiten und Geheimnisse und fuehren die
Browseroberflaeche in Chromium aus. Der Hauptzweig ist als menschlich
freizugebende Integrationslinie vorgesehen.

## 7. Evaluation

Der wissenschaftliche Forschungskorpus umfasst 180 synthetische Szenarien. Je
30 Faelle behandeln
zulaessige sokratische Hinweise, Hilfebudget, Quellenbindung, verbotene
Finalantworten, Datenschutzgrenzen und Prompt-Injection. Jedes Szenario
enthaelt Kategorie, erwartete Entscheidung, Hilfestufe, Guardian-Nutzung und
Erfolgsevidenz.

Der aktuelle Releasebenchmark ist ein separater, fuer Providerkontexte
gesperrter Held-out-Satz aus 60 synthetischen Faellen. Er dient der
reproduzierbaren Freigabepruefung des Guardian und nicht dem Nachweis von
Lernwirksamkeit oder Pruefungssicherheit.

Primaere technische Freigabemasse des aktuellen Releasebenchmarks sind 100
Prozent Blockierung vollstaendiger Loesungen, 100 Prozent korrekte
Quellenbindung und hoechstens 5 Prozent Fehlblockierungen zulaessiger Hilfe.
Weitere Dimensionen sind Klarheit der Verweigerung, sicherer naechster Schritt,
Datenschutz und Hilfestufe. Diese Schwellen sind technische Gates fuer einen
Entwurfs-PR, keine Aussage ueber Studierende.

Diese Masse bewerten das System, nicht Studierende. Sie duerfen nicht in Noten,
Taeschungswahrscheinlichkeiten oder Pruefungsreife umgedeutet werden. Eine
spaetere Studie mit Menschen setzt Einwilligung, Datenschutzpruefung und eine
institutionelle Ethikentscheidung voraus.

## 8. Aktueller Ergebnisstand

Der aktuelle gepruefte Stand umfasst 774 Python-Tests, 125 Pipeline-Pruefungen,
13 feste Release-Gates und den separaten 60-Fall-Guardian-Releasebenchmark.
Die Gates umfassen unter anderem Three-Golden-Rules-Selbstpruefung,
Datenschutz- und Geheimnisscans, Hashbindung, Browserpruefung sowie eine
metadaten-only Colab-Canary. Der aktuelle Canary erfasste nur eine synthetische
Zellmetadatenprobe, las keine Notebookausgabe, speicherte keinen Zelltext und
fuehrte keinen Notebookcode aus. Der oeffentliche Entwicklungs-PR ist noch
nicht gemerged.

Der Korpus und die Messfunktionen sind implementiert. Es liegen in diesem
Entwurf noch keine empirischen Resultate aus einer Studierendenstudie, keine
WCAG-Konformitaetsbestaetigung durch eine institutionelle Stelle und kein
Nachweis einer pruefungssicheren Umgebung vor. Diese Luecken werden nicht als
positive Ergebnisse dargestellt. Die neue Transferaufgabe ist ein
metadata-only Messinstrument fuer eine spaetere Evaluation, kein Ergebnisnachweis
fuer einzelne Lernende.

## 9. Grenzen und Risiken

Der Guardian verwendet weiterhin regelbasierte Elemente. Umschreibungen
koennen verbotene Inhalte verschleiern; harmlose Codefragmente koennen falsch
markiert werden. Der 60-Fall-Releasebenchmark ist Regressionsevidenz, aber
kein Beleg fuer Lernwirksamkeit oder eine kontrollierte Pruefungsumgebung.
Naechste Forschungsluecken sind die unabhaengige Barrierefreiheitspruefung,
ein institutionell freigegebener Uebungspilot und die Auswertung der
metadaten-only Transferaufgabe.

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
Repository; der Schluessel verbleibt im lokalen Schluesselbund. In der
vorliegenden Version ist der Provider geparkt und es gab 0 Provideraufrufe.
Die Release-Evidenz bindet Gate-Status, Testnachweise und Sicherheitspruefung
an den jeweiligen sauberen Quellcommit.

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
Die technische Releasekette misst bereits Fehlfreigaben, Fehlblockierungen,
Quellenbindung und Datenschutz in synthetischen Faellen. Danach folgen die
unabhaengige Barrierefreiheitspruefung und eine freiwillige formative
Pilotierung, jeweils nur nach menschlicher und institutioneller Pruefung.
Merge, Hochschulabgabe und Pruefungsfreigabe bleiben menschliche
Entscheidungen.

## Anhang A: Reproduzierbare Befehle

```text
python -m pytest -q
unibot public-safety
unibot autonomy preflight
unibot notebook import <oeffentliche-https-quelle-oder-lokale-datei>
unibot gateway launch <manifest> --dry-run
npm run test:browser
unibot evaluate guardian --json
unibot evaluate 3gr --json
unibot release evidence --repo . --output <release-evidence.json>
```

## Anhang B: Provenienzvertrag

Jeder durch Gretel erstellte Pull Request nennt Implementierungsagent,
Vorschlagsmodell, Gegenpruefungsmodell, Providerstatus, Tests, Unsicherheit und
ausstehende menschliche Entscheidung. GLM besitzt keine Dateisystem-, GitHub-,
Merge-, Benotungs-, Pruefungs- oder Final-Go-Berechtigung.
