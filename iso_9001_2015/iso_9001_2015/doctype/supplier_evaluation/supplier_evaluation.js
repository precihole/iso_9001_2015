// // // // // // // Copyright (c) 2026, Kiran and contributors
// // // // // // // For license information, please see license.txt

// // // // // // // frappe.ui.form.on("Supplier Evaluation", {
// // // // // // // 	refresh(frm) {

// // // // // // // 	},
// // // // // // // });



/************************************************************
 * CONSTANTS
 ************************************************************/
const SUPPLIER_THRESHOLDS = {
    preferred: 75,
    conditional: 50
};

/************************************************************
 * HELPERS
 ************************************************************/
function set_if_changed(frm, fieldname, value) {
    const current = frm.doc[fieldname];

    const cur = (current === null || current === undefined) ? "" : current;
    const val = (value === null || value === undefined) ? "" : value;

    if (String(cur) === String(val)) return;
    frm.set_value(fieldname, val);
}

function escape_html(v) {
    return frappe.utils.escape_html(v || "");
}

/************************************************************
 * SCORE + STATUS (DATA / LOGIC)
 ************************************************************/
function to_rating(grading) {
    if (grading === null || grading === undefined || grading === "") return 0;

    let g = parseFloat(grading);
    if (isNaN(g) || g <= 0) return 0;

    // ✅ handle normalized (0.2..1.0) -> 1..5
    if (g > 0 && g <= 1) {
        return Math.max(1, Math.min(5, Math.round(g * 5)));
    }

    // ✅ handle normal (1..5)
    return Math.max(1, Math.min(5, Math.round(g)));
}

// Guard to prevent refresh recursion
let __calc_in_progress = false;

function calculate_result(frm) {
    const rows = frm.doc.supplier_evaluation_system_details || [];

    const total_questions = rows.length;
    let na_count = 0;
    let graded_count = 0;
    let total_score = 0;

    rows.forEach(row => {
        const ans = (row.answer || "").trim().toUpperCase();

        // NA → excluded from denominator
        if (ans === "NA") {
            na_count += 1;
            return;
        }

        const rating = to_rating(row.grading);

        // only graded questions count
        if (rating) {
            graded_count += 1;
            total_score += rating;
        }
    });

    const applicable_questions = total_questions - na_count;
    const max_score = applicable_questions * 5;

    const achievement = max_score
        ?(total_score / max_score) * 100
        : 0;

    // total_count = ONLY graded questions
    set_if_changed(frm, "total_count", graded_count);
    set_if_changed(frm, "score", total_score);
    set_if_changed(frm, "achievement", achievement);

    frm.refresh_field("supplier_evaluation_system_details");

    return {
        total_questions,
        na_count,
        applicable_questions,
        graded_count,
        total_score,
        achievement
    };
}




function compute_supplier_status(achievement) {
    if (achievement >= SUPPLIER_THRESHOLDS.preferred) return "Preferred Supplier";
    if (achievement >= SUPPLIER_THRESHOLDS.conditional) return "Conditionally Approved";
    return "Rejected";
}

function compute_supplier_remarks(status) {
    if (status === "Preferred Supplier") {
        return "Supplier meets most requirements. Can be included in regular sourcing.";
    }
    if (status === "Conditionally Approved") {
        return "Supplier has gaps. May be considered with follow-up actions, risk mitigation, or trials.";
    }
    return "Supplier is not qualified. Must not be used until corrective actions are taken and re-evaluation is done.";
}

function set_supplier_status_field(frm) {
    const achievement = cint(frm.doc.achievement || 0);
    const status = compute_supplier_status(achievement);
    set_if_changed(frm, "supplier_status", status);
}

/************************************************************
 * CONTACT CARD UI (UI ONLY)
 ************************************************************/
function render_contact_card(contact) {
    const full_name = [contact.first_name, contact.last_name].filter(Boolean).join(" ");
    const name = full_name || contact.name;

    return `
        <div class="border rounded p-3 mb-3 h-100" style="background: rgb(243, 243, 243);">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <div class="font-weight-bold">
                        ${escape_html(name)}
                        ${contact.is_primary_contact ? `<span class="text-muted"> · Primary</span>` : ""}
                    </div>

                    ${contact.designation ? `<div>${escape_html(contact.designation)}</div>` : ""}
                    ${contact.mobile_no ? `<div>${escape_html(contact.mobile_no)}</div>` : ""}
                    ${contact.email_id ? `<div>${escape_html(contact.email_id)}</div>` : ""}
                </div>

                <a class="text-muted" href="/app/contact/${encodeURIComponent(contact.name)}" title="${__("Edit Contact")}">✎</a>
            </div>
        </div>
    `;
}

