"""Serial No helper actions for used/demo device workflow."""

from __future__ import annotations

from typing import Optional

import frappe
from frappe import _
from frappe.exceptions import PermissionError
from frappe.model.document import Document


@frappe.whitelist()
def mark_serial_as_used(
	serial_no: str,
	reason: Optional[str] = None,
	valuation_rate: Optional[float] = None,
) -> dict[str, str]:
	"""Transfer a serialised device to the Used Devices warehouse."""
	serial = _get_serial(serial_no)

	if serial.apx_is_demo:
		frappe.throw(_("Device is currently marked as Demo. Receive it first."))

	if serial.apx_is_used:
		frappe.throw(_("Device is already flagged as Used."))

	if not serial.warehouse:
		frappe.throw(_("Source warehouse is missing on this Serial No."))

	used_warehouse = _ensure_company_warehouse(serial.company, "Stores - Used Devices")

	stock_entry = _make_stock_transfer(
		serial=serial,
		source_warehouse=serial.warehouse,
		target_warehouse=used_warehouse,
		reason=reason or _("Customer return marked as used."),
		valuation_rate=valuation_rate,
	)

	serial.db_set(
		{
			"apx_is_used": 1,
			"apx_last_stock_entry": stock_entry,
			"apx_last_transfer_reason": reason or _("Customer return marked as used."),
			"apx_previous_warehouse": serial.warehouse,
			"warehouse": used_warehouse,
			"customer": None,
			"delivery_document_type": None,
			"delivery_document_no": None,
			"delivery_date": None,
			"status": "Active",
		},
		update_modified=False,
	)

	if valuation_rate:
		serial.db_set("purchase_rate", valuation_rate, update_modified=False)

	serial.add_comment(
		"Comment",
		_("Moved to Used Devices via Stock Entry {0}").format(stock_entry),
	)

	return {"stock_entry": stock_entry, "target_warehouse": used_warehouse}


@frappe.whitelist()
def send_serial_as_demo(
	serial_no: str,
	reason: Optional[str] = None,
	demo_owner_type: Optional[str] = None,
	demo_owner: Optional[str] = None,
	expected_return: Optional[str] = None,
) -> dict[str, str]:
	"""Issue a serialised device to the Demo warehouse."""
	serial = _get_serial(serial_no)

	if serial.apx_is_demo:
		frappe.throw(_("Device is already marked as Demo."))

	if not serial.warehouse:
		frappe.throw(_("Source warehouse is missing on this Serial No."))

	if not demo_owner_type or not demo_owner:
		frappe.throw(_("Demo owner information is required."))

	demo_warehouse = _ensure_company_warehouse(serial.company, "Demo Devices - HO")

	remarks = reason or _("Dispatched as demo unit.")

	stock_entry = _make_stock_transfer(
		serial=serial,
		source_warehouse=serial.warehouse,
		target_warehouse=demo_warehouse,
		reason=remarks,
		valuation_rate=None,
	)

	serial.db_set(
		{
			"apx_is_demo": 1,
			"apx_last_stock_entry": stock_entry,
			"apx_last_transfer_reason": remarks,
			"apx_demo_owner_type": demo_owner_type,
			"apx_demo_owner": demo_owner,
			"apx_demo_expected_return": expected_return,
			"apx_previous_warehouse": serial.warehouse,
			"warehouse": demo_warehouse,
		},
		update_modified=False,
	)

	serial.add_comment(
		"Comment",
		_("Sent as Demo device to {0} via Stock Entry {1}").format(
			_demo_owner_label(demo_owner_type, demo_owner),
			stock_entry,
		),
	)

	return {"stock_entry": stock_entry, "target_warehouse": demo_warehouse}


