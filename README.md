# Site Visit

Frappe-App für ERPNext v15/v16: Kundeneinsätze vor Ort dokumentieren und daraus
automatisch ein abrechenbares Zeitblatt erzeugen.

Ein Techniker legt pro Einsatz einen **Site Visit** an: Zeitraum, Aktivitätsart,
Fotos, optional die Unterschrift des Kunden direkt auf dem eigenen Gerät. Beim
Buchen (Submit) wird automatisch ein **Timesheet** angelegt, gebucht und
verknüpft — bereit zur Abrechnung.

---

## Aufbau

```
site_visit/
├── pyproject.toml
├── license.txt
├── README.md
└── site_visit/
    ├── __init__.py           # Versionsnummer
    ├── hooks.py              # doctype_js + doc_events
    ├── site_visit.py         # before_submit/on_cancel/check_app_permission
    ├── modules.txt           # Modulname "Site Visit"
    ├── patches.txt
    ├── public/
    │   ├── js/site_visit.js       # Feld-Defaults, Auftragsfilter, Link zum Zeitblatt
    │   └── images/site_visit-logo.svg
    ├── translations/
    │   └── de.csv               # Deutsche Übersetzungen (App-Ebene, nicht im Modulordner!)
    └── site_visit/           # Modulordner
        ├── doctype/
        │   ├── site_visit/          # Haupt-Doctype (submittable)
        │   └── site_visit_photo/    # Kindtabelle für Fotos
        ├── print_format/
        │   └── site_visit_report/   # PDF-Vorlage
        └── workspace/
            └── site_visits/         # Desk-Seite der App
```

Kein `install.py`: Es gibt keine Custom Fields auf Kern-Doctypes und keine
sonstigen Datensätze, die manuell aufgeräumt werden müssten — alles gehört
zum Modul "Site Visit" und wird von `uninstall-app` dadurch bereits
vollständig entfernt.

Das Formular-Skript ist eine **Datei**, kein Client-Script-Datensatz. Es
verschwindet restlos mit der App und unterliegt nicht dem
Client-Script-Cache im Browser.

## Sprache

Die App ist auf Englisch geschrieben (Feldbezeichnungen, Meldungen,
Druckvorlage) und liefert eine deutsche Übersetzung mit
(`site_visit/translations/de.csv`). Das ist das normale Frappe-Verfahren:
der englische Text im Code/in der Doctype-JSON bleibt die Quelle, die
CSV-Datei übersetzt sie für Nutzer mit Sprache "Deutsch" (User → Language).
Frappe wählt die Sprache automatisch passend zum jeweiligen Nutzer - keine
Einstellung pro App nötig.

Standardbegriffe, die bereits über Frappe/ERPNext selbst übersetzt sind
(z. B. "Customer", "Employee", "Project", "Sales Order", "Timesheet"),
sind bewusst **nicht** nochmal in `de.csv` enthalten, um keine
widersprüchlichen Übersetzungen zu erzeugen. Übersetzt sind nur die für
diese App eigenen Begriffe und Texte (z. B. "Site Visit" → "Kundeneinsatz",
Fehlermeldungen, Druckvorlagen-Überschriften).

Nach Änderungen an Texten im Code: neue/geänderte Strings auch in
`de.csv` ergänzen, sonst bleiben sie auf Deutsch unübersetzt (Englisch als
Fallback).

---

## Vor der Installation anpassen

In `pyproject.toml` und `site_visit/hooks.py` Name, E-Mail und Beschreibung
eintragen. Willst du die App anders nennen, muss der Name an vier Stellen
konsistent sein: Ordnername, Paketordner, `app_name` in `hooks.py` und `name`
in `pyproject.toml`.

---

## Installation (eigener Bench)

```bash
cd ~/frappe-bench
bench get-app https://github.com/<dein-user>/site_visit.git
bench --site <deine-site> install-app site_visit
bench build --app site_visit
bench --site <deine-site> clear-cache
```

## Installation (Frappe Cloud)

Eigene Apps brauchen dort ein Git-Repository und eine eigene Bench-Gruppe
(auf den kleinen Shared-Plänen nicht möglich).

1. Repository auf GitHub anlegen und den Inhalt dieses Ordners hochladen
2. In Frappe Cloud: Bench-Gruppe → *Apps* → *Add App* → *From GitHub*
3. Deploy anstoßen, danach die App auf der Site installieren

---

## Deinstallation

```bash
bench --site <deine-site> uninstall-app site_visit --dry-run   # nur anzeigen
bench --site <deine-site> uninstall-app site_visit
```

**Was dabei entfernt wird:**

