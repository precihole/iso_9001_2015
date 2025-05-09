// Copyright (c) 2024, Kiran and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Supplier Registration", {
// 	refresh(frm) {

// 	},
// });






frappe.ui.form.on('Supplier Registration', {
    // Trigger function when 'gst_no' field is modified
    gst_no: function(frm) {
        // Check if the gst_no field is populated
        if (frm.doc.gst_no) {
            // Make a server call to fetch GST details using the provided gst_no
            frappe.call({
                method: "iso_9001_2015.iso_9001_2015.doctype.supplier_registration.supplier_registration.get_gst_details", // The server-side method to fetch GST details
                args: { gst_no: frm.doc.gst_no }, // Passing the gst_no entered by the user
                callback: function(response) {
                    // If response contains valid data, set the office_address field with the GST status
                    if (response.message && response.message.data && response.message.data.details) {
                        frm.set_value('office_address', response.message.data.details.gstinstatus); // Update the 'office_address' field with GST status
                    } else {
                        // Show an error message if the response is invalid
                        frappe.msgprint(__('Invalid response from GST API.'));
                    }
                },
                error: function(err) {
                    // Show an error message if there is an issue with the API request
                    frappe.msgprint(__('Error fetching GST details. Check it again.'));
                }
            });
        }
    }
});
