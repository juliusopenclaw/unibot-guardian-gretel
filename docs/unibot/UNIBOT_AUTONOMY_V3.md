# UniBot Autonomie v3

Stand: lokale Implementierung durch Gretel/Codex. GLM-5.2 ist vollständig
geparkt und hat zu dieser Version keinen Beitrag geleistet. Nach einem späteren
ausdruecklichen menschlichen Go bleibt es auf Vorschlag und Gegenpruefung
bereits oeffentlicher UniBot-Dateien beschraenkt; Julius bleibt menschlicher
Merge- und Release-Freigeber.

## Zielkette

`messbare Lücke -> WorkItemV3 -> GLM-Vorschlag -> Codex-Änderung -> registrierte Tests -> tatsächlicher Diff -> unabhängige Codex-Prüfung -> GLM-Gegenprüfung -> CI -> Entwurfs-PR -> menschlicher Merge`

Keiner dieser technischen Gates bedeutet eine Freigabe für `main`, eine
Prüfungsfreigabe oder eine automatische Veröffentlichung.

## Bereits implementiert

- `WorkItemV3` bindet Quelle, Hypothese, Produktdelta, Risiko, erlaubte Dateien,
  registrierte Test-IDs und Basis-Commit an einen unveränderlichen Hash.
- Die Zustandsmaschine lässt nur dokumentierte Übergänge zu. Fehler enden in
  `blocked`, `retryable` oder `gretel_proposed`; es gibt keinen technischen
  `final-go`-Zustand.
- Eine lokale SQLite-Datenbank speichert nur Verträge, Zustände, Hashes und
  Kostenaggregate. Prompts, Notebookzellen, Transkripte und Sitzungstoken werden
  nicht gespeichert.
- Ein POSIX-Lease verhindert parallele Produktläufe. Der Controller kann keinen
  zweiten Produkt-PR innerhalb desselben lokalen Laufes erzeugen.
- Der Providerzustand ist standardmäßig
  `parked_awaiting_zai_balance`. Vor dem Parkzustand werden keine
  Schlüsselbund-, SDK-, Preis- oder Netzwerkzugriffe benötigt. Entparken verlangt
  `public-unibot-only`; die Zustandsdatei enthält keinen Schlüssel.
- Der öffentliche GLM-Kontext wird aus einer expliziten, höchstens vier Dateien
  umfassenden Allowlist aufgebaut. Absolute Pfade, private Marker, Symlinks,
  Binärdateien und lokale Lern-/Notebookdaten werden abgewiesen.
- Codex-Angaben über geänderte Dateien gelten nicht als Beweis. Die Evidence
  wird aus dem tatsächlichen Git-Diff, den untracked Dateien und registrierten
  Testresultaten neu abgeleitet.
- `CodexReviewV1` und `GLMReviewV2` sind an den tatsächlichen Diff- und
  Evidence-Hash gebunden. Manipulierte Zusammenfassungen oder veraltete Reviews
  können dadurch keinen grünen Zustand erzeugen.
- Ein grüner Lauf erzeugt nur eine bereinigte Entwurfs-PR-Vorschau. Der
  Standardpfad führt keinen GitHub-Push und keinen Merge aus.

## CLI und API

```bash
unibot autonomy provider status
unibot autonomy provider park
unibot autonomy provider unpark --scope public-unibot-only
unibot autonomy rollout status
unibot autonomy loop install
unibot autonomy loop doctor
unibot autonomy loop tick
unibot autonomy audit RUN_ID
```

Die API stellt lokale Diagnose-, Provider-, Work-Item-, Rollout- und Audit-Routen unter
`/api/unibot/autonomy/...` bereit. Issue-Text ist reines Metadatum: Er wird nie
als Shell-, Python- oder Testbefehl ausgeführt. Die `launchd`-Installation wird
zunächst nur als lokales Manifest vorbereitet; das Laden und Starten eines
Systemdienstes bleibt eine ausdrückliche menschliche Maschinenaktion.

## GLM und Kosten

Der produktive GLM-Adapter ist absichtlich nicht im Default-Import verborgen
aktiviert. Ein späterer Adapter muss ausschließlich den geprüften öffentlichen
Kontext verwenden und höchstens zwei Modellaufrufe pro Auftrag durchführen:
Vorschlag und Gegenprüfung. Das lokale Kostenledger warnt ab 15 USD und stoppt
oberhalb von 20 USD pro Monatsfenster. Providerfehler erlauben höchstens Triage
und ein bereinigtes `gretel-proposed`-Artefakt, niemals einen Code-Push.

## Rollout

1. Zehn Mock-/Schattenläufe ohne Änderung und ohne Providerzugriff.
2. Zehn lokale Codex-Läufe in wegwerfbaren Arbeitskopien.
3. Ein beaufsichtigter Entwurfs-PR mit tatsächlicher CI.
4. Drei grüne, menschlich gemergte Canary-PRs.
5. Erst danach kann ein lokaler Wächter dauerhaft aktiviert werden.

Jeder Controller-Lauf klont den freigegebenen Basis-Commit in eine kurzlebige,
remote-freie Arbeitskopie ausserhalb von Git und iCloud und entfernt sie danach.
Schatten- und lokale Rollout-Zaehler werden nur nach einem tatsaechlichen
erfolgreichen Lauf fortgeschrieben. Der lokale Waechter bleibt deaktiviert,
bis beide Zehner-Gates und die spaeteren menschlichen Canary-Merges vorliegen.

Die gegenwärtige Implementierung stellt die Verträge und Gates bereit; echte
Z.AI-Credentials, eine repo-beschränkte GitHub App, Branchschutz und menschliche
PR-Merges werden nicht aus dem lokalen Code heraus erzeugt.

## Rollenkennzeichnung

`Gretel/Codex` implementiert und dokumentiert. `GLM-5.2` schlägt vor und prüft
gegen, sobald ein menschlich freigegebener öffentlicher Providerlauf aktiviert
ist. `Julius` prüft menschlich und führt zusammen. Die ausgelieferte
Lernhilfe bleibt lokal, deterministisch und ohne Provider funktionsfähig.