- die Doctype "Site Visit" und die Kindtabelle "Site Visit Photo"
- das Modul „Site Visit" und alles, was daran hängt
- das Formular-Skript, da es reiner Code ist

**Was bewusst bestehen bleibt:**

- bereits gebuchte Site Visits inkl. Fotos und Unterschrift (als Daten, auch
  wenn die Doctype-Definition entfernt wird, greift Frappes reguläre
  Backup-vor-dem-Löschen-Mechanik)
- bereits angelegte und gebuchte Timesheets, auch wenn das erzeugende
  Site Visit später storniert würde
- bereits fakturierte Timesheets — ein Site Visit mit fakturiertem Timesheet
  lässt sich nicht mehr stornieren (siehe `on_cancel` in `site_visit.py`)

---

## Einrichtung

- Für jede genutzte **Activity Type** sollte ein sinnvoller Stundensatz
  hinterlegt sein, damit das automatisch erzeugte Timesheet korrekt
  abgerechnet werden kann.
- Ist auf derselben Site zusätzlich die Schwester-App
  [`zeit_projekt`](https://github.com/nienhausdavid/zeit_projekt) installiert,
  taucht das hier automatisch erzeugte (gebuchte, `is_billable=1`)
  Timesheet direkt in deren "Zeiten aus Zeiterfassung importieren"-Dialog
  auf der Ausgangsrechnung auf — keine zusätzliche Konfiguration nötig, nur
  lose Kopplung über die Kern-Doctype "Activity Type".

## Eigene App im Desk

Die App bringt ein eigenes Logo mit (`public/images/site_visit-logo.svg`) und
registriert sich über `add_to_apps_screen`/`app_logo_url` in `hooks.py` als
eigene Kachel auf der Apps-Übersicht (`/apps`), inklusive einer eigenen
Workspace mit Verknüpfungen zu "Site Visit" und "Timesheet".

## Automatische PDF-Erzeugung beim Buchen

Die App liefert ein eigenes, gestaltetes Print Format **"Site Visit Report"**
mit (Kopfbereich, Kundendaten, Fotogalerie, Unterschriftsblock) und setzt es
als Standard-Druckformat für "Site Visit". Das alleine erzeugt aber noch
keine automatische PDF-Anlage beim Buchen — dafür braucht es einen
PDF-Automatisierungsmechanismus wie die App
[`pdf_on_submit`](https://github.com/alyf-de/erpnext_pdf-on-submit) (bewusst
keine harte Abhängigkeit, `site_visit` funktioniert auch ohne).

Ist `pdf_on_submit` installiert, einmalig einrichten:

1. **PDF on Submit Settings** öffnen
2. Zeile in *Enabled For* hinzufügen: Document Type `Site Visit`,
   Print Format `Site Visit Report`
3. Speichern — ab dann wird bei jedem gebuchten Site Visit automatisch ein
   PDF erzeugt und angehängt

Ohne `pdf_on_submit` (oder eine ähnliche App) bleibt das Print Format
manuell nutzbar (Drucken/PDF-Button im Formular), nur eben nicht automatisch.

## Berechtigungen

| Rolle | Lesen | Schreiben | Anlegen | Buchen | Stornieren |
|---|---|---|---|---|---|
| System Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Projects Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Employee | eigene | eigene | ✓ | eigene | – |
| Projects User | ✓ | – | – | – | – |
| Accounts User | ✓ | – | – | – | – |

Ein gebuchter, unterschriebener Einsatz gilt als Bestätigung gegenüber dem
Kunden — nur Projects Manager/System Manager können ihn stornieren, nicht
der Techniker selbst. Es gibt bewusst keine eigene, engere Techniker-Rolle
als Fixture (Rollen sind nicht modulgebunden und würden beim Deinstallieren
als Karteileiche zurückbleiben); wer den Zugriff über die Standardrolle
"Employee" hinaus einschränken will, legt manuell eine eigene Rolle an.

---

## Erweiterungsideen

- **Externes USB/Bluetooth-Signaturpad** (z. B. Wacom STU) statt Finger/Stift
  auf dem Touch-Bildschirm. Das Feld `customer_signature` speichert am Ende
  nur ein Bild — ein Hardware-Pad müsste nur dasselbe Feld befüllen (über
  Hersteller-SDK/Treiber im Browser), kein Umbau des Datenmodells nötig.
- Mehrere Zeitsegmente/Pausen pro Einsatz statt eines durchgehenden Blocks.
- Automatisches Zusammenfassen mehrerer Einsätze desselben Mitarbeiters zu
  einem Timesheet pro Zeitraum, statt eines neuen Timesheets je Einsatz.
- GPS/Standort-Erfassung beim Anlegen.
- Direkte Rechnungs-/Angebotserstellung aus dem Site Visit heraus.
