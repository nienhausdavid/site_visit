app_name = "site_visit"
app_title = "Site Visit"
app_publisher = "Dein Name"
app_description = "Kundeneinsaetze dokumentieren (Fotos, Unterschrift) und automatisch ein abrechenbares Zeitblatt erzeugen"
app_email = "info@example.com"
app_license = "mit"

required_apps = ["frappe/erpnext"]

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

# Kein after_install/before_uninstall: keine Custom Fields auf Kern-Doctypes,
# keine sonstigen Datensaetze, die manuell aufgeraeumt werden muessten. Alles
# Neue gehoert zum Modul "Site Visit" und wird von uninstall-app dadurch
# bereits vollstaendig entfernt.
