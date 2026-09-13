app_name = "site_visit"
app_title = "Site Visit"
app_publisher = "Dein Name"
app_description = "Kundeneinsaetze dokumentieren (Fotos, Unterschrift) und automatisch ein abrechenbares Zeitblatt erzeugen"
app_email = "info@example.com"
app_license = "mit"

required_apps = ["frappe/erpnext"]

# ---------------------------------------------------------------------------
# Eigene App im Desk (Apps-Uebersicht + Logo oben links innerhalb der App)
# ---------------------------------------------------------------------------
app_logo_url = "/assets/site_visit/images/site_visit-logo.svg"

add_to_apps_screen = [
	{
		"name": "site_visit",
		"logo": "/assets/site_visit/images/site_visit-logo.svg",
		"title": "Site Visit",
		"route": "/app/site-visit",
		"has_permission": "site_visit.site_visit.site_visit.check_app_permission",
	}
]

# ---------------------------------------------------------------------------
# Formular-Skript
#
# Als Datei ausgeliefert statt als Client-Script-Datensatz - verschwindet
# restlos mit der App, ist versionierbar, unterliegt nicht dem
# Client-Script-Cache im Browser (siehe zeit_projekt/README.md "Aufbau").
# ---------------------------------------------------------------------------
doctype_js = {
	"Site Visit": "public/js/site_visit.js",
}

# ---------------------------------------------------------------------------
# Zeitblatt aus dem Site Visit
#
# Laeuft serverseitig, innerhalb derselben Transaktion wie das Buchen selbst
# (kein separater Request davor). Verhindert den "has been modified after you
# have opened it"-Konflikt, der bei einem eigenen frappe.call vor dem
# Buchen-Request auftreten kann (siehe zeit_projekt.zeit_projekt.sales_order
# fuer den Hintergrund - dort produktiv aufgetreten und dadurch behoben).
# Greift dadurch auch bei API-Zugriffen und Massenbuchungen.
# ---------------------------------------------------------------------------
doc_events = {
	"Site Visit": {
		"before_submit": "site_visit.site_visit.site_visit.before_submit",
		"on_cancel": "site_visit.site_visit.site_visit.on_cancel",
	},
}

# ---------------------------------------------------------------------------
# PDF-Generator serverweit auf "chrome" erzwingen
#
# wkhtmltopdf (Frappe-Standard) scheitert auf diesem Server grundsaetzlich
# an jeder frisch erzeugten Druckvorlage, nicht nur an Site Visit - schon
# das von Frappe selbst eingebundene print.bundle.css (relative URL ohne
# Basis-Adresse) bricht mit "ProtocolUnknownError" ab. Reproduziert am
# 13.09.2026 fuer Sales Order, Sales Invoice und Site Visit gleichermassen.
# Alte, bereits vorhandene Rechnungs-PDFs stammen vermutlich noch aus der
# Frappe-Cloud-Migration und wurden nie auf diesem Server neu erzeugt -
# deshalb ist es vorher nicht aufgefallen.
#
# frappe.utils.print_format.download_pdf ignoriert das pdf_generator-Feld
# des Print Format und faellt hart auf "wkhtmltopdf" zurueck. Das
# eigentliche Ausleseglied dafuer liefert normalerweise die App
# print_designer (eigener before_request-Hook), die auf diesem Server aber
# bewusst nicht installiert ist (kein version-16-Branch,
# Stabilitaetsbedenken laut INSTALL-APPS.md). Statt der riskanten App nur
# den konkret benoetigten Mechanismus selbst nachgebaut - siehe
# force_chrome_pdf() in site_visit.py fuer Details. Liegt in dieser App,
# wirkt aber (wie alle Hooks) serverweit fuer alle installierten Apps.
# ---------------------------------------------------------------------------
before_request = ["site_visit.site_visit.site_visit.force_chrome_pdf"]

# ---------------------------------------------------------------------------
# Site Visit in der Verknuepfungen-Liste des Projekt-Formulars
#
# Additiv (siehe project_dashboard.get_data) - ergaenzt nur einen Eintrag,
# ersetzt nicht die von ERPNext gelieferte Liste.
# ---------------------------------------------------------------------------
override_doctype_dashboards = {
	"Project": "site_visit.site_visit.project_dashboard.get_data",
}

# ---------------------------------------------------------------------------
# Optionale Kopplung an pdf_on_submit
#
# Traegt Site Visit in PDF on Submit Settings ein, wenn diese App installiert
# ist - siehe site_visit/install.py. Keine harte Abhaengigkeit (required_apps
# bleibt nur frappe/erpnext): after_install/before_uninstall pruefen selbst,
# ob pdf_on_submit ueberhaupt installiert ist.
# ---------------------------------------------------------------------------
after_install = "site_visit.site_visit.install.after_install"
before_uninstall = "site_visit.site_visit.install.before_uninstall"

# Der pdf_on_submit-Patch fuer den automatischen PDF-Weg steht in
# site_visit/__init__.py, nicht hier - siehe Kommentar dort fuer die
# Begruendung (hooks.py wird nicht zuverlaessig in jedem Prozesstyp beim
# Start importiert, das Paket-__init__.py dagegen schon).
