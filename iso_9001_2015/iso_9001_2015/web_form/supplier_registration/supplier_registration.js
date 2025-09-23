frappe.ready(function() {
    frappe.web_form.on('gst_no', (field, value) => {
        if (value) {
            console.log("GST No entered:", value);
            frappe.call({
                method: "iso_9001_2015.iso_9001_2015.web_form.supplier_registration.supplier_registration.fetch_gst_data",
                args: {
                    gst_no: value
                },
                callback: function(response) {
                    console.log("API Response:", response.message);

                    if (response.message && response.message.result) {
                        let data = response.message.result;

                        const stateGSTCodeToName = {
                            '1': 'Jammu & Kashmir',
                            '2': 'Himachal Pradesh',
                            '3': 'Punjab',
                            '4': 'Chandigarh',
                            '5': 'Uttarakhand',
                            '6': 'Haryana',
                            '7': 'Delhi',
                            '8': 'Rajasthan',
                            '9': 'Uttar Pradesh',
                            '10': 'Bihar',
                            '11': 'Sikkim',
                            '12': 'Arunachal Pradesh',
                            '13': 'Nagaland',
                            '14': 'Manipur',
                            '15': 'Mizoram',
                            '16': 'Tripura',
                            '17': 'Meghalaya',
                            '18': 'Assam',
                            '19': 'West Bengal',
                            '20': 'Jharkhand',
                            '21': 'Odisha',
                            '22': 'Chhattisgarh',
                            '23': 'Madhya Pradesh',
                            '24': 'Gujarat',
                            '25': 'Daman and Diu',
                            '26': 'Dadra and Nagar Haveli',
                            '27': 'Maharashtra',
                            '28': 'Goa',
                            '29': 'Karnataka',
                            '30': 'Lakshadweep',
                            '31': 'Kerala',
                            '32': 'Tamil Nadu',
                            '33': 'Puducherry',
                            '34': 'Andaman and Nicobar Islands',
                            '35': 'Telangana',
                            '36': 'Andhra Pradesh',
                            '37': 'Ladakh'
                        };


                        let stateName = stateGSTCodeToName[data.stateCode];

                        frappe.web_form.set_value("state", stateName || 'Unknown State');
                        frappe.web_form.set_value("office_address_1", data.address1 || '');
                        frappe.web_form.set_value("office_address_2", data.address2 || '');
                        frappe.web_form.set_value("state_gst_no", data.stateCode || '');
                        frappe.web_form.set_value("company", data.tradeName || '');
                    } else if (response.message && response.message.error) {
                        frappe.msgprint(response.message.error);
                    } else {
                        frappe.msgprint("Invalid GST Number or empty response.");
                    }
                }
            });
        }
    });
});