@frappe.whitelist()
def receive_demo_serial(
	serial_no: str,
	target_warehouse: str,
	reason: Optional[str] = None,
) -> dict[str, str]:
	"""Receive a demo device back into stock."""
	serial = _get_serial(serial_no)

	if not serial.apx_is_demo:
		frappe.throw(_("Device is not marked as Demo."))

	if not serial.warehouse:
		frappe.throw(_("Current warehouse is missing on this Serial No."))

	if not target_warehouse:
		frappe.throw(_("Target warehouse is required."))

	stock_entry = _make_stock_transfer(
		serial=serial,
		source_warehouse=serial.warehouse,
		target_warehouse=target_warehouse,
		reason=reason or _("Demo device returned to stock."),
		valuation_rate=None,
	)

	serial.db_set(
		{
			"apx_is_demo": 0,
			"apx_last_stock_entry": stock_entry,
			"apx_last_transfer_reason": reason or _("Demo device returned to stock."),
			"apx_previous_warehouse": serial.warehouse,
			"warehouse": target_warehouse,
		},
		update_modified=False,
	)

	serial.add_comment(
		"Comment",
		_("Demo device received into {0} via Stock Entry {1}").format(
			target_warehouse,
			stock_entry,
		),
	)

	return {"stock_entry": stock_entry, "target_warehouse": target_warehouse}


def _get_serial(serial_no: str) -> Document:
	serial = frappe.get_doc("Serial No", serial_no)
	serial.check_permission("write")
	return serial


def _make_stock_transfer(
	serial: Document,
	source_warehouse: str,
	target_warehouse: str,
	reason: Optional[str] = None,
	valuation_rate: Optional[float] = None,
) -> str:
	if not frappe.has_permission("Stock Entry", "submit"):
		raise PermissionError(_("You do not have permission to submit Stock Entries."))

	item = frappe.get_doc("Item", serial.item_code)
	uom = item.stock_uom or frappe.db.get_single_value("Stock Settings", "stock_uom")

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.stock_entry_type = "Material Transfer"
	stock_entry.company = serial.company or frappe.defaults.get_global_default("company")
	stock_entry.purpose = "Material Transfer"
	stock_entry.remarks = reason or ""

	stock_entry.append(
		"items",
		{
			"item_code": serial.item_code,
			"s_warehouse": source_warehouse,
			"t_warehouse": target_warehouse,
			"qty": 1,
			"transfer_qty": 1,
			"conversion_factor": 1,
			"uom": uom,
			"serial_no": serial.serial_no,
			"basic_rate": valuation_rate or 0,
		},
	)

	stock_entry.insert()

	for item_row in stock_entry.items:
		if item_row.serial_no:
			item_row.db_set("serial_no", "")

	stock_entry.reload()
	stock_entry.submit()

	return stock_entry.name


def _ensure_company_warehouse(company: Optional[str], base_name: str) -> str:
	company = company or frappe.defaults.get_global_default("company")
	if not company:
		frappe.throw(_("Company value is required to determine target warehouse."))

	abbr = frappe.db.get_value("Company", company, "abbr") or company
	full_name = f"{base_name} - {abbr}"

	if not frappe.db.exists("Warehouse", full_name):
		parent = frappe.db.get_value(
			"Warehouse",
			{"company": company, "is_group": 1},
			"name",
			order_by="lft asc",
		)
		doc = frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": base_name,
				"company": company,
				"is_group": 0,
				"parent_warehouse": parent,
			}
		)
		doc.insert(ignore_permissions=True)

	return full_name


def _demo_owner_label(owner_type: str, owner: str) -> str:
	if not owner_type or not owner:
		return owner or ""

	try:
		meta = frappe.get_meta(owner_type)
	except frappe.DoesNotExistError:
		meta = None

	name_field = "name"
	if meta:
		search_fields = meta.get_search_fields()
		if search_fields:
			name_field = search_fields[0]

	try:
		label = frappe.db.get_value(owner_type, owner, name_field)
	except Exception:
		label = None

	label = label or owner
	return f"{owner_type}: {label}"

