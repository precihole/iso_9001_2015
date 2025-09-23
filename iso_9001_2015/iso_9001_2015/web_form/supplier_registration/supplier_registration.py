import frappe
import requests
import uuid
from frappe.utils import add_days, nowdate, getdate, today

BASE_URL = "https://gsp.adaequare.com"  # ✅ correct spelling

def get_context(context):
    pass

def get_valid_token():
    """Return a valid token (refresh if expired, missing, or expiring in <=5 days)."""
    iso = frappe.get_single("ISO Setting")
    needs_refresh = (
        not iso.authorization
        or not iso.expiry_date
        or (getdate(iso.expiry_date) - getdate(today())).days <= 5
    )
    if needs_refresh:
        update_gsp_token()
    return frappe.db.get_single_value("ISO Setting", "authorization")


def update_gsp_token():
    """Authenticate with Adaequare and store access_token + expiry_date."""
    iso = frappe.get_single("ISO Setting")
    url = f"{BASE_URL}/gsp/authenticate?grant_type=token"

    headers = {
        "gspappid": iso.gspappid,
        "gspappsecret": iso.gspappsecret,
        "accept": "application/json",
    }

    try:
        resp = requests.post(url, headers=headers, timeout=30)
        frappe.logger().info(f"GSP auth status={resp.status_code}, body={resp.text}")
        resp.raise_for_status()
        data = resp.json()

        token = data.get("access_token")
        if not token:
            frappe.throw(f"No access_token in response: {data}")

        iso.authorization = token

        expires_in = data.get("expires_in")
        if isinstance(expires_in, int):
            days = max(1, expires_in // 86400 - 1)
            iso.expiry_date = add_days(nowdate(), days)
        else:
            iso.expiry_date = add_days(nowdate(), 25)

        iso.save(ignore_permissions=True)
        frappe.db.commit()

        # ✅ Force cache clear + reload
        frappe.clear_cache(doctype="ISO Setting")
        iso.reload()

    except Exception:
        frappe.log_error(frappe.get_traceback(), "GSP Token Update Failed")
        frappe.throw(
            "GSP Token Update Failed. Check gspappid/gspappsecret and your internet/DNS."
        )


@frappe.whitelist()
def fetch_gst_data(gst_no: str):
    """Fetch GST details from Adaequare Enriched EWB API."""
    token = get_valid_token()
    iso = frappe.get_single("ISO Setting")

    # Use test environment like your Postman screenshot; change to prod when ready.
    url = f"{BASE_URL}/test/enriched/ewb/master/GetGSTINDetails?GSTIN={gst_no}"
    req_id = uuid.uuid4().hex[:12]

    headers = {
        "Content-Type": "application/json",
        "username": iso.username,
        "password": iso.password,
        "gstin": iso.username,
        "requestid": req_id,
        "Authorization": f"Bearer {token}",  # ✅ don't forget the 'Bearer ' prefix
    }

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        frappe.logger().info(f"GST GET status={resp.status_code}, body={resp.text[:500]}")
        if resp.status_code == 200:
            data = resp.json()
            return {"result": data.get("result")}
        else:
            frappe.log_error(resp.text, "GST API Error")
            return {"error": f"API failed with status code {resp.status_code}", "details": resp.text}
    except requests.exceptions.RequestException as e:
        frappe.log_error(str(e), "GST API Error")
        return {"error": "Failed to connect to GST API"}
