# import frappe
# from frappe.utils import getdate, date_diff
# from datetime import datetime
# from collections import deque

# @frappe.whitelist()
# def get_data(filters=None):
#     if filters:
#         data = []
#         purchase_orders = frappe.db.get_list('Purchase Order', 
#                                              filters=filters,
#                                              fields=['transaction_date', 'name', 'po_type', 'supplier', 'schedule_date', 'contact_email', 'uom'],
#                                              order_by='transaction_date desc'
#         )

#         for po in purchase_orders:
#             po_dict = dict(po)
#             if po_dict.get('transaction_date') and po_dict.get('schedule_date'):
#                 transaction_date = getdate(po_dict['transaction_date'])
#                 schedule_date = getdate(po_dict['schedule_date'])

#                 po_dict['lead_time_days'] = date_diff(schedule_date, transaction_date)
#                 po_dict['formatted_transaction_date'] = transaction_date.strftime('%d-%m-%Y')
#                 po_dict['number_of_days_from_po'] = ((datetime.now().date() - transaction_date).days) + 1
#             else:
#                 po_dict['formatted_transaction_date'] = None
#                 po_dict['number_of_days_from_po'] = None

#             purchase_order_doc = frappe.get_doc("Purchase Order", po_dict["name"])
#             items = purchase_order_doc.items

#             processing_queue = deque()
#             processed_items = set()

#             for item in items:
#                 item_dict = dict(po_dict)
#                 item_dict["item_name"] = item.item_name
#                 item_dict["item_code"] = item.item_code
#                 item_dict["qty"] = item.qty
#                 item_dict["fg_item"] = item.fg_item
#                 item_dict["uom"] = item.uom

#                 filter_field = item.fg_item if item.fg_item else item.item_code

#                 item_dict.update({
#                     "purchase_receipt": None,
#                     "total_accepted_qty": 0,
#                     "total_rework": 0,
#                     "total_reject": 0,
#                     "total_received_qty": 0,
#                     "pending_qty": item.qty,
#                     "supplied_qty": 0,
#                     "consumed_qty": 0,
#                     "rm_balance_qty": 0,
#                     "rm_received_qty": 0
#                 })

#                 if po_dict.get('po_type') == 'Sub-Contract':
#                     processing_queue.append({
#                         "type": "subcontracting_receipt",
#                         "po_name": po_dict["name"],
#                         "filter_field": filter_field,
#                         "item_code": item.item_code,
#                         "item_qty": item.qty,
#                         "item_dict": item_dict
#                     })
#                 else:
#                     processing_queue.append({
#                         "type": "purchase_receipt",
#                         "po_name": po_dict["name"],
#                         "filter_field": filter_field,
#                         "item_code": item.item_code,
#                         "item_qty": item.qty,
#                         "item_dict": item_dict
#                     })

#                 processing_queue.append({
#                     "type": "subcontracting_order",
#                     "po_name": po_dict["name"],
#                     "filter_field": filter_field,
#                     "item_code": item.item_code,
#                     "item_qty": item.qty,
#                     "item_dict": item_dict
#                 })

#             while processing_queue:
#                 task = processing_queue.popleft()
#                 item_key = f"{task['item_code']}-{task['po_name']}"

#                 if item_key in processed_items:
#                     continue

#                 if task["type"] == "purchase_receipt":
#                     purchase_receipts = frappe.db.get_list("Purchase Receipt", 
#                                                            filters={"purchase_order": task["po_name"], "docstatus": 1},
#                                                            fields=["name", "posting_date"])

#                     for pr in purchase_receipts:
#                         pr_doc = frappe.get_doc("Purchase Receipt", pr.name)
#                         for pr_item in pr_doc.items:
#                             if pr_item.item_code == task["item_code"]:
#                                 task["item_dict"]["total_received_qty"] += pr_item.qty

