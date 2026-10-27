# Data sources

Every fee, deadline rule and link in `services.json` must trace back to a row here.
This file is also your evidence for the "Effective Use of Open Data" score (20%).

| Record id | Field(s) | Source (name) | URL | Downloaded / checked on | Notes |
|---|---|---|---|---|---|
| dubai-traffic-fine | official_url | Dubai Police (official home page) | https://www.dubaipolice.gov.ae | 2026-10-27 | Official domain. Hosts the Fines Inquiry and Payment service. |
| dubai-traffic-fine | next_steps | Dubai Police, services page (Fines Inquiry and Payment) | https://www.dubaipolice.gov.ae/app/services/ | 2026-10-27 | Official. Lists traffic fines payment by plate, licence or traffic code, plus Instalments, Pay Against Impound and Violation Evidence Images. Supports the 3 next_steps (app or website, search by plate or traffic file number, pay online). |
| dubai-traffic-fine | fee_aed, fee_note | Dubai Police, service card: Fines Inquiry and Payment | https://youfirst.dubaipolice.gov.ae/wps/portal/home/services/individualservicescontent/finesinquiryDetails | 2026-10-27 | Official. Fee = the amount of the fine + AED 20 knowledge and innovation fees. Keep fee_aed = null (varies per fine). Suggested fee_note: "The amount printed on the fine, plus AED 20 knowledge and innovation fees." Also states cards issued outside the UAE/GCC are not accepted online, and a valid email and mobile number are needed. |
| dubai-traffic-fine | fee_note (list of violations) | Dubai Police, home page FAQ | https://www.dubaipolice.gov.ae/wps/portal/home | 2026-10-27 | Official. Printed list of violations is free online and AED 5 per vehicle at a service location. Optional detail. |
| dubai-traffic-fine | deadline_rule (early-payment discount) | UAE Times, "UAE Traffic Fine Discount 2026" | https://theuaetimes.ae/uae-traffic-fine-discount/ | 2026-10-27 | Third-party. Found NO official standing Dubai early-payment discount (35% / 25% is confirmed for Abu Dhabi and Sharjah only). Recommended: leave deadline_rule = null or state "No standing discount confirmed; check the amount in the Dubai Police app". Do not claim 35% for Dubai. |
| dubai-traffic-fine | deadline_rule (conflict note) | UAE Expert Hub, "Dubai Traffic & Police Fines: How to Check and Pay in 2026" | https://www.uaeexperthub.com/dubai-traffic-fines-check-pay-online/ | 2026-10-27 | Third-party. Says an up-to-35% discount within 60 days is only periodically activated and not guaranteed. Other sites claim 50% or a permanent 35%. Conflicting, so unverified. |
| dubai-traffic-fine | items.speeding: fine_aed, black_points | Gulf News, "Dubai Police AI traffic fines: Eight offences detected by radars" (updated 2026-07-30) | https://gulfnews.com/living-in-uae/transport/uae-eight-traffic-offences-detected-by-dubai-polices-advanced-ai-radar-system-1.500056465 | 2026-10-27 | Media report of Dubai Police figures. Fine scale: up to 20 km/h over = AED 300; up to 30 = 600; up to 40 = 700; up to 50 = 1,000; over 60 = 2,000 + 12 points + 30-day impound; over 80 = 3,000 + 23 points + 60-day impound. Black points for the lower bands are not given consistently, so keep black_points = null (a range) unless an official table is found. |
| dubai-traffic-fine | items.parking: fine_aed, black_points | No source found | n/a | 2026-10-27 | Parking fines are issued by RTA and vary by zone. No verified single figure was found, so keep null. Parking carries no black points. |
| abu-dhabi-traffic-fine | official_url | Abu Dhabi Police | https://www.adpolice.gov.ae | 2026-10-27 | Domain confirmed by several guides (Askexplorer, Pit Stop Arabia, Policybazaar). Not opened directly, so treat as secondary-source verified. |
| abu-dhabi-traffic-fine | next_steps | Policybazaar UAE, "Abu Dhabi Traffic Fines 2026" | https://www.policybazaar.ae/car-insurance/articles/traffic-fines-in-abu-dhabi/ | 2026-10-27 | Third-party. Inquiry by plate, licence number or Emirates ID on adpolice.gov.ae; payment via the Abu Dhabi Police app or TAMM (UAE PASS login) or MOI. |
| abu-dhabi-traffic-fine | fee_aed, fee_note | Abu Dhabi Police via Gulf News, "90% traffic fine discount in UAE? It could be a fake account" | https://gulfnews.com/uae/90-traffic-fine-discount-in-uae-it-could-be-a-fake-account-1.500145072 | 2026-10-27 | Media report of an official statement. No extra service fee was found, so fee = the amount on the fine. Keep fee_aed = null. |
| abu-dhabi-traffic-fine | deadline_rule | Abu Dhabi Police via Gulf News (same article as above) | https://gulfnews.com/uae/90-traffic-fine-discount-in-uae-it-could-be-a-fake-account-1.500145072 | 2026-10-27 | Rule ("Act Early & Benefit"): 35% off if paid within 60 days of the offence, 25% off if paid between 60 days and one year from issue. Excludes serious violations. |
| abu-dhabi-traffic-fine | deadline_rule (corroboration) | Khaleej Times, "73 screens in Abu Dhabi urge motorists to pay traffic fines early, get 35% discount" | https://www.khaleejtimes.com/uae/abu-dhabi-police-offers-drivers-discounts-on-fines | 2026-10-27 | Media report. Confirms 35% within 60 days and 25% within one year, excluding dangerous violations. |
| dubai-residency-notice | official_url | GDRFA Dubai | https://gdrfad.gov.ae | 2026-10-27 | Official domain. Search results show GDRFA pages at www.gdrfad.gov.ae (e.g. /en/faq). |
| dubai-residency-notice | items.overstay: fine_aed; deadline_rule | Sarmat, "Residence Visa Renewal Dubai 2026" | https://sarmat.ae/resources/residence-visa-renewal-dubai-2026 | 2026-10-27 | Third-party. States the ICP applies a unified overstay fine of AED 50 per day across all emirates since 2026-02-11, starting after the grace period. Needs official confirmation. |
| dubai-residency-notice | items.overstay: fine_aed (corroboration) | HenryClub, "GDRFA Fine Check: UAE Overstay Fines" | https://www.henryclub.ae/visa-immigration/gdrfa-fine-check/ | 2026-10-27 | Third-party. Also reports a flat AED 50 per day for all visa types. Warns that older AED 25 and AED 100 figures are outdated. |
| dubai-residency-notice | items.overstay: fine_aed (CONFLICT) | GDRFA Dubai, FAQ page (older content) | https://www.gdrfad.gov.ae/en/faq | 2026-10-27 | Official but stale (about 2 years old): AED 100 per day + AED 200 out pass. Conflicts with the newer AED 50 per day. Do not use the old figure. Re-check the official GDRFA fines page before setting verified = true. |
| dubai-residency-notice | fee_note, items.renewal: fine_aed | UAE Expert Hub, "Renewing a UAE Residence Visa in Dubai: 2026 Step-by-Step" | https://www.uaeexperthub.com/process/residence-visa-renewal-dubai/ | 2026-10-27 | Third-party. The Dubai renewal fee depends on category and channel and is not confirmed. Keep fee_aed = null. Suggested fee_note: "Fees depend on the visa type and length. Confirm on the GDRFA Dubai website or app." |
| federal-residency-notice | official_url | ICP (Federal Authority for Identity, Citizenship, Customs and Port Security) | https://icp.gov.ae | 2026-10-27 | Official domain. The home page lists Issuing and Renewal of residency permits. |
| federal-residency-notice | fee_note, deadline_rule | UAE Expert Hub (citing the ICP Renewal of residency permits service) | https://www.uaeexperthub.com/process/residence-visa-renewal-dubai/ | 2026-10-27 | Third-party summary of ICP: renewal = AED 100 application + AED 100 per year + a smart-service fee; grace period 30 / 60 / 90 / 180 days by category; overstay AED 50 per day after grace. Verify on the ICP service page before setting verified = true. |
| dubai-tenancy-contract | official_url | Dubai Land Department (DLD) | https://dubailand.gov.ae | 2026-10-27 | Domain (www.dubailand.gov.ae) referenced by Wasl, HenryClub and others as the Ejari registration site. Not opened directly. |
| dubai-tenancy-contract | fee_aed, fee_note | RealKeyper, "Ejari Registration in Dubai: Fees, Steps and Renewal 2026" (cites the DLD Register / Renew Tenancy Contract page, read 2026-10-15) | https://www.realkeyper.com/blogs/ejari-dubai-guide | 2026-10-27 | Third-party citing DLD. AED 177.75 via the Dubai REST app or DLD website (AED 100 registration + 10 knowledge + 10 innovation + 55 partner fee + 2.75 VAT); AED 220 at a Trustee Centre. Renewal costs the same. Suggested fee_aed = 177.75 with the note about AED 220 at a trustee centre. |
| dubai-tenancy-contract | fee_aed (corroboration) | Samana Developers, "What Is Ejari?" | https://www.samanadevelopers.com/blogs/what-is-ejari-how-to-register-your-dubai-tenancy-contract | 2026-10-27 | Third-party. Same AED 177.75 online and AED 220 trustee-centre totals, attributed to DLD. |
| dubai-tenancy-contract | fee_aed (CONFLICT) | ID Booth, "UAE Property Rental: Ejari Registration Guide 2026" | https://idbooth.ae/uae-property-rental-ejari-registration-guide-2026/ | 2026-10-27 | Third-party. Claims a flat AED 220 for all channels. Another older guide (Wasl) gives AED 120 as the base government fee. Conflicting, so confirm on the DLD page before setting verified = true. |
| dubai-tenancy-contract | deadline_rule | UAE Expert Hub, "Tenancy Contract & Ejari Registration Dubai 2026 Guide" | https://www.uaeexperthub.com/tenancy-contract-dubai-guide/ | 2026-10-27 | Third-party. Ejari is mandatory for all rentals in Dubai (Law No. 26 of 2007) and must be redone for each new tenancy period. No official numeric deadline was found (one guide suggests registering within 30 days, which is unconfirmed). Landlord approval is reported to take up to 5 days (RealKeyper). |

