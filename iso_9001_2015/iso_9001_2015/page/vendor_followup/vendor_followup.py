# import frappe, json
# from frappe.utils import getdate, date_diff
# from datetime import datetime

# @frappe.whitelist()
# def get_data(filters=None):
#     if not filters:
#         frappe.msgprint("No filters provided.")
#         return []

#     # Ensure filters is a dict
#     if isinstance(filters, str):
#         filters = json.loads(filters)

#     # -------------------------------
#     # Build dynamic WHERE conditions
#     # -------------------------------
#     conditions = []
#     values = {}
#     for key, val in filters.items():
#         if isinstance(val, list):
#             op = (val[0] or "").lower()
#             if op == "between" and isinstance(val[1], list) and len(val[1]) == 2:
#                 conditions.append(f"po.{key} BETWEEN %({key}_from)s AND %({key}_to)s")
#                 values[f"{key}_from"] = val[1][0]
#                 values[f"{key}_to"] = val[1][1]
#             elif op == "in" and isinstance(val[1], list):
#                 placeholders = ", ".join([f"%({key}_{i})s" for i in range(len(val[1]))])
#                 conditions.append(f"po.{key} IN ({placeholders})")
#                 for i, v in enumerate(val[1]):
#                     values[f"{key}_{i}"] = v
#             elif op in (">=", "<=", ">", "<", "!=") and len(val) > 1:
#                 conditions.append(f"po.{key} {op} %({key})s")
#                 values[key] = val[1]
#         else:
#             conditions.append(f"po.{key} = %({key})s")
#             values[key] = val

#     condition_sql = " AND ".join(conditions) if conditions else "1=1"

#     # --------------------------------
#     # Base fetch: PO + PO Item (one SQL)
#     # --------------------------------
#     # base_query = f"""
#     #     SELECT 
#     #         po.name as po_name,
#     #         po.transaction_date,
#     #         po.schedule_date,
#     #         po.po_type,
#     #         po.supplier,
#     #         po.contact_email,
#     #         po.status,
#     #         poi.item_code,
#     #         poi.item_name,
#     #         poi.fg_item,
#     #         poi.qty,
#     #         poi.uom
#     #     FROM `tabPurchase Order` po
#     #     INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
#     #     WHERE {condition_sql}
#     #     ORDER BY po.transaction_date DESC
#     # """

#     base_query = f"""
#         SELECT 
#             po.name as po_name,
#             po.transaction_date,
#             po.schedule_date,
#             po.po_type,
#             po.supplier,
#             po.contact_email,
#             po.status,
#             poi.item_code,
#             poi.item_name,
#             # (
#             #     SELECT COUNT(*) 
#             #     FROM `tabVendor Followup Log` vfl
#             #     WHERE vfl.purchase_order = po.name
#             #     AND vfl.item_code = poi.item_code
#             # ) AS followup_count,
#             (
#                 SELECT COUNT(*) 
#                 FROM `tabVendor Followup Log` vfl
#                 WHERE vfl.purchase_order = po.name
#                 AND vfl.item_code = poi.item_code
#             ) AS followup_count,

#             poi.fg_item,
#             poi.qty,
#             poi.uom
#         FROM `tabPurchase Order` po
#         INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
#         WHERE {condition_sql}
#         ORDER BY po.transaction_date DESC
#     """

#     rows = frappe.db.sql(base_query, values, as_dict=True)

#     data = []

#     for row in rows:
#         # Dates
#         if row.transaction_date and row.schedule_date:
#             transaction_date = getdate(row.transaction_date)
#             schedule_date = getdate(row.schedule_date)
#             row["lead_time_days"] = date_diff(schedule_date, transaction_date)
#             row["formatted_transaction_date"] = transaction_date.strftime("%d-%m-%Y")
#             row["number_of_days_from_po"] = (datetime.now().date() - transaction_date).days + 1
#         else:
#             row["lead_time_days"] = None
#             row["formatted_transaction_date"] = None
#             row["number_of_days_from_po"] = None

