# Contract: breadcrumb trails

Interface is the rendered trail on detail and tab pages. Left to right, the first entry is always the list of the object type, the last the object itself.

| Page | Trail |
|------|-------|
| Contract | Contracts > external party name (links to contracts of that party; omitted without a party) > contract name |
| Contract line | Contract lines > contract name (links to the lines of that contract) > line name |
| Invoice | Invoices > each contract name (links to invoices of that contract) > invoice number |
| Invoice line | Invoice lines > invoice number (links to the lines of that invoice) > line name |

Tab pages (changelog, journal, contracts and so on) show the same trail. Entries are displayed whatever the viewer's permissions; following one still applies the viewer's permissions on the target list.
