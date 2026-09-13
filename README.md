# Site Visit

Frappe-App für ERPNext v15/v16: Kundeneinsätze vor Ort dokumentieren und daraus
automatisch ein abrechenbares Zeitblatt erzeugen.

Ein Techniker legt pro Einsatz einen **Site Visit** an: Zeitraum, Aktivitätsart,
Fotos, optional die Unterschrift des Kunden direkt auf dem eigenen Gerät. Beim
Buchen (Submit) wird automatisch ein **Timesheet** angelegt, gebucht und
verknüpft — bereit zur Abrechnung.

Ein **Auftrag** ist Pflicht, da darüber abgerechnet wird — gibt es noch
keinen, lässt er sich direkt aus dem Site Visit heraus anlegen (siehe
"Auftrag" unten). Wird vor Ort zusätzliches Material gebraucht (z. B. ein
USB-auf-LAN-Adapter), lässt sich das unter "Additional Items" erfassen und
wandert beim Buchen automatisch in die Auftragspositionen.

---

## Aufbau

```
site_visit/
├── pyproject.toml
├── license.txt
├── README.md
└── site_visit/
    ├── __init__.py           # Versionsnummer
    ├── hooks.py              # doctype_js + doc_events + pdf_on_submit-Patch
    ├── install.py            # after_install/before_uninstall (nur PDF on Submit Settings)
    ├── site_visit.py         # before_submit/on_cancel/create_sales_order/...
    ├── project_dashboard.py  # ergaenzt "Site Visit" in den Projekt-Verknuepfungen
    ├── modules.txt           # Modulname "Site Visit"
    ├── patches.txt
    ├── public/
    │   ├── js/site_visit.js       # Feld-Defaults, Auftragsfilter, Neuer-Auftrag-Dialog
    │   └── images/site_visit-logo.svg
    ├── translations/
    │   └── de.csv               # Deutsche Übersetzungen (App-Ebene, nicht im Modulordner!)
    ├── workspace_sidebar/
    │   └── site_visits.json     # Eigene Sidebar (nur Site Visit + Timesheet, kein Home-Link)
    └── site_visit/           # Modulordner
        ├── doctype/
        │   ├── site_visit/          # Haupt-Doctype (submittable)
        │   ├── site_visit_photo/    # Kindtabelle für Fotos
        │   └── site_visit_item/     # Kindtabelle fuer Zusatzartikel
        ├── print_format/
        │   └── site_visit_report/   # PDF-Vorlage
        └── workspace/
            └── site_visits/         # Desk-Seite der App
```

`install.py` legt **keine** Custom Fields oder sonstigen Datensätze auf
Kern-Doctypes an — der einzige Zweck ist der optionale Eintrag in
`PDF on Submit Settings` (siehe "Automatische PDF-Erzeugung" unten), und
auch der nur, wenn `pdf_on_submit` installiert ist. Alles andere gehört
weiterhin zum Modul "Site Visit" und wird von `uninstall-app` bereits
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

- die Doctype "Site Visit" und die Kindtabellen "Site Visit Photo"/"Site Visit Item"
- das Modul „Site Visit" und alles, was daran hängt
- das Formular-Skript, da es reiner Code ist
- die Zeile `Site Visit` in `PDF on Submit Settings` (nur falls `pdf_on_submit`
  installiert ist — `before_uninstall` räumt sie mit auf)

**Was bewusst bestehen bleibt:**

- bereits gebuchte Site Visits inkl. Fotos und Unterschrift (als Daten, auch
  wenn die Doctype-Definition entfernt wird, greift Frappes reguläre
  Backup-vor-dem-Löschen-Mechanik)
- bereits angelegte und gebuchte Timesheets, auch wenn das erzeugende
  Site Visit später storniert würde
- bereits fakturierte Timesheets — ein Site Visit mit fakturiertem Timesheet
  lässt sich nicht mehr stornieren (siehe `on_cancel` in `site_visit.py`)
- bereits in Aufträge übernommene Zusatzartikel (die Auftragspositionen
  selbst gehören nicht zu dieser App)

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

## Auftrag

`sales_order` ist Pflichtfeld — jeder Einsatz muss einem Auftrag zugeordnet
sein, da darüber (und über das automatisch erzeugte Timesheet) abgerechnet
wird. Gibt es noch keinen passenden Auftrag, öffnet der Button **"New Sales
Order"** im Formular (sichtbar, solange kein Auftrag verknüpft ist) einen
Dialog: Kunde/Firma/Projekt kommen vom Site Visit, dazu lässt sich die
**Kundenreferenz** (Feld `po_no`, wie beim normalen Anlegen eines Auftrags)
eintragen. Der neue Auftrag entsteht als **Entwurf** — Buchen bleibt Sache
des Vertriebs, nicht des Technikers vor Ort — und übernimmt die bereits
eingetragenen Zusatzartikel (siehe unten) als Startpositionen; dafür muss
mindestens eine Zeile in "Additional Items" stehen, da ein Auftrag ohne
Position nicht anlegbar ist.

**Zusätzliche Artikel** (`extra_items`): vor Ort zusätzlich benötigtes
Material (z. B. ein USB-auf-LAN-Adapter), das noch nicht im Auftrag steht.
Beim Buchen des Site Visit werden neue (noch nicht übernommene) Zeilen
automatisch in die Positionen des verknüpften Auftrags aufgenommen — auch
wenn der Auftrag bereits gebucht ist (über
`erpnext.controllers.accounts_controller.update_child_qty_rate`, dieselbe
Funktion, die auch der "Update Items"-Dialog im Auftrag selbst verwendet;
bestehende Positionen, Steuern und Summen werden dabei korrekt neu
berechnet). Da Techniker i. d. R. keine eigenen Sales-Order-Rechte haben,
läuft das serverseitig kurzzeitig als Administrator — die eigentliche
Berechtigungsprüfung ist die auf den Site Visit selbst.

## Automatische PDF-Erzeugung beim Buchen

Die App liefert ein eigenes, gestaltetes Print Format **"Site Visit Report"**
mit (Kopfbereich, Kundendaten, Fotogalerie, Unterschriftsblock) und setzt es
als Standard-Druckformat für "Site Visit". Das alleine erzeugt aber noch
keine automatische PDF-Anlage beim Buchen — dafür braucht es einen
PDF-Automatisierungsmechanismus wie die App
[`pdf_on_submit`](https://github.com/alyf-de/erpnext_pdf-on-submit) (bewusst
keine harte Abhängigkeit, `site_visit` funktioniert auch ohne).

Ist `pdf_on_submit` zum Zeitpunkt der Installation bereits vorhanden, trägt
`install.py` automatisch die Zeile `Site Visit` / `Site Visit Report` in
dessen **PDF on Submit Settings** ein — kein manueller Schritt nötig. Wird
`pdf_on_submit` erst später installiert, einmalig von Hand nachtragen (die
gleiche Zeile in *Enabled For*) oder `bench execute
site_visit.install.after_install` erneut laufen lassen.

`hooks.py` patcht zusätzlich `pdf_on_submit.attach_pdf.get_pdf_data()`, damit
die automatische PDF-Erzeugung über `frappe.get_print(..., pdf_generator=
"chrome")` läuft statt über deren eigenen, direkten wkhtmltopdf-Aufruf — auf
Servern, auf denen wkhtmltopdf grundsätzlich fehlschlägt (siehe
`force_chrome_pdf` weiter oben), würde die automatische PDF-Anlage sonst im
Hintergrund lautlos scheitern. Der Patch greift nur, wenn `pdf_on_submit`
tatsächlich installiert ist (`try`/`except ImportError`).

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