#         # Initialize fields
#         row["purchase_receipt"]   = None
#         row["total_accepted_qty"] = 0
#         row["total_rework"]       = 0
#         row["total_reject"]       = 0
#         row["total_received_qty"] = 0
#         row["pending_qty"]        = row.qty or 0
#         row["supplied_qty"]       = 0
#         row["consumed_qty"]       = 0
#         row["rm_balance_qty"]     = 0
#         row["rm_received_qty"]    = 0

#         # For subcontracting, finished good code can be fg_item; fallback to item_code
#         filter_field = row.fg_item or row.item_code
#         row["fg_item_display"] = filter_field  # use this in template if you want a guaranteed display

#         # -----------------------------------------
#         # Aggregate quantities depending on PO type
#         # -----------------------------------------
#         if row.po_type == "Sub-Contract":
#             # Subcontracting Receipts (FG receipt)
#             sr_sum = frappe.db.sql(
#                 """
#                 SELECT SUM(sri.qty) AS qty
#                 FROM `tabSubcontracting Receipt Item` sri
#                 INNER JOIN `tabSubcontracting Receipt` sr ON sr.name = sri.parent
#                 WHERE sr.docstatus = 1
#                   AND sri.item_code = %s
#                   AND sri.subcontracting_order IN (
#                       SELECT name FROM `tabSubcontracting Order`
#                       WHERE purchase_order = %s
#                   )
#                 """,
#                 (filter_field, row.po_name),
#                 as_dict=True,
#             )
#             if sr_sum and sr_sum[0].qty:
#                 row["total_received_qty"] = sr_sum[0].qty or 0

#             # QA against those SRs
#             qa_sr = frappe.db.sql(
#                 """
#                 SELECT 
#                     SUM(total_accepted_qty) AS acc,
#                     SUM(total_rework)       AS rew,
#                     SUM(total_reject)       AS rej
#                 FROM `tabQA Inspection`
#                 WHERE docstatus = 1
#                   AND item_code = %s
#                   AND reference_name IN (
#                       SELECT sr.name
#                       FROM `tabSubcontracting Receipt` sr
#                       INNER JOIN `tabSubcontracting Receipt Item` sri ON sri.parent = sr.name
#                       WHERE sr.docstatus = 1
#                         AND sri.subcontracting_order IN (
#                             SELECT name FROM `tabSubcontracting Order`
#                             WHERE purchase_order = %s
#                         )
#                   )
#                 """,
#                 (filter_field, row.po_name),
#                 as_dict=True,
#             )
#             if qa_sr and qa_sr[0]:
#                 row["total_accepted_qty"] = qa_sr[0].acc or 0
#                 row["total_rework"]       = qa_sr[0].rew or 0
#                 row["total_reject"]       = qa_sr[0].rej or 0

#             # RM supplied/consumed from SO Supplied Items
#             so_rm = frappe.db.sql(
#                 """
#                 SELECT 
#                     COALESCE(SUM(sosi.supplied_qty), 0) AS supplied,
#                     COALESCE(SUM(sosi.consumed_qty), 0) AS consumed,
#                     MAX(sosi.stock_uom)                 AS stock_uom
#                 FROM `tabSubcontracting Order Supplied Item` sosi
#                 WHERE sosi.main_item_code = %s
#                   AND sosi.parent IN (
#                       SELECT name FROM `tabSubcontracting Order`
#                       WHERE purchase_order = %s
#                   )
#                 """,
#                 (filter_field, row.po_name),
#                 as_dict=True,
#             )
#             if so_rm and so_rm[0]:
#                 row["supplied_qty"]    = so_rm[0].supplied or 0
#                 row["consumed_qty"]    = so_rm[0].consumed or 0
#                 row["rm_balance_qty"]  = (row["supplied_qty"] - row["consumed_qty"])
#                 row["rm_received_qty"] = row["consumed_qty"]   # as per your logic
#                 # Optional: if you want to reflect RM UOM when FG set
#                 if row.get("fg_item") and so_rm[0].stock_uom:
#                     row["uom"] = so_rm[0].stock_uom

