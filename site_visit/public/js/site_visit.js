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

		// Ueber die Verknuepfungen-Liste des Projekts angelegt ("+" bei Site
		// Visit): project ist dann schon vorbelegt, aber das Feldevent
		// project() unten feuert dabei nicht (Frappe setzt route_options beim
		// Neuanlegen direkt als Feldwert, nicht ueber set_value). Deshalb hier
		// dieselbe Logik einmal explizit anstossen.
		if (frm.doc.project) fill_from_project(frm);
	},

	project(frm) {
		if (!frm.doc.project) return;
		fill_from_project(frm);
	},

	sales_order(frm) {
		// Kunde (und, falls noch leer, Projekt) aus dem gewaehlten Auftrag
		// uebernehmen - derselbe Grund wie bei project(): der Techniker soll
		// das nicht doppelt eintragen muessen.
		if (!frm.doc.sales_order) return;
		frappe.db.get_value('Sales Order', frm.doc.sales_order, ['customer', 'project']).then((r) => {
			if (!r.message) return;
			if (r.message.customer) frm.set_value('customer', r.message.customer);
			if (r.message.project && !frm.doc.project) frm.set_value('project', r.message.project);
		});
	},

	refresh(frm) {
		frm.dashboard.clear_headline();
		if (frm.doc.docstatus === 0 && !frm.doc.customer_signature) {
			frm.dashboard.set_headline_alert(__('No customer signature captured yet.'), 'orange');
		}
		if (frm.doc.docstatus === 1 && frm.doc.timesheet) {
			frm.add_custom_button(__('Open Timesheet'), () => {
				frappe.set_route('Form', 'Timesheet', frm.doc.timesheet);
			});
		}
		if (frm.doc.docstatus === 0 && !frm.doc.sales_order) {
			frm.add_custom_button(__('New Sales Order'), () => show_create_sales_order_dialog(frm));
		}
	},
});

// Betrag in der Zusatzartikel-Tabelle ist reine Anzeige (qty * rate) - der
// verknuepfte Auftrag rechnet beim Uebernehmen selbst neu (Steuern,
// Preisregeln usw., siehe site_visit.py -> _sync_extra_items_to_sales_order).
frappe.ui.form.on('Site Visit Item', {
	qty(frm, cdt, cdn) {
		update_extra_item_amount(cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		update_extra_item_amount(cdt, cdn);
	},
});

function update_extra_item_amount(cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	const qty = Number(row.qty) || 0;
	const rate = Number(row.rate) || 0;
	frappe.model.set_value(cdt, cdn, 'amount', qty * rate);
}

function show_create_sales_order_dialog(frm) {
	if (!frm.doc.customer) {
		frappe.msgprint(__('Please select a Customer first.'));
		return;
	}
	if (!(frm.doc.extra_items || []).length) {
		frappe.msgprint(__('Add at least one item below before creating a new Sales Order.'));
		return;
	}
	const dialog = new frappe.ui.Dialog({
		title: __('New Sales Order'),
		fields: [{ fieldname: 'po_no', fieldtype: 'Data', label: __('Customer Reference') }],
		primary_action_label: __('Create'),
		primary_action(values) {
			frappe.call({
				method: 'site_visit.site_visit.site_visit.create_sales_order',
				args: {
					customer: frm.doc.customer,
					company: frm.doc.company,
					project: frm.doc.project,
					po_no: values.po_no,
					items: frm.doc.extra_items.map((row) => ({
						item_code: row.item_code,
						qty: row.qty,
						uom: row.uom,
						rate: row.rate,
					})),
				},
				freeze: true,
				freeze_message: __('Creating Sales Order...'),
				callback(r) {
					if (!r.message) return;
					dialog.hide();
					frm.set_value('sales_order', r.message).then(() => {
						// Diese Zeilen stecken schon im neuen Auftrag - beim
						// Buchen nicht nochmal uebernehmen (added_to_order,
						// siehe site_visit.py -> _sync_extra_items_to_sales_order).
						(frm.doc.extra_items || []).forEach((row) => {
							frappe.model.set_value(row.doctype, row.name, 'added_to_order', 1);
						});
					});
				},
			});
		},
	});
	dialog.show();
}

function fill_from_project(frm) {
	if (!frm.doc.customer) {
		frappe.db.get_value('Project', frm.doc.project, 'customer').then((r) => {
			if (r.message && r.message.customer) frm.set_value('customer', r.message.customer);
		});
	}
	// Genau ein passender Auftrag zum gewaehlten Projekt? Dann gleich
	// uebernehmen. Bei mehreren zeigt der Filter aus onload() nur noch die
	// passenden im Dropdown - der Techniker waehlt dann selbst.
	if (!frm.doc.sales_order) {
		frappe.db.get_list('Sales Order', {
			filters: { project: frm.doc.project, docstatus: ['!=', 2] },
			fields: ['name'],
			limit: 2,
		}).then((rows) => {
			if (rows.length === 1) frm.set_value('sales_order', rows[0].name);
		});
	}
}