#                                 qa_inspections = frappe.db.get_list("QA Inspection",
#                                                                     filters={
#                                                                         "reference_name": pr.name,
#                                                                         "item_code": task["item_code"],
#                                                                         "docstatus": 1
#                                                                     },
#                                                                     fields=["total_accepted_qty", "total_rework", "total_reject", "total_received_qty"])
                                
#                                 for qa in qa_inspections:
#                                     task["item_dict"]["total_accepted_qty"] += qa.total_accepted_qty or 0
#                                     task["item_dict"]["total_rework"] += qa.total_rework or 0
#                                     task["item_dict"]["total_reject"] += qa.total_reject or 0
#                                     task["item_dict"]["total_received_qty"] += qa.total_received_qty or 0

#                     task["item_dict"]["pending_qty"] = max(0, task["item_qty"] - task["item_dict"]["total_accepted_qty"])

#                 elif task["type"] == "subcontracting_receipt":
#                     subcontracting_orders = frappe.db.get_list("Subcontracting Order",
#                                                                filters={"purchase_order": task["po_name"]},
#                                                                fields=["name"])
#                     so_names = [so.name for so in subcontracting_orders]

#                     subcontracting_receipts = frappe.db.get_list("Subcontracting Receipt",
#                                                                  filters={"subcontracting_order": ["in", so_names], "docstatus": 1},
#                                                                  fields=["name"])

#                     for sr in subcontracting_receipts:
#                         sr_doc = frappe.get_doc("Subcontracting Receipt", sr.name)
#                         for sr_item in sr_doc.items:
#                             if sr_item.item_code == task["filter_field"]:
#                                 task["item_dict"]["total_received_qty"] += sr_item.qty

#                                 qa_inspections = frappe.db.get_list("QA Inspection",
#                                                                     filters={
#                                                                         "reference_name": sr.name,
#                                                                         "item_code": task["filter_field"],
#                                                                         "docstatus": 1
#                                                                     },
#                                                                     fields=["total_accepted_qty", "total_rework", "total_reject", "total_received_qty"])

#                                 for qa in qa_inspections:
#                                     task["item_dict"]["total_accepted_qty"] += qa.total_accepted_qty or 0
#                                     task["item_dict"]["total_rework"] += qa.total_rework or 0
#                                     task["item_dict"]["total_reject"] += qa.total_reject or 0
#                                     task["item_dict"]["total_received_qty"] += qa.total_received_qty or 0

#                     task["item_dict"]["pending_qty"] = max(0, task["item_qty"] - task["item_dict"]["total_accepted_qty"])

#                 elif task["type"] == "subcontracting_order":
#                     subcontracting_orders = frappe.db.get_list("Subcontracting Order",
#                                                                filters={"purchase_order": task["po_name"]},
#                                                                fields=["name"])

#                     for so in subcontracting_orders:
#                         supplied_items = frappe.db.get_all("Subcontracting Order Supplied Item",
#                                                            filters={"parent": so.name, "main_item_code": task['filter_field']},
#                                                            fields=["supplied_qty", "consumed_qty", "stock_uom"])

#                         total_supplied = sum(item.supplied_qty for item in supplied_items)
#                         total_consumed = sum(item.consumed_qty for item in supplied_items)

#                         task["item_dict"]["supplied_qty"] += total_supplied
#                         task["item_dict"]["consumed_qty"] += total_consumed
#                         task["item_dict"]["rm_balance_qty"] = round(total_supplied - total_consumed, 3)
#                         task["item_dict"]["rm_received_qty"] = round(total_consumed, 3)

#                         if supplied_items and task["item_dict"].get("fg_item"):
#                             task["item_dict"]["uom"] = supplied_items[0].stock_uom

#                     # ✅ Skip completed items (optional: make configurable)
#                     if task["item_dict"]["pending_qty"] <= 0:
#                         continue

#                     data.append(task["item_dict"])
#                     processed_items.add(item_key)

#         return data
#     else:
#         frappe.msgprint("No filters provided.")