#         else:
#             # Normal purchase (PR + QA)
#             pr_sum = frappe.db.sql(
#                 """
#                 SELECT SUM(pri.qty) AS qty
#                 FROM `tabPurchase Receipt Item` pri
#                 INNER JOIN `tabPurchase Receipt` pr ON pr.name = pri.parent
#                 WHERE pr.purchase_order = %s
#                   AND pr.docstatus = 1
#                   AND pri.item_code = %s
#                 """,
#                 (row.po_name, row.item_code),
#                 as_dict=True,
#             )
#             if pr_sum and pr_sum[0].qty:
#                 row["total_received_qty"] = pr_sum[0].qty or 0

#             qa_pr = frappe.db.sql(
#                 """
#                 SELECT 
#                     SUM(total_accepted_qty) AS acc,
#                     SUM(total_rework)       AS rew,
#                     SUM(total_reject)       AS rej
#                 FROM `tabQA Inspection`
#                 WHERE docstatus = 1
#                   AND item_code = %s
#                   AND reference_name IN (
#                       SELECT name FROM `tabPurchase Receipt`
#                       WHERE purchase_order = %s AND docstatus = 1
#                   )
#                 """,
#                 (row.item_code, row.po_name),
#                 as_dict=True,
#             )
#             if qa_pr and qa_pr[0]:
#                 row["total_accepted_qty"] = qa_pr[0].acc or 0
#                 row["total_rework"]       = qa_pr[0].rew or 0
#                 row["total_reject"]       = qa_pr[0].rej or 0

#         # Pending
#         ordered = row.qty or 0
#         received = row["total_received_qty"] or 0
#         row["pending_qty"] = max(0, ordered - received)

#         # Append if pending > 0 (keeps behavior aligned with your page intent)
#         if row["pending_qty"] > 0:
#             data.append(row)

#     return data



# # @frappe.whitelist()
# # def send_supplier_email(supplier, email, po_name, schedule_date, item_name, item_code):
# #     """Send follow-up email and record it in Vendor Followup Log."""
# #     user_fullname = frappe.get_value("User", frappe.session.user, "full_name") or "ERP User"

# #     subject = f"Follow Up: Purchase Order {po_name}"
# #     message = f"""
# #     Dear {supplier},<br><br>
# #     This is a reminder regarding Item <b>{item_name}</b> from Purchase Order <b>{po_name}</b>,
# #     scheduled for delivery on <b>{schedule_date}</b>.<br><br>
# #     Kindly confirm the delivery status.<br><br>
# #     Best regards,<br>
# #     {user_fullname}<br>
# #     """

# #     try:
# #         frappe.sendmail(
# #             recipients=email,
# #             subject=subject,
# #             message=message,
# #         )

# #         # ✅ Create follow-up log
# #         log = frappe.get_doc({
# #             "doctype": "Vendor Followup Log",
# #             "purchase_order": po_name,
# #             "item_code": item_code,       # ✅ fixed: correct field
# #             "supplier": supplier,
# #             "email": email,
# #             "followup_date": frappe.utils.now_datetime(),
# #             "sent_by": frappe.session.user,
# #         })
# #         log.insert(ignore_permissions=True)
# #         frappe.db.commit()

# #         # ✅ Count all followups
# #         count = frappe.db.sql("""
# #             SELECT COALESCE(COUNT(*), 0)
# #             FROM `tabVendor Followup Log`
# #             WHERE purchase_order = %s AND item_code = %s
# #         """, (po_name, item_code))[0][0]

# #         return {
# #             "message": "Follow-up email sent successfully!",
# #             "total_sent": count
# #         }

# #     except Exception as e:
# #         frappe.log_error(f"Failed to send email to {email}: {e}", "Vendor Followup Email Error")
# #         return {"message": f"Failed to send email: {e}", "total_sent": 0}

















# @frappe.whitelist()
# def get_data(filters=None):
#     if not filters:
#         frappe.msgprint("No filters provided.")
#         return []

#     if isinstance(filters, str):
#         filters = json.loads(filters)

