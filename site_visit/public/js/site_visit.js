// Zeitblatt wird erst beim Buchen angelegt (serverseitig, siehe hooks.py ->
// doc_events -> site_visit.site_visit.site_visit.before_submit). Dieses
// Skript setzt nur Feld-Defaults und liefert nach dem Buchen einen Link
// dorthin - keine async Calls vor dem Buchen, um die Race Condition aus
// zeit_projekt/sales_order.js nicht zu wiederholen.

frappe.ui.form.on('Site Visit', {
	onload(frm) {
		// Auftrag-Auswahl auf Auftraege des gewaehlten Projekts einschraenken.
		// Dynamischer Filter - wird bei jedem Oeffnen des Dropdowns neu anhand
		// des aktuellen frm.doc.project ausgewertet.
		frm.set_query('sales_order', () => {
			return frm.doc.project ? { filters: { project: frm.doc.project } } : {};
		});

		if (!frm.is_new()) return;
		if (!frm.doc.employee) {
			frappe.db.get_value('Employee', { user_id: frappe.session.user, status: 'Active' }, 'name')
				.then((r) => {
					if (r.message && r.message.name) frm.set_value('employee', r.message.name);
				});
		}
		if (!frm.doc.from_time) frm.set_value('from_time', frappe.datetime.now_datetime());
	},

	project(frm) {
		// Genau ein passender Auftrag zum gewaehlten Projekt? Dann gleich
		// uebernehmen. Bei mehreren zeigt der Filter aus onload() nur noch die
		// passenden im Dropdown - der Techniker waehlt dann selbst.
		if (!frm.doc.project) return;
		frappe.db.get_list('Sales Order', {
			filters: { project: frm.doc.project, docstatus: ['!=', 2] },
			fields: ['name'],
			limit: 2,
		}).then((rows) => {
			if (rows.length === 1) frm.set_value('sales_order', rows[0].name);
		});
	},

	refresh(frm) {
		frm.dashboard.clear_headline();
		if (frm.doc.docstatus === 0 && !frm.doc.customer_signature) {
			frm.dashboard.set_headline_alert('No customer signature captured yet.', 'orange');
		}
		if (frm.doc.docstatus === 1 && frm.doc.timesheet) {
			frm.add_custom_button(__('Open Timesheet'), () => {
				frappe.set_route('Form', 'Timesheet', frm.doc.timesheet);
			});
		}
	},
});
