# Copyright (c) 2026, Kiran and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SupplierEvaluation(Document):
	pass







import frappe

@frappe.whitelist()
def get_supplier_contacts(supplier_name: str):
    """
    Return contacts linked to a Supplier using Dynamic Link, including primary flags.
    Works across ERPNext versions.
    """

    if not supplier_name:
        return []

    # Get all contact names linked to this supplier via Dynamic Link child table
    contact_names = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Supplier",
            "link_name": supplier_name,
            "parenttype": "Contact",
        },
        pluck="parent",
    )

    if not contact_names:
        return []

    contacts = frappe.get_all(
        "Contact",
        filters={"name": ["in", contact_names]},
        fields=[
            "name",
            "first_name",
            "last_name",
            "email_id",
            "mobile_no",
            "designation"        ],
        order_by="is_primary_contact desc, modified desc",
    )

    return contacts