#     conditions = []
#     values = {}
#     for key, val in filters.items():
#         if isinstance(val, list):
#             op = (val[0] or "").lower()
#             if op == "between" and isinstance(val[1], list) and len(val[1]) == 2:
#                 conditions.append(f"po.{key} BETWEEN %({key}_from)s AND %({key}_to)s")
#                 values[f"{key}_from"] = val[1][0]
#                 values[f"{key}_to"] = val[1][1]
#             elif op == "in" and isinstance(val[1], list):
#                 placeholders = ", ".join([f"%({key}_{i})s" for i in range(len(val[1]))])
#                 conditions.append(f"po.{key} IN ({placeholders})")
#                 for i, v in enumerate(val[1]):
#                     values[f"{key}_{i}"] = v
#             elif op in (">=", "<=", ">", "<", "!=") and len(val) > 1:
#                 conditions.append(f"po.{key} {op} %({key})s")
#                 values[key] = val[1]
#         else:
#             conditions.append(f"po.{key} = %({key})s")
#             values[key] = val

#     condition_sql = " AND ".join(conditions) if conditions else "1=1"

#     # ✅ Fixed: consistent item_name reference
#     base_query = f"""
#         SELECT 
#             po.name as po_name,
#             po.transaction_date,
#             po.schedule_date,
#             po.po_type,
#             po.supplier,
#             po.contact_email,
#             po.status,
#             poi.item_code,
#             poi.item_name,
#             (
#                 SELECT COUNT(*) 
#                 FROM `tabVendor Followup Log` vfl
#                 WHERE vfl.purchase_order = po.name
#                 AND vfl.item_name = poi.item_name
#             ) AS followup_count,
#             poi.fg_item,
#             poi.qty,
#             poi.uom
#         FROM `tabPurchase Order` po
#         INNER JOIN `tabPurchase Order Item` poi ON poi.parent = po.name
#         WHERE {condition_sql}
#         ORDER BY po.transaction_date DESC
#     """

#     rows = frappe.db.sql(base_query, values, as_dict=True)

   





















import frappe
import json
from frappe.utils import getdate, date_diff
from datetime import datetime