function add_new_contact_button(wrapper, frm) {
    wrapper.append(`
        <button class="btn btn-sm btn-secondary mt-2 new-contact-btn">
            ${__("New Contact")}
        </button>
    `);

    wrapper.find(".new-contact-btn").on("click", () => {
        if (!frm.doc.supplier_name) {
            frappe.msgprint(__("Please select Supplier first."));
            return;
        }

        frappe.new_doc("Contact", {
            links: [{
                link_doctype: "Supplier",
                link_name: frm.doc.supplier_name
            }]
        });
    });
}

/************************************************************
 * HTML TABLES (UI ONLY)
 ************************************************************/
function render_guidelines_for_grading(frm) {
    const field = frm.get_field("guidelines_for_grading");
    if (!field || !field.$wrapper) return;

    const html = `
        <div style="border:2px solid #000;">
            <table style="width:100%; border-collapse:collapse; font-size:14px;">
                <tr>
                    <th colspan="2" style="border-bottom:2px solid #000; padding:8px; text-align:center; font-size:16px;">
                        Guidelines for Grading
                    </th>
                </tr>

                <tr>
                    <th style="border:1px solid #000; padding:8px;">Description</th>
                    <th style="border:1px solid #000; padding:8px; width:90px;">Grading</th>
                </tr>

                <tr><td style="border:1px solid #000; padding:8px;">No evidence of basic systems</td><td style="border:1px solid #000; padding:8px; text-align:center;">1</td></tr>
                <tr><td style="border:1px solid #000; padding:8px;">Defined systems but no evidence of implementation</td><td style="border:1px solid #000; padding:8px; text-align:center;">2</td></tr>
                <tr><td style="border:1px solid #000; padding:8px;">Partial implementation of the systems</td><td style="border:1px solid #000; padding:8px; text-align:center;">3</td></tr>
                <tr><td style="border:1px solid #000; padding:8px;">Adequate systems and systems are followed</td><td style="border:1px solid #000; padding:8px; text-align:center;">4</td></tr>
                <tr><td style="border:1px solid #000; padding:8px;">The system is a benchmark amongst all suppliers in the same category</td><td style="border:1px solid #000; padding:8px; text-align:center;">5</td></tr>
                <tr><td style="border:1px solid #000; padding:8px; font-weight:bold;">Not Applicable</td><td style="border:1px solid #000; padding:8px; text-align:center; font-weight:bold;">NA</td></tr>
            </table>
        </div>
    `;

    field.$wrapper.html(html);
}

function render_supplier_classification(frm) {
    const field = frm.get_field("supplier_classification_based_on_achievement");
    if (!field || !field.$wrapper) return;

    const html = `
        <div style="border:2px solid #000; margin-top:10px;">
            <table style="width:100%; border-collapse:collapse; font-size:14px;">
                <tr>
                    <th colspan="3" style="border-bottom:2px solid #000; padding:8px; text-align:center; font-size:16px;">
                        Supplier Classification Based on Achievement (%)
                    </th>
                </tr>

                <tr>
                    <th style="border:1px solid #000; padding:8px; width:30%;">Supplier Status</th>
                    <th style="border:1px solid #000; padding:8px; width:20%;">Achievement (%)</th>
                    <th style="border:1px solid #000; padding:8px;">Remarks</th>
                </tr>

                <tr>
                    <td style="border:1px solid #000; padding:8px;">Preferred Supplier</td>
                    <td style="border:1px solid #000; padding:8px; text-align:center;">≥ ${SUPPLIER_THRESHOLDS.preferred}%</td>
                    <td style="border:1px solid #000; padding:8px;">Supplier meets most requirements. Can be included in regular sourcing.</td>
                </tr>

                <tr>
                    <td style="border:1px solid #000; padding:8px;">Conditionally Approved</td>
                    <td style="border:1px solid #000; padding:8px; text-align:center;">${SUPPLIER_THRESHOLDS.conditional}% – ${SUPPLIER_THRESHOLDS.preferred - 1}%</td>
                    <td style="border:1px solid #000; padding:8px;">Supplier has gaps. May be considered with follow-up actions, risk mitigation, or trials.</td>
                </tr>

                <tr>
                    <td style="border:1px solid #000; padding:8px;">Rejected</td>
                    <td style="border:1px solid #000; padding:8px; text-align:center;">&lt; ${SUPPLIER_THRESHOLDS.conditional}%</td>
                    <td style="border:1px solid #000; padding:8px;">Supplier is not qualified. Must not be used until corrective actions are taken and re-evaluation is done.</td>
                </tr>
            </table>
        </div>
    `;

    field.$wrapper.html(html);
}

