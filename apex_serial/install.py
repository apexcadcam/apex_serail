"""Install / uninstall helpers for Apex Serial."""

from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe import _


def after_install() -> None:
	"""Setup Serial No customizations after install."""
	try:
		print("\n" + "=" * 70)
		print("📦 Installing Apex Serial fixtures...")
		print("=" * 70)

		import_custom_fields()
		setup_used_demo_warehouses()

		frappe.db.commit()

		print("=" * 70)
		print("✅ Apex Serial installed successfully!")
		print("=" * 70 + "\n")
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Apex Serial Installation Error")
		print(f"\n❌ Error during installation: {str(e)}\n")
		raise


def after_migrate() -> None:
	"""Ensure defaults exist after migrations run."""
	try:
		setup_used_demo_warehouses()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Apex Serial After Migrate")


def before_uninstall() -> None:
	"""Clean up Serial No customizations before uninstall."""
	try:
		print("\n" + "=" * 70)
		print("🗑️  Uninstalling Apex Serial...")
		print("=" * 70)
		print("\n⚠️  WARNING: Serial No helper fields will be removed.\n")

		remove_custom_fields()

		frappe.db.commit()

		print("=" * 70)
		print("✅ Apex Serial uninstalled successfully!")
		print("=" * 70 + "\n")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Apex Serial Uninstall Error")
		print("\n❌ Error during uninstall. Check error logs for details.\n")


def import_custom_fields() -> None:
	"""Import Serial No custom fields from fixtures."""
	print("\n📋 Importing Serial No custom fields...")

	app_path = Path(frappe.get_app_path("apex_serial"))
	fixtures_path = app_path / "fixtures" / "custom_field.json"

	if not fixtures_path.exists():
		print(f"  ⚠️  custom_field.json not found at: {fixtures_path}")
		return

	with fixtures_path.open("r", encoding="utf-8") as handle:
		custom_fields = json.load(handle)

	total = len(custom_fields)
	print(f"  Found {total} custom field(s) to process")

	created = 0
	updated = 0
	failed = 0

	batch_size = 5
	for i in range(0, total, batch_size):
		batch = custom_fields[i:i + batch_size]
		batch_num = (i // batch_size) + 1
		total_batches = (total + batch_size - 1) // batch_size

		for field_data in batch:
			field_data["module"] = "Apex Serial"
			field_name = field_data.get("name")
			dt = field_data.get("dt")
			fieldname = field_data.get("fieldname")

			if not field_name or not dt or not fieldname:
				print(f"  ❌ Invalid fixture entry, skipping...")
				failed += 1
				continue

			try:
				if frappe.db.exists("Custom Field", field_name):
					frappe.db.set_value("Custom Field", field_name, "module", "Apex Serial")
					updated += 1
					print(f"  🔄 Updated: {dt}.{fieldname} [{batch_num}/{total_batches}]")
					continue

				custom_field = frappe.get_doc(field_data)
				custom_field.insert(ignore_permissions=True, ignore_if_duplicate=True)
				print(f"  ✅ Created: {dt}.{fieldname} [{batch_num}/{total_batches}]")
				created += 1
			except Exception as exc:
				print(f"  ❌ Failed: {dt}.{fieldname} - {exc}")
				failed += 1

		if i + batch_size < total:
			frappe.db.commit()

	print(f"\n  Summary: {created} created, {updated} updated, {failed} failed")
	if failed > 0:
		print(f"  ⚠️  {failed} field(s) failed. Check logs for details.")
	print("  ✓ Custom field installation complete!\n")


def remove_custom_fields() -> None:
	"""Remove Apex Serial custom fields during uninstall."""
	print("\n📋 Removing Apex Serial custom fields...")

	fieldnames = [
		"apx_is_used",
		"apx_is_demo",
		"apx_last_stock_entry",
		"apx_last_transfer_reason",
		"apx_demo_owner_type",
		"apx_demo_owner",
		"apx_demo_expected_return",
		"apx_previous_warehouse",
	]

	custom_fields = frappe.get_all(
		"Custom Field",
		filters={"dt": "Serial No", "fieldname": ["in", fieldnames]},
		fields=["name", "dt", "fieldname"],
	)

	if not custom_fields:
		print("  ℹ️  No Apex Serial custom fields found to remove")
		return

	print(f"  Found {len(custom_fields)} custom field(s) to remove:")

	removed = 0
	failed = 0

	for field in custom_fields:
		field_label = f"{field.dt}.{field.fieldname}"
		try:
			if frappe.db.exists("Custom Field", field.name):
				frappe.delete_doc("Custom Field", field.name, force=True, ignore_permissions=True)
				print(f"  ✅ Removed: {field_label}")
				removed += 1
			else:
				print(f"  ⏭️  {field_label} not found, skipping...")
		except Exception as exc:
			print(f"  ❌ Failed to remove {field_label}: {exc}")
			failed += 1

	print(f"\n  Summary: {removed} removed, {failed} failed")
	print("  ✓ Custom field cleanup complete!\n")


def setup_used_demo_warehouses() -> None:
	"""Ensure dedicated warehouses for used and demo devices exist."""
	print("\n🏬 Ensuring Apex Serial warehouses exist...")

	default_company = frappe.defaults.get_global_default("company")
	if not default_company:
		print("  ⚠️  No default company set. Skipping warehouse creation.")
		return

	company_abbr = frappe.db.get_value("Company", default_company, "abbr") or default_company

	parent_warehouse = frappe.db.get_value(
		"Warehouse",
		{"company": default_company, "is_group": 1},
		"name",
		order_by="lft asc",
	)

	warehouse_bases = [
		"Stores - Used Devices",
		"Demo Devices - HO",
	]

	for base_name in warehouse_bases:
		full_name = f"{base_name} - {company_abbr}"

		if frappe.db.exists("Warehouse", full_name):
			print(f"  ✅ Warehouse exists: {full_name}")
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": base_name,
				"company": default_company,
				"is_group": 0,
			}
		)

		if parent_warehouse:
			doc.parent_warehouse = parent_warehouse

		try:
			doc.insert(ignore_permissions=True)
			print(f"  ✅ Created warehouse: {full_name}")
		except Exception as exc:
			print(f"  ❌ Failed to create warehouse {full_name}: {exc}")

	print("  ✓ Warehouse preparation complete!\n")

