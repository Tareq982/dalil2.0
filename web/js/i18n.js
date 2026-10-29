// Interface text, in one place. Issue #16 adds the other languages here:
// copy the "en" block, translate the values, keep the keys. Missing keys fall back to English.
export const STRINGS = {
  en: {
    tab_scan: "Scan",
    tab_deadlines: "My deadlines",
    tab_services: "Services",
    tab_how: "How it works",

    scan_title: "What does this paper say?",
    scan_lede: "Take a photo of a fine, visa notice or tenancy contract. Dalil explains it in your language and shows the official next step.",
    drop_title: "Take a photo or choose a file",
    drop_hint: "Photo or PDF of the whole page",
    drop_change: "Choose a different file",
    answer_language: "Explain it in",
    explain_button: "Explain this document",
    privacy: "Your photo is read once and never saved.",

    step_read: "Reading your document",
    step_match: "Matching it to official data",
    step_explain: "Writing the explanation",

    kind_traffic_fine: "Traffic fine",
    kind_visa_residency_notice: "Residency or visa notice",
    kind_tenancy_contract: "Tenancy contract",
    kind_other: "Document",
    kind_from: "from",

    fact_amount: "Amount on the paper",
    fact_fee: "Official fee",
    fact_deadline: "Deadline on the paper",
    fact_none: "Not printed",
    stamp_days_left: "days left",
    stamp_day_left: "day left",
    stamp_overdue: "days overdue",
    stamp_today: "today",

    h_cost: "How much",
    h_deadline: "By when",
    h_steps: "What to do next",
    open_official: "Open the official service",

    verified: "Fees and steps checked on the official page",
    unverified: "Not yet checked on an official page. Confirm before you pay.",
    legal_basis: "Legal basis",
    source: "Source",

    read_title: "What Dalil read from your paper",
    read_type: "Type",
    read_authority: "Issued by",
    read_reference: "Reference number",
    read_amount: "Amount",
    read_issue: "Issue date",
    read_deadline: "Deadline",
    read_subject: "About",

    scan_another: "Scan another document",
    mock: "Mock mode: sample answer, no AI key set",
    error_title: "Dalil couldn't read this document.",
    error_hint: "Check the photo is sharp and shows the whole page, then try again.",

    coming_deadlines: "Saved deadlines will appear here, with reminders and an Add to calendar button.",
    coming_services: "The official services Dalil knows, with fees, steps and where each fact comes from.",
    coming_how: "How Dalil reads, checks and explains your document, which open data it uses, and how your privacy is protected.",
  },
};

let lang = "en";

export function setLanguage(code) {
  lang = STRINGS[code] ? code : "en";
}

export function t(key) {
  return (STRINGS[lang] && STRINGS[lang][key]) || STRINGS.en[key] || key;
}

// Fill every element that has data-i18n="key" (used by the static parts of index.html).
export function applyStatic(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
}
