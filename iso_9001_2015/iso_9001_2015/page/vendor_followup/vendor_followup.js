// frappe.pages["vendor-followup"].on_page_load = function (wrapper) {
//     var page = frappe.ui.make_app_page({
//         parent: wrapper,
//         title: "Vendor Follow-Up",
//         single_column: true,
//     });

//     let container = $('<div>').appendTo(page.body);

//     function load_data() {
//         let supplier = page.supplier_field.get_value();
//         let from_date = page.from_date_field.get_value();
//         let to_date = page.to_date_field.get_value();
//         let po_type = page.po_type_field.get_value();
//         let status = page.status_field.get_value();

//         get_data(supplier, from_date, to_date, po_type, status).then((supplierData) => {
//             render_data(supplierData);
//         }).catch((err) => {
//             console.log("Error fetching data:", err);
//         });
//     }

//     // Add filters
//     page.from_date_field = page.add_field({
//         fieldname: 'from_date',
//         label: __('From Date'),
//         fieldtype: 'Date',
//         reqd: 1   // make field required
//     });

//     page.to_date_field = page.add_field({
//         fieldname: 'to_date',
//         label: __('To Date'),
//         fieldtype: 'Date',
//         reqd: 1   // make field required
//     });

//     page.supplier_field = page.add_field({
//         fieldname: 'supplier',
//         label: __('Supplier'),
//         fieldtype: 'Link',
//         options: 'Supplier'
//     });

//     page.po_type_field = page.add_field({
//         fieldname: 'po_type',
//         label: __('PO Type'),
//         fieldtype: 'Select',
//         options: ["",'Capital', 'Consumable', 'Expense', 'Others', 'Return', 'Rework', 'Sub-Contract'].join('\n')
//     });

//     page.status_field = page.add_field({
//         fieldname: 'status',
//         label: __('Status'),
//         fieldtype: 'Select',
//         options: ["",'To Receive and Bill', 'To Bill'].join('\n')
//     });

//     // Add Search button
//     page.search_button = page.add_field({
//         fieldname: 'search',
//         label: __('Search'),
//         fieldtype: 'Button',
//         click: function () {
//             let from_date = page.from_date_field.get_value();
//             let to_date = page.to_date_field.get_value();

//             // Validation
//             if (!from_date || !to_date) {
//                 frappe.msgprint(__('From Date and To Date are mandatory.'));
//                 return;
//             }
//             load_data();
//         }
//     });

//     // Apply custom styles
//     page.search_button.$wrapper.addClass('btn custom-search-btn');
//     const style = document.createElement('style');
//     style.innerHTML = `
//         .custom-search-btn button {
//             background-color: #007bff;
//             color: white;
//             border: 1px solid #0056b3;
//             padding: 8px 16px;
//             border-radius: 6px;
//             font-weight: bold;
//             transition: all 0.3s ease;
//             box-shadow: 0px 4px 6px rgba(0, 123, 255, 0.3);
//         }

//         .custom-search-btn button:hover {
//             background-color: #0056b3;
//             color: white;
//             box-shadow: 0px 6px 10px rgba(0, 91, 187, 0.5);
//         }

//         /* Prevent default bootstrap blue focus/active styles */
//         .custom-search-btn button:focus,
//         .custom-search-btn button:active {
//             outline: none !important;
//             background-color: #007bff !important;
//             border: 1px solid #0056b3 !important;
//             color: white !important;
//             box-shadow: 0px 4px 6px rgba(0, 123, 255, 0.3) !important;
//             transform: none !important;
//         }
//     `;
//     document.head.appendChild(style);

//     function get_data(supplier, from_date, to_date, po_type, status) {
//         let filters = { docstatus: 1 };

//         if (supplier) filters["supplier"] = supplier;
//         if (from_date && to_date) {
//             filters["transaction_date"] = ["between", [from_date, to_date]];
//         } else if (to_date) {
//             filters["transaction_date"] = ["<=", to_date];
//         } else if (from_date) {
//             filters["transaction_date"] = [">=", from_date];
//         }

//         if (po_type) filters["po_type"] = po_type;
//         if (status) {
//             filters["status"] = status;
//         } else {
//             filters["status"] = ["in", ["To Receive and Bill", "To Receive"]];
//         }

//         return frappe.call({
//             method: 'iso_9001_2015.iso_9001_2015.page.vendor_followup.vendor_followup.get_data',
//             args: { filters: filters }
//         }).then((response) => response.message || []);
//     }

//     function render_data(data) {
//         data.forEach((item, index) => { item.index = index + 1; });
//         let html = frappe.render_template("vendor_followup", { purchase_orders: data });
//         container.html(html);

//         container.find('.msgprint-btn').click(function () {
//             var button = $(this);
//             var supplier = button.data('supplier');
//             var email = button.data('email');
//             var po_name = button.data('po');
//             var item_name = button.data('item_name') || button.attr('data-item-name') || '';
//             var schedule_date = button.data('schedule-date');