# import frappe
# from frappe.utils import getdate, date_diff
# from datetime import datetime
# from collections import deque

# @frappe.whitelist()
# def get_data(filters=None):
#     if filters:
#         data = []
#         purchase_orders = frappe.db.get_list(
#             'Purchase Order',
#             filters=filters,
#             fields=['transaction_date', 'name', 'po_type', 'supplier',
#                     'schedule_date', 'contact_email', 'uom'],
#             order_by='transaction_date desc'
#         )

#         for po in purchase_orders:
#             po_dict = dict(po)
#             if po_dict.get('transaction_date') and po_dict.get('schedule_date'):
#                 transaction_date = getdate(po_dict['transaction_date'])
#                 schedule_date = getdate(po_dict['schedule_date'])

#                 po_dict['lead_time_days'] = date_diff(schedule_date, transaction_date)
#                 po_dict['formatted_transaction_date'] = transaction_date.strftime('%d-%m-%Y')
#                 po_dict['number_of_days_from_po'] = (datetime.now().date() - transaction_date).days + 1
#             else:
#                 po_dict['formatted_transaction_date'] = None
#                 po_dict['number_of_days_from_po'] = None

#             purchase_order_doc = frappe.get_doc("Purchase Order", po_dict["name"])
#             items = purchase_order_doc.items

#             processing_queue = deque()
#             processed_items = set()

#             for item in items:
#                 item_dict = dict(po_dict)
#                 item_dict["item_name"] = item.item_name
#                 item_dict["item_code"] = item.item_code
#                 item_dict["qty"] = item.qty or 0
#                 item_dict["fg_item"] = item.fg_item
#                 item_dict["uom"] = item.uom

#                 filter_field = item.fg_item if item.fg_item else item.item_code

#                 item_dict.update({
#                     "purchase_receipt": None,
#                     "total_accepted_qty": 0,
#                     "total_rework": 0,
#                     "total_reject": 0,
#                     "total_received_qty": 0,
#                     "pending_qty": item.qty or 0,
#                     "supplied_qty": 0,
#                     "consumed_qty": 0,
#                     "rm_balance_qty": 0,
#                     "rm_received_qty": 0
#                 })

#                 if po_dict.get('po_type') == 'Sub-Contract':
#                     processing_queue.append({
#                         "type": "subcontracting_receipt",
#                         "po_name": po_dict["name"],
#                         "filter_field": filter_field,
#                         "item_code": item.item_code,
#                         "item_qty": item.qty or 0,
#                         "item_dict": item_dict
#                     })
#                 else:
#                     processing_queue.append({
#                         "type": "purchase_receipt",
#                         "po_name": po_dict["name"],
#                         "filter_field": filter_field,
#                         "item_code": item.item_code,
#                         "item_qty": item.qty or 0,
#                         "item_dict": item_dict
#                     })

#                 processing_queue.append({
#                     "type": "subcontracting_order",
#                     "po_name": po_dict["name"],
#                     "filter_field": filter_field,
#                     "item_code": item.item_code,
#                     "item_qty": item.qty or 0,
#                     "item_dict": item_dict
#                 })

#             while processing_queue:
#                 task = processing_queue.popleft()
#                 item_key = f"{task['item_code']}-{task['po_name']}"

#                 if item_key in processed_items:
#                     continue

#                 if task["type"] == "purchase_receipt":
#                     purchase_receipts = frappe.db.get_list(
#                         "Purchase Receipt",
#                         filters={"purchase_order": task["po_name"], "docstatus": 1},
#                         fields=["name"]
#                     )
#                     for pr in purchase_receipts:
#                         pr_doc = frappe.get_doc("Purchase Receipt", pr.name)
#                         for pr_item in pr_doc.items:
#                             if pr_item.item_code == task["item_code"]:
#                                 task["item_dict"]["total_received_qty"] += pr_item.qty or 0

