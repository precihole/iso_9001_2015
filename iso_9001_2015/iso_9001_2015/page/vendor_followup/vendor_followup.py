import frappe
from frappe.utils import getdate, date_diff
from datetime import datetime
from collections import deque

@frappe.whitelist()
def get_data(filters=None):
    if filters:
        data = []
        purchase_orders = frappe.db.get_list('Purchase Order', 
                                             filters=filters,
                                             fields=['transaction_date', 'name', 'po_type', 'supplier', 'schedule_date', 'contact_email', 'uom'],
                                             order_by='transaction_date desc'
        )

        for po in purchase_orders:
            po_dict = dict(po)
            if po_dict.get('transaction_date') and po_dict.get('schedule_date'):
                transaction_date = getdate(po_dict['transaction_date'])
                schedule_date = getdate(po_dict['schedule_date'])

                po_dict['lead_time_days'] = date_diff(schedule_date, transaction_date)
                po_dict['formatted_transaction_date'] = transaction_date.strftime('%d-%m-%Y')
                po_dict['number_of_days_from_po'] = ((datetime.now().date() - transaction_date).days) + 1
            else:
                po_dict['formatted_transaction_date'] = None
                po_dict['number_of_days_from_po'] = None

            purchase_order_doc = frappe.get_doc("Purchase Order", po_dict["name"])
            items = purchase_order_doc.items

            processing_queue = deque()
            processed_items = set()

            for item in items:
                item_dict = dict(po_dict)
                item_dict["item_name"] = item.item_name
                item_dict["item_code"] = item.item_code
                item_dict["qty"] = item.qty
                item_dict["fg_item"] = item.fg_item
                item_dict["uom"] = item.uom

                filter_field = item.fg_item if item.fg_item else item.item_code

                item_dict.update({
                    "purchase_receipt": None,
                    "total_accepted_qty": 0,
                    "total_rework": 0,
                    "total_reject": 0,
                    "total_received_qty": 0,
                    "pending_qty": item.qty,
                    "supplied_qty": 0,
                    "consumed_qty": 0,
                    "rm_balance_qty": 0,
                    "rm_received_qty": 0
                })

                if po_dict.get('po_type') == 'Sub-Contract':
                    processing_queue.append({
                        "type": "subcontracting_receipt",
                        "po_name": po_dict["name"],
                        "filter_field": filter_field,
                        "item_code": item.item_code,
                        "item_qty": item.qty,
                        "item_dict": item_dict
                    })
                else:
                    processing_queue.append({
                        "type": "purchase_receipt",
                        "po_name": po_dict["name"],
                        "filter_field": filter_field,
                        "item_code": item.item_code,
                        "item_qty": item.qty,
                        "item_dict": item_dict
                    })

                processing_queue.append({
                    "type": "subcontracting_order",
                    "po_name": po_dict["name"],
                    "filter_field": filter_field,
                    "item_code": item.item_code,
                    "item_qty": item.qty,
                    "item_dict": item_dict
                })

            while processing_queue:
                task = processing_queue.popleft()
                item_key = f"{task['item_code']}-{task['po_name']}"

                if item_key in processed_items:
                    continue

                if task["type"] == "purchase_receipt":
                    purchase_receipts = frappe.db.get_list("Purchase Receipt", 
                                                           filters={"purchase_order": task["po_name"], "docstatus": 1},
                                                           fields=["name", "posting_date"])

                    for pr in purchase_receipts:
                        pr_doc = frappe.get_doc("Purchase Receipt", pr.name)
                        for pr_item in pr_doc.items:
                            if pr_item.item_code == task["item_code"]:
                                task["item_dict"]["total_received_qty"] += pr_item.qty

                                qa_inspections = frappe.db.get_list("QA Inspection",
                                                                    filters={
                                                                        "reference_name": pr.name,
                                                                        "item_code": task["item_code"],
                                                                        "docstatus": 1
                                                                    },
                                                                    fields=["total_accepted_qty", "total_rework", "total_reject", "total_received_qty"])
                                
                                for qa in qa_inspections:
                                    task["item_dict"]["total_accepted_qty"] += qa.total_accepted_qty or 0
                                    task["item_dict"]["total_rework"] += qa.total_rework or 0
                                    task["item_dict"]["total_reject"] += qa.total_reject or 0
                                    task["item_dict"]["total_received_qty"] += qa.total_received_qty or 0

                    task["item_dict"]["pending_qty"] = max(0, task["item_qty"] - task["item_dict"]["total_accepted_qty"])

                elif task["type"] == "subcontracting_receipt":
                    subcontracting_orders = frappe.db.get_list("Subcontracting Order",
                                                               filters={"purchase_order": task["po_name"]},
                                                               fields=["name"])
                    so_names = [so.name for so in subcontracting_orders]

                    subcontracting_receipts = frappe.db.get_list("Subcontracting Receipt",
                                                                 filters={"subcontracting_order": ["in", so_names], "docstatus": 1},
                                                                 fields=["name"])

                    for sr in subcontracting_receipts:
                        sr_doc = frappe.get_doc("Subcontracting Receipt", sr.name)
                        for sr_item in sr_doc.items:
                            if sr_item.item_code == task["filter_field"]:
                                task["item_dict"]["total_received_qty"] += sr_item.qty

                                qa_inspections = frappe.db.get_list("QA Inspection",
                                                                    filters={
                                                                        "reference_name": sr.name,
                                                                        "item_code": task["filter_field"],
                                                                        "docstatus": 1
                                                                    },
                                                                    fields=["total_accepted_qty", "total_rework", "total_reject", "total_received_qty"])

                                for qa in qa_inspections:
                                    task["item_dict"]["total_accepted_qty"] += qa.total_accepted_qty or 0
                                    task["item_dict"]["total_rework"] += qa.total_rework or 0
                                    task["item_dict"]["total_reject"] += qa.total_reject or 0
                                    task["item_dict"]["total_received_qty"] += qa.total_received_qty or 0

                    task["item_dict"]["pending_qty"] = max(0, task["item_qty"] - task["item_dict"]["total_accepted_qty"])

                elif task["type"] == "subcontracting_order":
                    subcontracting_orders = frappe.db.get_list("Subcontracting Order",
                                                               filters={"purchase_order": task["po_name"]},
                                                               fields=["name"])

                    for so in subcontracting_orders:
                        supplied_items = frappe.db.get_all("Subcontracting Order Supplied Item",
                                                           filters={"parent": so.name, "main_item_code": task['filter_field']},
                                                           fields=["supplied_qty", "consumed_qty", "stock_uom"])

                        total_supplied = sum(item.supplied_qty for item in supplied_items)
                        total_consumed = sum(item.consumed_qty for item in supplied_items)

                        task["item_dict"]["supplied_qty"] += total_supplied
                        task["item_dict"]["consumed_qty"] += total_consumed
                        task["item_dict"]["rm_balance_qty"] = round(total_supplied - total_consumed, 3)
                        task["item_dict"]["rm_received_qty"] = round(total_consumed, 3)

                        if supplied_items and task["item_dict"].get("fg_item"):
                            task["item_dict"]["uom"] = supplied_items[0].stock_uom

                    # ✅ Skip completed items (optional: make configurable)
                    if task["item_dict"]["pending_qty"] <= 0:
                        continue

                    data.append(task["item_dict"])
                    processed_items.add(item_key)

        return data
    else:
        frappe.msgprint("No filters provided.")


@frappe.whitelist()
def send_supplier_email(supplier, email, po_name, schedule_date):
    user_fullname = frappe.get_value("User", frappe.session.user, "full_name")

    subject = f"Follow Up: Purchase Order {po_name}"
    message = f"""
    Dear {supplier},<br><br>
    This is a reminder regarding Purchase Order <b>{po_name}</b>,
    scheduled for delivery on <b>{schedule_date}</b>.<br><br>
    Kindly confirm the delivery status.<br><br>
    Best regards,<br>
    {user_fullname}<br>
    """

    try:
        frappe.sendmail(
            recipients=email,
            subject=subject,
            message=message,
            now=True
        )
    except Exception as e:
        frappe.log_error(f"Failed to send email to {email}: {e}")
        return f"Failed to send email: {e}"