//             var user_fullname = frappe.session.user_fullname || "Your Name";  
//             var preview_message = `
//                 Dear ${supplier},<br><br>
//                 This is a reminder regarding Item <b>${item_name}</b> from Purchase Order <b>${po_name}</b>,
//                 scheduled for delivery on <b>${schedule_date}</b>.<br><br>
//                 Kindly confirm the delivery status.<br><br>
//                 Best regards,<br>
//                 ${user_fullname}<br>
//             `;

//             var d = new frappe.ui.Dialog({
//                 title: 'Send Follow-Up Email',
//                 fields: [
//                     { label: 'Supplier Name', fieldname: 'supplier_name', fieldtype: 'Data', default: supplier, read_only: 1 },
//                     { label: 'Supplier Email', fieldname: 'contact_email', fieldtype: 'Data', default: email, read_only: 1 },
//                     { label: 'Email Preview', fieldname: 'email_preview', fieldtype: 'HTML', options: preview_message },
//                     { fieldname: 'item_name', fieldtype: 'Data', default: item_name, hidden: 1 },
//                     { fieldname: 'item_code', fieldtype: 'Data', default: item_code, hidden: 1 },
//                     { fieldname: 'po_name', fieldtype: 'Data', default: po_name, hidden: 1 },
//                     { fieldname: 'schedule_date', fieldtype: 'Data', default: schedule_date, hidden: 1 }
//                 ],
//                 size: 'large',
//                 primary_action_label: 'Send',
//                 primary_action(values) {
//                     if (!values.contact_email) {
//                         frappe.msgprint('Supplier email is required');
//                         return;
//                     }
//                     frappe.call({
//                         method: "iso_9001_2015.iso_9001_2015.page.vendor_followup.vendor_followup.send_supplier_email",
//                         args: {
//                             item_name:values.item_name,
//                             item_code:values.item_code,
//                             supplier: values.supplier_name,
//                             email: values.contact_email,
//                             po_name: values.po_name,
//                             schedule_date: values.schedule_date
//                         },

//                         callback: function (r) {
//                             if (r && r.message) {
//                                 const msg = r.message.message || "Follow-up email sent.";
//                                 const total_sent = r.message.total_sent || 0;
//                                 const po_name = values.po_name;
//                                 const item_code = values.item_code;

//                                 frappe.msgprint(`${msg} (Total sent: ${total_sent})`);

//                                 console.log("Updating count for:", po_name, item_code, "→", total_sent);

//                                 // Update correct card count
//                                 const card = button.closest(".card");
//                                 const countEl = card.find(".followup-count");

//                                 if (countEl.length) {
//                                     countEl.text(total_sent);
//                                     console.log("Count element updated successfully");
//                                 } else {
//                                     console.warn("No .followup-count found inside this card");
//                                 }
//                             } else {
//                                 frappe.msgprint("Unexpected response from server.");
//                             }
//                         }


//                     });
//                     d.hide();

//                 }
//             });
//             d.show();
//         });
//     }
// };




















