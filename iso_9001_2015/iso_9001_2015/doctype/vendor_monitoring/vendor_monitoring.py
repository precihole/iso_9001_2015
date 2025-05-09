# Copyright (c) 2024, Kiran and contributors
# For license information, please see license.txt








# supplier_name = frappe.form_dict.get("supplier_name")

# if not supplier_name:
#     frappe.response["error"] = _("Supplier name is required")
# else:
#     try:
#         # Fetch QA Inspection Data
#         qa_inspection_data = frappe.get_all(
#             "QA Inspection",
#             filters={"source_details": supplier_name},
#             fields=["name", "total_rework", "total_reject", "total_accepted_qty", "condition_of_goods_on_arrival"]
#         )

#         # Fetch Purchase Orders for the Supplier
#         po_data = frappe.get_all(
#             "Purchase Order",
#             filters={"supplier": supplier_name},
#             fields=["name", "schedule_date"]
#         )

#         # Extract PO names for filtering PRs
#         po_names = [po["name"] for po in po_data]

#         # Fetch Purchase Receipts that are **linked to these POs**
#         pr_data = []
#         if po_names:
#             pr_data = frappe.get_all(
#                 "Purchase Receipt",
#                 filters={"purchase_order": ["in", po_names]},
#                 fields=["name", "posting_date", "purchase_order"]
#             )

#         # Convert PR data into a dictionary to ensure **matching PO-PR structure**
#         pr_dict = {pr["purchase_order"]: pr for pr in pr_data}

#         # Ensure PR data **matches** the PO data structure
#         formatted_pr_data = []
#         for po in po_data:
#             pr_entry = pr_dict.get(po["name"], {"name": None, "posting_date": None, "purchase_order": po["name"]})
#             formatted_pr_data.append(pr_entry)

#         # Construct Response
#         frappe.response["message"] = {
#             "qa_inspection": qa_inspection_data,
#             "purchase_orders": po_data,
#             "purchase_receipts": formatted_pr_data  # PR data exactly matching PO data
#         }

#     except Exception as e:
#         frappe.log_error(f"Error fetching data for supplier {supplier_name}: {str(e)}")
#         frappe.response["error"] = _("An error occurred while fetching supplier-related data.")








import frappe
from frappe.model.document import Document

# Define a new class for Vendor Monitoring (currently no custom functionality needed)
class VendorMonitoring(Document):
    pass  # Keeping the class empty since we are using a whitelisted function

# Whitelisted function that can be called from the client-side
@frappe.whitelist()
def get_vendor_monitoring_data(supplier_name):
    # Ensure the supplier name is provided
    if not supplier_name:
        frappe.throw("Supplier name is required")  # Raise an error if supplier name is missing

    try:
        # Fetch QA Inspection Data for the given supplier
        qa_inspection_data = frappe.get_all(
            "QA Inspection",  # Document type to fetch data from
            filters={"source_details": supplier_name},  # Filter records by supplier name
            fields=["name", "total_rework", "total_reject", "total_accepted_qty", "condition_of_goods_on_arrival"]  # Required fields
        )

        # Fetch Purchase Orders related to the supplier
        po_data = frappe.get_all(
            "Purchase Order",  # Document type to fetch data from
            filters={"supplier": supplier_name},  # Filter records by supplier name
            fields=["name", "schedule_date"]  # Required fields
        )

        # Extract the names of the Purchase Orders for filtering Purchase Receipts
        po_names = [po["name"] for po in po_data]

        # Fetch Purchase Receipts that are linked to the fetched Purchase Orders
        pr_data = []
        if po_names:  # Ensure that we only fetch Purchase Receipts if there are related Purchase Orders
            pr_data = frappe.get_all(
                "Purchase Receipt",  # Document type to fetch data from
                filters={"purchase_order": ["in", po_names]},  # Filter records by linked Purchase Orders
                fields=["name", "posting_date", "purchase_order"]  # Required fields
            )

        # Convert the Purchase Receipt data into a dictionary to match each PO with its respective PR
        pr_dict = {pr["purchase_order"]: pr for pr in pr_data}

        # Format the PR data so that each PO has a corresponding PR, ensuring the data structure matches
        formatted_pr_data = [
            pr_dict.get(po["name"], {"name": None, "posting_date": None, "purchase_order": po["name"]})
            for po in po_data  # Iterate over each PO to match it with PR data
        ]

        # Return the data as a dictionary, so it can be used in the client-side callback
        return {
            "qa_inspection": qa_inspection_data,  # QA Inspection data for the supplier
            "purchase_orders": po_data,  # Purchase Orders data for the supplier
            "purchase_receipts": formatted_pr_data  # Formatted Purchase Receipts data
        }

    except Exception as e:
        # Log any exceptions that occur and provide a user-friendly error message
        frappe.log_error(f"Error fetching data for supplier {supplier_name}: {str(e)}")  # Log error for debugging
        frappe.throw("An error occurred while fetching supplier-related data.")  # Display error to the user
