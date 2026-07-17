# UniBot TutorRulePackV2

Stand: lokale, deterministische Entwicklung durch Gretel/Codex. GLM-5.2 ist
fuer diesen Baustein nicht erforderlich und bleibt geparkt.

## Zweck

TutorRulePackV2 verbindet sichtbare Python-Struktur, Fehlertyp, erkannte
Kompetenzbereiche und versionierte Quellenanker mit einem kleinsten naechsten
Lernschritt. Der Tutor fuehrt Notebookcode nie aus und speichert weder Zelltext
noch den eigenen Versuch.

Das Pack deckt die bounded Bereiche Python-Grundlagen, Kontrollfluss,
Collections, Funktionen, NumPy, pandas, Visualisierung, Statistik, Debugging
und Notebookzustand ab. Die Auswahl ist reproduzierbar: gleicher Task-, Zell-
und Traceback-Kontext ergibt dieselbe Regel-ID.

## Wissensgrenze

Kann keine Regel einen belastbaren oeffentlichen oder lokal freigegebenen
Quellenanker zuordnen, liefert UniBot `no_reliable_source`. Es gibt dann keine
generische Fachbehauptung, keinen Quellenanker und keinen Hilfebudget-Abzug.
Die lernende Person bekommt nur die Aufforderung, den eigenen naechsten
Pruefschritt zu formulieren.

Das ist eine wissenschaftlich wichtige Negativentscheidung: Sprachlich
fluessige Hilfe ersetzt keine nachgewiesene Quellenbindung.

## Stufen

- A0: Ziel, Eingabe und erwartete Ausgabe klären.
- A1: sichtbare Fehlerart oder kleinste Problemstelle lokalisieren.
- A2: Konzept, Prüffrage und Quellenanker verbinden.
- A3: Formelstruktur, Variablen oder Pseudocode skizzieren.
- A4: unvollständiges Gerüst mit absichtlichen Lücken.

Vollständiger Aufgabencode, konkrete Endwerte und fertige Interpretation
bleiben durch den bestehenden Guardian-Ausgabefilter blockiert. Der
Pruefungsstatus bleibt `not_cleared`; Barrierefreiheit ist kostenneutral und
wird nicht als Lernleistung bewertet.

## Nachweis

Jede Tutorantwort weist `TutorRulePackV2`, `rule_id`, `knowledge_boundary`,
Quellen-IDs und die unveränderten Hash-/Budgetmetadaten aus. Tests prüfen
AST-Auswahl, Traceback-Auswahl, Quellenbindung und die fail-closed
`no_reliable_source`-Entscheidung mit synthetischen Eingaben.