#                                 qa_inspections = frappe.db.get_list(
#                                     "QA Inspection",
#                                     filters={
#                                         "reference_name": pr.name,
#                                         "item_code": task["item_code"],
#                                         "docstatus": 1
#                                     },
#                                     fields=["total_accepted_qty", "total_rework", "total_reject"]
#                                 )
#                                 for qa in qa_inspections:
#                                     task["item_dict"]["total_accepted_qty"] += qa.total_accepted_qty or 0
#                                     task["item_dict"]["total_rework"] += qa.total_rework or 0
#                                     task["item_dict"]["total_reject"] += qa.total_reject or 0

#                     task["item_dict"]["pending_qty"] = max(
#                         0, (task["item_qty"] or 0) - (task["item_dict"]["total_received_qty"] or 0)
#                     )

#                 elif task["type"] == "subcontracting_receipt":
#                     subcontracting_orders = frappe.db.get_list(
#                         "Subcontracting Order",
#                         filters={"purchase_order": task["po_name"]},
#                         fields=["name"]
#                     )
#                     so_names = [so.name for so in subcontracting_orders]

#                     subcontracting_receipts = frappe.db.get_list(
#                         "Subcontracting Receipt",
#                         filters={"subcontracting_order": ["in", so_names], "docstatus": 1},
#                         fields=["name"]
#                     )
#                     for sr in subcontracting_receipts:
#                         sr_doc = frappe.get_doc("Subcontracting Receipt", sr.name)
#                         for sr_item in sr_doc.items:
#                             if sr_item.item_code == task["filter_field"]:
#                                 task["item_dict"]["total_received_qty"] += sr_item.qty or 0

#                                 qa_inspections = frappe.db.get_list(
#                                     "QA Inspection",
#                                     filters={
#                                         "reference_name": sr.name,
#                                         "item_code": task["filter_field"],
#                                         "docstatus": 1
#                                     },
#                                     fields=["total_accepted_qty", "total_rework", "total_reject"]
#                                 )
#                                 for qa in qa_inspections:
#                                     task["item_dict"]["total_accepted_qty"] += qa.total_accepted_qty or 0
#                                     task["item_dict"]["total_rework"] += qa.total_rework or 0
#                                     task["item_dict"]["total_reject"] += qa.total_reject or 0

#                     task["item_dict"]["pending_qty"] = max(
#                         0, (task["item_qty"] or 0) - (task["item_dict"]["total_received_qty"] or 0)
#                     )

#                 elif task["type"] == "subcontracting_order":
#                     subcontracting_orders = frappe.db.get_list(
#                         "Subcontracting Order",
#                         filters={"purchase_order": task["po_name"]},
#                         fields=["name"]
#                     )
#                     for so in subcontracting_orders:
#                         supplied_items = frappe.db.get_all(
#                             "Subcontracting Order Supplied Item",
#                             filters={"parent": so.name, "main_item_code": task['filter_field']},
#                             fields=["supplied_qty", "consumed_qty", "stock_uom"]
#                         )
#                         total_supplied = sum(item.supplied_qty or 0 for item in supplied_items)
#                         total_consumed = sum(item.consumed_qty or 0 for item in supplied_items)

#                         task["item_dict"]["supplied_qty"] += total_supplied
#                         task["item_dict"]["consumed_qty"] += total_consumed
#                         task["item_dict"]["rm_balance_qty"] = total_supplied - total_consumed
#                         # ✅ RM Received Qty = total consumed qty
#                         task["item_dict"]["rm_received_qty"] = total_consumed

#                         if supplied_items and task["item_dict"].get("fg_item"):
#                             task["item_dict"]["uom"] = supplied_items[0].stock_uom

#                     if task["item_dict"]["pending_qty"] <= 0:
#                         continue

#                     data.append(task["item_dict"])
#                     processed_items.add(item_key)

#         return data
#     else:
#         frappe.msgprint("No filters provided.")



import frappe, json
from frappe.utils import getdate, date_diff
from datetime import datetime

