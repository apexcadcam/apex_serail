frappe.ui.form.on("Serial No", {
	refresh(frm) {
		if (frm.is_new()) {
			return;
		}

		// Make status flags readonly; can only change via actions
		try {
			frm.set_df_property("apx_is_used", "read_only", 1);
			frm.set_df_property("apx_is_demo", "read_only", 1);
		} catch (e) {
			// ignore if fields not present
		}

		const label_group = __("Apex Serial");

		if (!frm.doc.apx_is_used && !frm.doc.__onload?.apex_serial_loading) {
			frm.add_custom_button(
				__("Mark as Used"),
				() => show_mark_used_dialog(frm),
				label_group
			);
		}

		if (frm.doc.apx_is_demo) {
			frm.add_custom_button(
				__("Receive Demo Device"),
				() => show_receive_demo_dialog(frm),
				label_group
			);
		} else {
			frm.add_custom_button(
				__("Send as Demo"),
				() => show_send_demo_dialog(frm),
				label_group
			);
		}
	},
});

function show_mark_used_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Move to Used Devices"),
		fields: [
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("Transfer Reason"),
				reqd: 1,
				description: __("Example: Customer return, refurbished, etc."),
			},
			{
				fieldname: "valuation_rate",
				fieldtype: "Currency",
				label: __("New Valuation Rate"),
				description: __("Optional: update valuation rate after refurbishment."),
			},
		],
		primary_action_label: __("Transfer"),
		primary_action(values) {
			d.hide();
			frappe.call({
				method: "apex_serial.serial_flow.mark_serial_as_used",
				args: {
					serial_no: frm.doc.name,
					reason: values.reason,
					valuation_rate: values.valuation_rate,
				},
				freeze: true,
				freeze_message: __("Creating Stock Entry..."),
				callback: () => frm.reload_doc(),
			});
		},
	});

	d.show();
}

function show_send_demo_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Send Device as Demo"),
		fields: [
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("Dispatch Notes"),
				description: __("Purpose or customer reference."),
			},
			{
				fieldname: "demo_owner_type",
				fieldtype: "Select",
				label: __("Demo Owner Type"),
				options: ["Employee", "Sales Partner"],
				default: "Employee",
				reqd: 1,
			},
			{
				fieldname: "demo_owner",
				fieldtype: "Link",
				label: __("Demo Owner"),
				reqd: 1,
				get_query() {
					const doctype = d.get_value("demo_owner_type");
					return {
						doctype,
					};
				},
			},
			{
				fieldname: "expected_return",
				fieldtype: "Date",
				label: __("Expected Return Date"),
			},
		],
		primary_action_label: __("Dispatch"),
		primary_action(values) {
			d.hide();
			frappe.call({
				method: "apex_serial.serial_flow.send_serial_as_demo",
				args: {
					serial_no: frm.doc.name,
					reason: values.reason,
					demo_owner_type: values.demo_owner_type,
					demo_owner: values.demo_owner,
					expected_return: values.expected_return,
				},
				freeze: true,
				freeze_message: __("Creating Stock Entry..."),
				callback: () => frm.reload_doc(),
			});
		},
	});

	d.fields_dict.demo_owner.df.options = d.get_value("demo_owner_type");
	d.fields_dict.demo_owner.refresh();

	d.fields_dict.demo_owner_type.df.onchange = () => {
		const doctype = d.get_value("demo_owner_type");
		d.fields_dict.demo_owner.df.options = doctype;
		d.fields_dict.demo_owner.refresh();
		d.set_value("demo_owner", "");
	};

	d.show();
}

function show_receive_demo_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Receive Demo Device"),
		fields: [
			{
				fieldname: "target_warehouse",
				fieldtype: "Link",
				label: __("Target Warehouse"),
				options: "Warehouse",
				reqd: 1,
				default: frm.doc.apx_previous_warehouse || "",
			},
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("Receipt Notes"),
				description: __("Example: Demo returned by owner."),
			},
		],
		primary_action_label: __("Receive"),
		primary_action(values) {
			d.hide();
			frappe.call({
				method: "apex_serial.serial_flow.receive_demo_serial",
				args: {
					serial_no: frm.doc.name,
					target_warehouse: values.target_warehouse,
					reason: values.reason,
				},
				freeze: true,
				freeze_message: __("Creating Stock Entry..."),
				callback: () => frm.reload_doc(),
			});
		},
	});

	d.show();
}

