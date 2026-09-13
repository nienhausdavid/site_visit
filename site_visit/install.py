import click
import frappe

DOCUMENT_TYPE = "Site Visit"
PRINT_FORMAT = "Site Visit Report"


def after_install():
	_pdf_on_submit_enable()


def before_uninstall():
	# Kein frappe.db.commit() hier - siehe zeit_projekt/install.py fuer die
	# Begruendung (--dry-run verlaesst sich auf ein Rollback am Ende).
	_pdf_on_submit_disable()


def _pdf_on_submit_enable():
	"""Traegt Site Visit automatisch in PDF on Submit Settings ein, damit
	beim Buchen automatisch ein PDF am Einsatz haengt - nur falls die
	optionale App pdf_on_submit ueberhaupt installiert ist (siehe
	README.md "Automatische PDF-Erzeugung")."""
	if "pdf_on_submit" not in frappe.get_installed_apps():
		return

	settings = frappe.get_single("PDF on Submit Settings")
	if any(row.document_type == DOCUMENT_TYPE for row in settings.enabled_for):
		return

	settings.append("enabled_for", {"document_type": DOCUMENT_TYPE, "print_format": PRINT_FORMAT})
	settings.save(ignore_permissions=True)
	click.secho(
		f"Site Visit: in PDF on Submit Settings eingetragen "
		f"({DOCUMENT_TYPE} / {PRINT_FORMAT}).",
		fg="green",
	)


def _pdf_on_submit_disable():
	if "pdf_on_submit" not in frappe.get_installed_apps():
		return
	if not frappe.db.exists("DocType", "PDF on Submit Settings"):
		return

	settings = frappe.get_single("PDF on Submit Settings")
	remaining = [row for row in settings.enabled_for if row.document_type != DOCUMENT_TYPE]
	if len(remaining) == len(settings.enabled_for):
		return

	settings.enabled_for = []
	for row in remaining:
		settings.append("enabled_for", row)
	settings.save(ignore_permissions=True)
	click.secho("Site Visit: Eintrag in PDF on Submit Settings entfernt.", fg="yellow")