@frappe.whitelist()
def get_data(filters=None):
    if not filters:
        frappe.msgprint("No filters provided.")
        return []

    # Ensure filters is a dict
    if isinstance(filters, str):
        filters = json.loads(filters)

    # -------------------------------
    # Build dynamic WHERE conditions
    # -------------------------------
    conditions = []
    values = {}
    for key, val in filters.items():
        if isinstance(val, list):
            op = (val[0] or "").lower()
            if op == "between" and isinstance(val[1], list) and len(val[1]) == 2:
                conditions.append(f"po.{key} BETWEEN %({key}_from)s AND %({key}_to)s")
                values[f"{key}_from"] = val[1][0]
                values[f"{key}_to"] = val[1][1]
            elif op == "in" and isinstance(val[1], list):
                placeholders = ", ".join([f"%({key}_{i})s" for i in range(len(val[1]))])
                conditions.append(f"po.{key} IN ({placeholders})")
                for i, v in enumerate(val[1]):
                    values[f"{key}_{i}"] = v
            elif op in (">=", "<=", ">", "<", "!=") and len(val) > 1:
                conditions.append(f"po.{key} {op} %({key})s")
                values[key] = val[1]
        else:
            conditions.append(f"po.{key} = %({key})s")
            values[key] = val

    condition_sql = " AND ".join(conditions) if conditions else "1=1"

    # --------------------------------
    # Base fetch: PO + PO Item (one SQL)
    # --------------------------------
    base_query = f"""
        SELECT 
            po.name as po_name,
            po.transaction_date,
            po.schedule_date,
            po.po_type,
            po.supplier,
            po.contact_email,
            po.status,
            poi.item_code,
            poi.item_name,
            poi.fg_item,
            poi.qty,
            poi.uom
        FROM `tabPurchase Order` po
        INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
        WHERE {condition_sql}
        ORDER BY po.transaction_date DESC
    """
    rows = frappe.db.sql(base_query, values, as_dict=True)

    data = []

    for row in rows:
        # Dates
        if row.transaction_date and row.schedule_date:
            transaction_date = getdate(row.transaction_date)
            schedule_date = getdate(row.schedule_date)
            row["lead_time_days"] = date_diff(schedule_date, transaction_date)
            row["formatted_transaction_date"] = transaction_date.strftime("%d-%m-%Y")
            row["number_of_days_from_po"] = (datetime.now().date() - transaction_date).days + 1
        else:
            row["lead_time_days"] = None
            row["formatted_transaction_date"] = None
            row["number_of_days_from_po"] = None

        # Initialize fields
        row["purchase_receipt"]   = None
        row["total_accepted_qty"] = 0
        row["total_rework"]       = 0
        row["total_reject"]       = 0
        row["total_received_qty"] = 0
        row["pending_qty"]        = row.qty or 0
        row["supplied_qty"]       = 0
        row["consumed_qty"]       = 0
        row["rm_balance_qty"]     = 0
        row["rm_received_qty"]    = 0

        # For subcontracting, finished good code can be fg_item; fallback to item_code
        filter_field = row.fg_item or row.item_code
        row["fg_item_display"] = filter_field  # use this in template if you want a guaranteed display

        # -----------------------------------------
        # Aggregate quantities depending on PO type
        # -----------------------------------------
        if row.po_type == "Sub-Contract":
            # Subcontracting Receipts (FG receipt)
            sr_sum = frappe.db.sql(
                """
                SELECT SUM(sri.qty) AS qty
                FROM `tabSubcontracting Receipt Item` sri
                INNER JOIN `tabSubcontracting Receipt` sr ON sr.name = sri.parent
                WHERE sr.docstatus = 1
                  AND sri.item_code = %s
                  AND sri.subcontracting_order IN (
                      SELECT name FROM `tabSubcontracting Order`
                      WHERE purchase_order = %s
                  )
                """,
                (filter_field, row.po_name),
                as_dict=True,
            )
            if sr_sum and sr_sum[0].qty:
                row["total_received_qty"] = sr_sum[0].qty or 0

            # QA against those SRs
            qa_sr = frappe.db.sql(
                """
                SELECT 
                    SUM(total_accepted_qty) AS acc,
                    SUM(total_rework)       AS rew,
                    SUM(total_reject)       AS rej
                FROM `tabQA Inspection`
                WHERE docstatus = 1
                  AND item_code = %s
                  AND reference_name IN (
                      SELECT sr.name
                      FROM `tabSubcontracting Receipt` sr
                      INNER JOIN `tabSubcontracting Receipt Item` sri ON sri.parent = sr.name
                      WHERE sr.docstatus = 1
                        AND sri.subcontracting_order IN (
                            SELECT name FROM `tabSubcontracting Order`
                            WHERE purchase_order = %s
                        )
                  )
                """,
                (filter_field, row.po_name),
                as_dict=True,
            )
            if qa_sr and qa_sr[0]:
                row["total_accepted_qty"] = qa_sr[0].acc or 0
                row["total_rework"]       = qa_sr[0].rew or 0
                row["total_reject"]       = qa_sr[0].rej or 0

            # RM supplied/consumed from SO Supplied Items
            so_rm = frappe.db.sql(
                """
                SELECT 
                    COALESCE(SUM(sosi.supplied_qty), 0) AS supplied,
                    COALESCE(SUM(sosi.consumed_qty), 0) AS consumed,
                    MAX(sosi.stock_uom)                 AS stock_uom
                FROM `tabSubcontracting Order Supplied Item` sosi
                WHERE sosi.main_item_code = %s
                  AND sosi.parent IN (
                      SELECT name FROM `tabSubcontracting Order`
                      WHERE purchase_order = %s
                  )
                """,
                (filter_field, row.po_name),
                as_dict=True,
            )
            if so_rm and so_rm[0]:
                row["supplied_qty"]    = so_rm[0].supplied or 0
                row["consumed_qty"]    = so_rm[0].consumed or 0
                row["rm_balance_qty"]  = (row["supplied_qty"] - row["consumed_qty"])
                row["rm_received_qty"] = row["consumed_qty"]   # as per your logic
                # Optional: if you want to reflect RM UOM when FG set
                if row.get("fg_item") and so_rm[0].stock_uom:
                    row["uom"] = so_rm[0].stock_uom

        else:
            # Normal purchase (PR + QA)
            pr_sum = frappe.db.sql(
                """
                SELECT SUM(pri.qty) AS qty
                FROM `tabPurchase Receipt Item` pri
                INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
                WHERE pr.purchase_order = %s
                  AND pr.docstatus = 1
                  AND pri.item_code = %s
                """,
                (row.po_name, row.item_code),
                as_dict=True,
            )
            if pr_sum and pr_sum[0].qty:
                row["total_received_qty"] = pr_sum[0].qty or 0

            qa_pr = frappe.db.sql(
                """
                SELECT 
                    SUM(total_accepted_qty) AS acc,
                    SUM(total_rework)       AS rew,
                    SUM(total_reject)       AS rej
                FROM `tabQA Inspection`
                WHERE docstatus = 1
                  AND item_code = %s
                  AND reference_name IN (
                      SELECT name FROM `tabPurchase Receipt`
                      WHERE purchase_order = %s AND docstatus = 1
                  )
                """,
                (row.item_code, row.po_name),
                as_dict=True,
            )
            if qa_pr and qa_pr[0]:
                row["total_accepted_qty"] = qa_pr[0].acc or 0
                row["total_rework"]       = qa_pr[0].rew or 0
                row["total_reject"]       = qa_pr[0].rej or 0

        # Pending
        ordered = row.qty or 0
        received = row["total_received_qty"] or 0
        row["pending_qty"] = max(0, ordered - received)

        # Append if pending > 0 (keeps behavior aligned with your page intent)
        if row["pending_qty"] > 0:
            data.append(row)

    return data






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