function render_supplier_status_banner(frm) {
    if (frm.is_new()) return;

    const achievement = cint(frm.doc.achievement || 0);
    const status = frm.doc.supplier_status || compute_supplier_status(achievement);
    const remarks = compute_supplier_remarks(status);

    let color = "red";
    if (status === "Preferred Supplier") color = "green";
    else if (status === "Conditionally Approved") color = "orange";

    frm.dashboard.set_headline_alert(
        `
        <div class="supplier-status-alert ${color}">
            Supplier Status: <b>${frappe.utils.escape_html(status)}</b>
            &nbsp; | &nbsp;
            Achievement: <b>${achievement}%</b>
            <br>
            <span class="supplier-remarks-badge ${color}">
                ${frappe.utils.escape_html(remarks)}
            </span>
        </div>
        `,
        color
    );

    setTimeout(() => {
        frm.dashboard.headline_area
            .find(".supplier-status-alert")
            .closest(".alert")
            .css({ width: "100%", maxWidth: "100%", marginLeft: "0", marginRight: "0" });
    }, 0);
}

/************************************************************
 * DEFAULT QUESTIONS
 ************************************************************/
function add_default_questions(frm) {
    if (frm.doc.supplier_evaluation_system_details?.length) return;

    const questions = [
        { category: "Quality Management System", question: "Is the supplier certified to a recognized QMS standard (e.g., ISO 9001, IATF 16949)?" },
        { category: "Quality Management System", question: "Are documents (e.g. design, drawings, work instructions) controlled and updated systematically?" },
        { category: "Quality Management System", question: "Does the supplier have a structured Corrective & Preventive Action (CAPA) and traceability system?" },
        { category: "Confidentiality", question: "Is there a signed Supplier Confidentiality Agreement (NDA) in place?" },
        { category: "Supplier Indemnification", question: "Does the supplier have existing customers with indemnification agreements?" },
        { category: "Supplier Indemnification", question: "Is the supplier willing to negotiate an indemnification & NDA agreement with Precihole Sports?" },
        { category: "Machine and Process Technology", question: "Is the latest equipment or process technology being used?" },
        { category: "Machine and Process Technology", question: "1> Does the supplier have modern manufacturing equipment (e.g., 4/5-Axis CNC, Wirecut EDM)?, 2> Does the supplier have modern injection molding and in-house tool room capability?, 3> Is the supplier equipped with laser cutting or sheet metal punching facilities?"},
        { category: "Machine and Process Technology", question: "How well are process flow, WIP handling, and preventive maintenance system, production planning managed?" },
        { category: "Machine and Process Technology", question: "Does the supplier have automated or semi-automated assembly processes?" },
        { category: "Tooling & Dies Management", question: "Is there a machine list, tool history card, and proper storage & maintenance system?" },
        { category: "Tooling & Dies Management", question: "Are preventive maintenance records maintained and followed?" },
        { category: "Incoming / Outgoing Inspection", question: "Are incoming materials and finished goods inspected with a documented system?" },
        { category: "Incoming / Outgoing Inspection", question: "Are quality tools like Control Plan, SPC, MSA, FAI, 4M, 8D, COPQ used?" },
        { category: "Incoming / Outgoing Inspection", question: "Is a master list maintained, and are all tools calibrated?" },
        { category: "Incoming / Outgoing Inspection", question: "Are test reports and calibration certificates readily available?" },
        { category: "Incoming / Outgoing Inspection", question: "Are customer complaints recorded and addressed formally?" },
        { category: "Incoming / Outgoing Inspection", question: "Is there a record of rejection/rework and trend analysis?" },
        { category: "Material Handling & Storage", question: "Is FIFO followed, shelf-life monitored, and traceability maintained?" },
        { category: "Workforce & Training", question: "Are skill levels recorded, and training provided with documented work instructions?" },
        { category: "EHS Compliance", question: "Is there compliance with basic EHS requirements? (_toggle, Fire Safety & Waste Handling)" },
        { category: "Response to Customer Complaints", question: "How fast is the response time after a customer complaint is received?" },
        { category: "Response to Customer Complaints", question: "Are proper 8D reports or other RCA tools used?" },
        { category: "Response to Customer Complaints", question: "How quickly can supplier arrange sorting at the customer site?" },
        { category: "Delivery & Logistics", question: "How consistently does the supplier deliver materials on or before the agreed timeline?" },
        { category: "Delivery & Logistics", question: "Are materials packed in line with customer requirements and industry norms?" }
    ];

    questions.forEach(q => {
        const row = frm.add_child("supplier_evaluation_system_details");
        row.category = q.category;
        row.question = q.question;
    });

    frm.refresh_field("supplier_evaluation_system_details");
}