frappe.pages["vendor-followup"].on_page_load = function (wrapper) {
    // -----------------------------------
    // Initialize Page
    // -----------------------------------
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Vendor Follow-Up",
        single_column: true,
    });

    let container = $('<div>').appendTo(page.body);

    // -----------------------------------
    // Function to Load Data
    // -----------------------------------
    function load_data() {
        let supplier = page.supplier_field.get_value();
        let from_date = page.from_date_field.get_value();
        let to_date = page.to_date_field.get_value();
        let po_type = page.po_type_field.get_value();
        let status = page.status_field.get_value();

        get_data(supplier, from_date, to_date, po_type, status)
            .then((supplierData) => render_data(supplierData))
            .catch((err) => console.log("Error fetching data:", err));
    }

    // -----------------------------------
    // Add Filters
    // -----------------------------------
    page.from_date_field = page.add_field({
        fieldname: 'from_date',
        label: __('From Date'),
        fieldtype: 'Date',
        reqd: 1
    });

    page.to_date_field = page.add_field({
        fieldname: 'to_date',
        label: __('To Date'),
        fieldtype: 'Date',
        reqd: 1
    });

    page.supplier_field = page.add_field({
        fieldname: 'supplier',
        label: __('Supplier'),
        fieldtype: 'Link',
        options: 'Supplier'
    });

    page.po_type_field = page.add_field({
        fieldname: 'po_type',
        label: __('PO Type'),
        fieldtype: 'Select',
        options: ["", "Capital", "Consumable", "Expense", "Others", "Return", "Rework", "Sub-Contract"].join('\n')
    });

    page.status_field = page.add_field({
        fieldname: 'status',
        label: __('Status'),
        fieldtype: 'Select',
        options: ["", "To Receive and Bill", "To Bill"].join('\n')
    });

    // -----------------------------------
    // Search Button
    // -----------------------------------
    page.search_button = page.add_field({
        fieldname: 'search',
        label: __('Search'),
        fieldtype: 'Button',
        click: function () {
            let from_date = page.from_date_field.get_value();
            let to_date = page.to_date_field.get_value();
            if (!from_date || !to_date) {
                frappe.msgprint(__('From Date and To Date are mandatory.'));
                return;
            }
            load_data();
        }
    });

    // -----------------------------------
    // Button Styling
    // -----------------------------------
    page.search_button.$wrapper.addClass('btn custom-search-btn');
    const style = document.createElement('style');
    style.innerHTML = `
        .custom-search-btn button {
            background-color: #007bff;
            color: white;
            border: 1px solid #0056b3;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0px 4px 6px rgba(0, 123, 255, 0.3);
        }
        .custom-search-btn button:hover {
            background-color: #0056b3;
            color: white;
            box-shadow: 0px 6px 10px rgba(0, 91, 187, 0.5);
        }
        .custom-search-btn button:focus,
        .custom-search-btn button:active {
            outline: none !important;
            background-color: #007bff !important;
            border: 1px solid #0056b3 !important;
            color: white !important;
            box-shadow: 0px 4px 6px rgba(0, 123, 255, 0.3) !important;
            transform: none !important;
        }
    `;
    document.head.appendChild(style);

    // -----------------------------------
    // Fetch Data from Backend
    // -----------------------------------
    function get_data(supplier, from_date, to_date, po_type, status) {
        let filters = { docstatus: 1 };

        if (supplier) filters["supplier"] = supplier;
        if (from_date && to_date) {
            filters["transaction_date"] = ["between", [from_date, to_date]];
        } else if (from_date) {
            filters["transaction_date"] = [">=", from_date];
        } else if (to_date) {
            filters["transaction_date"] = ["<=", to_date];
        }

        if (po_type) filters["po_type"] = po_type;
        if (status) filters["status"] = status;
        else filters["status"] = ["in", ["To Receive and Bill", "To Receive"]];

        return frappe.call({
            method: "iso_9001_2015.iso_9001_2015.page.vendor_followup.vendor_followup.get_data",
            args: { filters: filters }
        }).then((r) => r.message || []);
    }

    // -----------------------------------
    // Render Data Cards
    // -----------------------------------
    function render_data(data) {
        data.forEach((item, index) => item.index = index + 1);

        let html = frappe.render_template("vendor_followup", { purchase_orders: data });
        container.html(html);

        // Attach button click events for each card
        container.find('.msgprint-btn').click(function () {
            var button = $(this);
            var supplier = button.data('supplier');
            var email = button.data('email');
            var po_name = button.data('po');
            var item_name = button.data('item-name');
            var item_code = button.data('item-code');
            var schedule_date = button.data('schedule-date');

            var user_fullname = frappe.session.user_fullname || "Your Name";
            var preview_message = `
                Dear ${supplier},<br><br>
                This is a reminder regarding Item <b>${item_name}</b> from Purchase Order <b>${po_name}</b>,
                scheduled for delivery on <b>${schedule_date}</b>.<br><br>
                Kindly confirm the delivery status.<br><br>
                Best regards,<br>
                ${user_fullname}<br>
            `;

            // -----------------------------------
            // Dialog to Confirm & Send Email
            // -----------------------------------
            var d = new frappe.ui.Dialog({
                title: 'Send Follow-Up Email',
                fields: [
                    { label: 'Supplier Name', fieldname: 'supplier_name', fieldtype: 'Data', default: supplier, read_only: 1 },
                    { label: 'Supplier Email', fieldname: 'contact_email', fieldtype: 'Data', default: email, read_only: 1 },
                    { label: 'Email Preview', fieldname: 'email_preview', fieldtype: 'HTML', options: preview_message },
                    { fieldname: 'item_name', fieldtype: 'Data', default: item_name, hidden: 1 },
                    { fieldname: 'item_code', fieldtype: 'Data', default: item_code, hidden: 1 },
                    { fieldname: 'po_name', fieldtype: 'Data', default: po_name, hidden: 1 },
                    { fieldname: 'schedule_date', fieldtype: 'Data', default: schedule_date, hidden: 1 }
                ],
                size: 'large',
                primary_action_label: 'Send',
                primary_action(values) {
                    if (!values.contact_email) {
                        frappe.msgprint('Supplier email is required.');
                        return;
                    }

                   frappe.call({
                        method: "iso_9001_2015.iso_9001_2015.page.vendor_followup.vendor_followup.send_supplier_email",
                        args: {
                            supplier: values.supplier_name,
                            email: values.contact_email,
                            po_name: values.po_name,
                            schedule_date: values.schedule_date,
                            item_name: values.item_name,
                            item_code: values.item_code
                        },
                        callback: function (r) {
                            if (r && r.message) {
                                const msg = r.message.message || "Follow-up email sent.";
                                const total_sent = r.message.total_sent || 0;
                                frappe.msgprint(`${msg} (Total sent: ${total_sent})`);

                                // Update follow-up count dynamically
                                const card = button.closest(".card");
                                const countEl = card.find(".followup-count");
                                if (countEl.length) {
                                    countEl.text(total_sent);
                                    countEl.css({ "color": "#007bff", "font-weight": "bold" });
                                }
                            } else {
                                frappe.msgprint("Unexpected response from server.");
                            }
                        }
                    });

                    d.hide();
                }
            });

            d.show();
        });
    }
};