@frappe.whitelist()
def get_data(filters=None):
    """Fetch Purchase Order data, including item details, QA stats, RM, and persistent follow-up count."""
    if not filters:
        frappe.msgprint("No filters provided.")
        return []

    if isinstance(filters, str):
        filters = json.loads(filters)

    # -------------------------------
    # Dynamic WHERE conditions
    # -------------------------------
    conditions = []
    values = {}

    for key, val in filters.items():
        if isinstance(val, list):
            op = (val[0] or "").lower()
            if op == "between" and isinstance(val[1], list) and len(val[1]) == 2:
                conditions.append(f"po.{key} BETWEEN %({key}_from)s AND %({key}_to)s")
                values[f"{key}_from"], values[f"{key}_to"] = val[1]
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

    # -----------------------------------------------
    # Main query — get PO, PO Items, and Follow-up count
    # -----------------------------------------------
    base_query = f"""
        SELECT 
            po.name AS po_name,
            po.transaction_date,
            po.schedule_date,
            po.po_type,
            po.supplier,
            po.contact_email,
            po.status,
            poi.item_code,
            poi.item_name,
            # (
            #     SELECT COUNT(*) 
            #     FROM `tabVendor Followup Log` vfl
            #     WHERE vfl.purchase_order = po.name
            #     AND vfl.item_name = poi.item_name
            # ) AS followup_count,
            (
                SELECT COUNT(*) 
                FROM `tabVendor Followup Log` vfl
                WHERE vfl.purchase_order = po.name
                AND vfl.item_code = poi.item_code
            ) AS followup_count,

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

    # -----------------------------------------------
    # Post-processing each item row
    # -----------------------------------------------
    for row in rows:
        # Dates & lead time
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

        # Initialize metrics
        row["purchase_receipt"] = None
        row["total_accepted_qty"] = 0
        row["total_rework"] = 0
        row["total_reject"] = 0
        row["total_received_qty"] = 0
        row["pending_qty"] = row.qty or 0
        row["supplied_qty"] = 0
        row["consumed_qty"] = 0
        row["rm_balance_qty"] = 0
        row["rm_received_qty"] = 0

        filter_field = row.fg_item or row.item_code
        row["fg_item_display"] = filter_field

        # -----------------------------------------------
        # Sub-Contract PO Logic
        # -----------------------------------------------
        if row.po_type == "Sub-Contract":
            # Subcontracting Receipts
            sr_sum = frappe.db.sql(
                """
                SELECT SUM(sri.qty) AS qty
                FROM `tabSubcontracting Receipt Item` sri
                INNER JOIN `tabSubcontracting Receipt` sr ON sr.name = sri.parent
                WHERE sr.docstatus = 1
                  AND sri.item_code = %s
                  AND sri.subcontracting_order IN (
                      SELECT name FROM `tabSubcontracting Order` WHERE purchase_order = %s
                  )
                """,
                (filter_field, row.po_name),
                as_dict=True,
            )
            if sr_sum and sr_sum[0].qty:
                row["total_received_qty"] = sr_sum[0].qty or 0

            # QA against Subcontract Receipts
            qa_sr = frappe.db.sql(
                """
                SELECT 
                    SUM(total_accepted_qty) AS acc,
                    SUM(total_rework) AS rew,
                    SUM(total_reject) AS rej
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
                row["total_rework"] = qa_sr[0].rew or 0
                row["total_reject"] = qa_sr[0].rej or 0

            # RM (Supplied / Consumed)
            so_rm = frappe.db.sql(
                """
                SELECT 
                    COALESCE(SUM(sosi.supplied_qty), 0) AS supplied,
                    COALESCE(SUM(sosi.consumed_qty), 0) AS consumed,
                    MAX(sosi.stock_uom) AS stock_uom
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
                row["supplied_qty"] = so_rm[0].supplied or 0
                row["consumed_qty"] = so_rm[0].consumed or 0
                row["rm_balance_qty"] = (row["supplied_qty"] - row["consumed_qty"])
                row["rm_received_qty"] = row["consumed_qty"]
                if row.get("fg_item") and so_rm[0].stock_uom:
                    row["uom"] = so_rm[0].stock_uom

        # -----------------------------------------------
        # Normal PO Logic
        # -----------------------------------------------
        else:
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
                    SUM(total_rework) AS rew,
                    SUM(total_reject) AS rej
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
                row["total_rework"] = qa_pr[0].rew or 0
                row["total_reject"] = qa_pr[0].rej or 0

        # Pending Quantity
        ordered = row.qty or 0
        received = row["total_received_qty"] or 0
        row["pending_qty"] = max(0, ordered - received)

        if row["pending_qty"] > 0:
            data.append(row)

    return data


# ----------------------------------------------------
# SEND FOLLOW-UP EMAIL
# ----------------------------------------------------
@frappe.whitelist()
def send_supplier_email(supplier, email, po_name, schedule_date, item_name, item_code=None):
    """Send follow-up email and log it into Vendor Followup Log."""
    user_fullname = frappe.get_value("User", frappe.session.user, "full_name") or "ERP User"

    subject = f"Follow Up: Purchase Order {po_name}"
    message = f"""
    Dear {supplier},<br><br>
    This is a reminder regarding Item <b>{item_name}</b> from Purchase Order <b>{po_name}</b>,
    scheduled for delivery on <b>{schedule_date}</b>.<br><br>
    Kindly confirm the delivery status.<br><br>
    Best regards,<br>
    {user_fullname}<br>
    """

    try:
        frappe.sendmail(recipients=email, subject=subject, message=message, now=True)

        # Create follow-up log
        log = frappe.get_doc({
            "doctype": "Vendor Followup Log",
            "purchase_order": po_name,
            "item_code": item_code or "",
            "supplier": supplier,
            "email": email,
            "followup_date": frappe.utils.now_datetime(),
            "sent_by": frappe.session.user,
        })
        log.insert(ignore_permissions=True)
        frappe.db.commit()

        # Update persistent count
        count = frappe.db.sql("""
            SELECT COALESCE(COUNT(*), 0)
            FROM `tabVendor Followup Log`
            WHERE purchase_order = %s AND item_code = %s
        """, (po_name, item_code))[0][0]

        return {"message": "Follow-up email sent successfully!", "total_sent": count}

    except Exception as e:
        frappe.log_error(f"Failed to send email to {email}: {e}", "Vendor Followup Email Error")
        return {"message": f"Failed to send email: {e}", "total_sent": 0}