## Verification status (read before setting `verified = true`)

Only the **Dubai Police** fee rule (AED 20 knowledge and innovation fees) and links come from an official authority page. Everything else is from media reports or third-party guides, and is marked as such in the Notes column. Each of those should be re-checked on the authority's own page before the record is set to `verified = true`.

Open conflicts to resolve:
- **Dubai early-payment discount:** claimed by many sites, not confirmed by Dubai Police (confirmed for Abu Dhabi).
- **Overstay fine:** AED 50 per day (2026, reported) vs the older AED 100 per day on the GDRFA FAQ.
- **Ejari fee:** AED 177.75 online / AED 220 trustee centre vs a flat AED 220.

## Open data portals to check

Check what is actually downloadable before claiming it in the pitch.

- **Bayanat** (UAE federal open data): https://bayanat.ae
- **Dubai Pulse** (Dubai open data): https://www.dubaipulse.gov.ae (see also its data catalog dataset)
- **RTA open data**: https://www.rta.ae/wps/portal/rta/ae/home/open-data
- Official service catalogs and fee pages of each authority (Dubai Police, GDRFA, ICP, Dubai Land Department)

## Ideas for the pitch

- Use open data on fine categories or service volumes to show which documents cause the most confusion.
- Show one example end to end: photo → matched record → fee/deadline/link → which dataset each came from.
