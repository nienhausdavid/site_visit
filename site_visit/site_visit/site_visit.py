import frappe
from erpnext.projects.doctype.timesheet.timesheet import OverlapError
from frappe import _
from frappe.utils import get_datetime


def before_submit(doc, method=None):
	"""Legt ein Timesheet an, bucht es und verknuepft es - im selben Request
	wie das Buchen des Site Visit selbst. Serverseitig, damit kein zweiter
	Request und damit kein Zeitfenster fuer "has been modified after you have
	opened it" entsteht (gleiche Begruendung wie
	zeit_projekt.zeit_projekt.sales_order.before_submit)."""
	if doc.timesheet:
		return

	if get_datetime(doc.to_time) <= get_datetime(doc.from_time):
		frappe.throw(_("End time must be after the start time."))

	ts = frappe.get_doc(
		{
			"doctype": "Timesheet",
			"employee": doc.employee,
			"company": doc.company,
			"time_logs": [
				{
					"activity_type": doc.activity_type,
					"from_time": doc.from_time,
					"to_time": doc.to_time,
					"project": doc.project or None,
					"description": doc.description or doc.name,
					"is_billable": 1,
				}
			],
		}
	)
	ts.insert()
	try:
		ts.submit()
	except OverlapError:
		frappe.throw(
			_("This time range overlaps an existing time entry for {0}.").format(doc.employee),
			title=_("Overlapping Time"),
		)

	doc.timesheet = ts.name
	frappe.msgprint(
		_("Timesheet {0} created and submitted.").format(f"<b>{ts.name}</b>"),
		indicator="green",
		alert=True,
	)


def on_cancel(doc, method=None):
	"""Storniert das verknuepfte Timesheet mit, sofern es noch nicht
	fakturiert wurde."""
	if not doc.timesheet:
		return

	ts = frappe.get_doc("Timesheet", doc.timesheet)
	if ts.docstatus != 1:
		return

	for row in ts.time_logs:
		if row.sales_invoice:
			frappe.throw(
				_("Timesheet {0} was already invoiced on {1} and can no longer be cancelled.").format(
					ts.name, row.sales_invoice
				)
			)

	ts.cancel()


def check_app_permission():
	"""Fuer add_to_apps_screen in hooks.py: wer die App-Kachel im Desk sehen darf."""
	if frappe.session.user == "Administrator":
		return True
	roles = frappe.get_roles()
	return any(role in roles for role in ("System Manager", "Projects Manager", "Employee"))


def force_chrome_pdf():
	"""Vor download_pdf/printview: erzwingt pdf_generator=chrome fuer alle
	Doctypes auf diesem Server.

	wkhtmltopdf (der Frappe-Standard) scheitert hier grundsaetzlich an jeder
	frisch gerenderten Druckvorlage - schon das von Frappe selbst
	eingebundene <link ...print.bundle...css> ist eine relative URL ohne
	Basis-Adresse, die wkhtmltopdf im from_string-Modus nicht aufloesen kann
	("ProtocolUnknownError"). Betroffen sind nicht nur Vorlagen mit Bildern:
	am 13.09.2026 reproduziert fuer Sales Order, Sales Invoice und Site
	Visit gleichermassen, per echtem HTTP-Request wie im Browser. Bereits
	vorhandene PDFs (z. B. an alten Rechnungen) stammen vermutlich noch aus
	der Frappe-Cloud-Migration und wurden nie auf diesem Server neu erzeugt
	- deshalb ist es vorher nicht aufgefallen.

	Normalerweise liest die App print_designer das pdf_generator-Feld des
	Print Format aus und setzt es genau so vor dem eigentlichen Request -
	print_designer ist auf diesem Server aber bewusst nicht installiert
	(kein version-16-Branch, Stabilitaetsbedenken laut INSTALL-APPS.md).
	Statt der riskanten App nur den konkret benoetigten Mechanismus selbst
	nachgebaut - hier bewusst ohne Doctype-Einschraenkung, weil der
	zugrundeliegende wkhtmltopdf-Fehler alle Doctypes betrifft, nicht nur
	Site Visit."""
	request = getattr(frappe.local, "request", None)
	if not request or request.path not in (
		"/api/method/frappe.utils.print_format.download_pdf",
		"/printview",
	):
		return
	frappe.local.form_dict.pdf_generator = "chrome"