/************************************************************
 * CONTACT RENDER (UI ONLY)
 ************************************************************/
function render_supplier_contacts(frm) {
    const wrapper = frm.fields_dict.contact_html?.$wrapper;
    if (!wrapper) return;

    wrapper.empty();

    if (!frm.doc.supplier_name) {
        wrapper.html(`<div class="text-muted">${__("Select Supplier to view contacts")}</div>`);
        return;
    }

    frappe.call({
        method: "iso_9001_2015.iso_9001_2015.doctype.supplier_evaluation.supplier_evaluation.get_supplier_contacts",
        args: { supplier_name: frm.doc.supplier_name },
        callback(r) {
            const contacts = r.message || [];

            if (!contacts.length) {
                wrapper.html(`<div class="text-muted">${__("No contacts found")}</div>`);
                add_new_contact_button(wrapper, frm);
                return;
            }

            const row = $(`<div class="row"></div>`);

            contacts.forEach(contact => {
                row.append(`
                    <div class="col-md-6">
                        ${render_contact_card(contact)}
                    </div>
                `);
            });

            wrapper.append(row);
            add_new_contact_button(wrapper, frm);
        }
    });
}

function lock_all_na_rows(frm) {
    const grid = frm.fields_dict.supplier_evaluation_system_details?.grid;
    if (!grid) return;

    (frm.doc.supplier_evaluation_system_details || []).forEach(row => {
        const ans = (row.answer || "").trim().toUpperCase();
        const grid_row = grid.grid_rows_by_docname[row.name];
        if (!grid_row) return;

        const is_na = ans === "NA";
        grid_row.toggle_editable("grading", !is_na);
    });
}


/************************************************************
 * MAIN FORM EVENTS
 ************************************************************/
frappe.ui.form.on("Supplier Evaluation", {
    onload(frm) {
        add_default_questions(frm);
    },

    refresh(frm) {
        render_supplier_contacts(frm);
        render_guidelines_for_grading(frm);
        render_supplier_classification(frm);
        render_supplier_status_banner(frm);

        calculate_result(frm);
        lock_all_na_rows(frm);
    },


    validate(frm) {
        if (!frm.doc.posting_date) {
            frappe.msgprint(__("Posting Date is mandatory"));
            frappe.validated = false;
            return;
        }

        const today = frappe.datetime.now_date();

        if (frm.doc.posting_date > today) {
            frappe.msgprint(__("Posting Date cannot be in the future"));
            frappe.validated = false;
            return;
        }

        if (frm.doc.posting_date < "2022-04-01") {
            frappe.msgprint(__("Posting Date cannot be before 01-04-2022"));
            frappe.validated = false;
            return;
        }
    },

    supplier_name(frm) {
        render_supplier_contacts(frm);
        if (typeof fetch_city_pin_safe === "function") {
            fetch_city_pin_safe(frm);
        }
    },

    before_save(frm) {
        calculate_result(frm);
        set_supplier_status_field(frm);
    },

    after_save(frm) {
        render_supplier_status_banner(frm);
    },

    supplier_evaluation_system_details_remove(frm) {
        calculate_result(frm);
    }
});

frappe.ui.form.on("Supplier Evaluation System Details", {
    grading(frm) {
        calculate_result(frm);
    },
    answer(frm) {
        calculate_result(frm);
        lock_all_na_rows(frm);
    }
});


