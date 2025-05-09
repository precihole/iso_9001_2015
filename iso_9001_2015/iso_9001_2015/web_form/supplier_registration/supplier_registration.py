import frappe
import requests
import uuid


# # This function is called when Frappe renders the page context
def get_context(context):
    pass

# # app/api_token_updater.py
# def on_refresh(self):
#     frappe.msgprint("Updating GSP Token...")
#     try:
#         url = "https://gsp.adaequare.com/gsp/authenticate?grant_type=token"

#         headers = {
#             "Content-Type": "application/json",
#             "accept": "application/json",
#         }

#         response = requests.post(url, headers=headers)
#         response.raise_for_status()

#         data = response.json()
#         access_token = data.get("access_token")

#         if not access_token:
#             frappe.throw("No access token received from GSP API")

#         iso_settings = frappe.get_single("ISO Settings")
#         iso_settings.authorization = access_token
#         iso_settings.save()
#         frappe.db.commit()

#         frappe.logger().info("GSP Token updated successfully.")

#     except Exception:
#         frappe.log_error(frappe.get_traceback(), "GSP Token Update Failed")




@frappe.whitelist()
def fetch_gst_data(gst_no):
    # Generate a random 8-character string for request ID
    random_string = str(uuid.uuid4()).replace('-', '')[:8]

    # API endpoint with GST number
    url = f"https://gsp.adaequare.com/test/enriched/ewb/master/GetGSTINDetails?GSTIN={gst_no}"

    # Fetch token from ISO Settings doctype
    token = frappe.db.get_single_value('ISO Settings', 'authorization')

    # Prepare headers for the API request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Username": frappe.db.get_single_value('ISO Settings', 'username'),
        "Password": frappe.db.get_single_value('ISO Settings', 'password'),
        "gstin": "05AAACG2115R1ZN",  # Static GSTIN (as per your example)
        "requestid": random_string
    }
    
    try:
        # Send GET request to the GST API
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Return the API response JSON directly
            result = response.json()
            return result
        else:
            # Return error message if API response code is not 200
            return {"error": f"API request failed with status code {response.status_code}"}
    except requests.exceptions.RequestException as e:
        # Log error if request fails and return error message
        frappe.log_error(f"GST API call failed: {str(e)}", "GST API Error")
        return {"error": "Failed to connect to GST API"}
