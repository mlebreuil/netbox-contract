# Contract lines and units

A contract is described line by line. Each contract line says what the contract bills for, how much, and how.

## Units

A unit defines the nature of a cost:

- **Billing method**:
    - *One-time*: invoiced once, for example a setup fee.
    - *Recurring*: invoiced for each period, for example a monthly subscription.
    - *Usage-based*: invoiced from the quantity used, entered on each invoice line (for example gigabytes of traffic).
- **Months**: for a recurring unit only, the number of months one unit price covers (monthly is 1, quarterly 3, yearly 12). It must be empty for the other billing methods.

A unit used by contract lines cannot be deleted. Its billing method and months cannot change while a contract that has invoices uses it; create a new unit instead. The other fields can be edited at any time.

The upgrade to version 2.5.0 creates the units "One-time", "Monthly" and "Yearly" when it needs them.

## Contract lines

- **Contract**: the contract the line belongs to.
- **Description**.
- **Quantity**: defaults to 1. Zero and negative values are accepted (for example a credit).
- **Unit price**: the price of one unit. For a recurring unit, it is the price of the months the unit covers.
- **Unit**.
- **Currency**: defaults to the currency of the contract and must be equal to it.
- **Start date** and **end date**: default to the dates of the contract and must lie within them. A contract without a start or an end date imposes no limit on that side.
- **Accounting dimensions**: any number of dimensions. They are copied to the invoice lines generated from the line.
- **Invoiced at conversion** (read-only): set by the upgrade for a one-time line of a contract that already had a posted invoice. Such a line is considered fully invoiced and is never proposed again.

Contract lines are shown on their contract, with a button to add a new one. They can also be managed from the *Contract lines* menu, imported in bulk and managed through the REST API.

### Values

- **Total value**: recurring lines over their dates (quantity x unit price x months of the line / months of the unit), one-time lines once, usage-based lines at their stated quantity. It is "not available" for a recurring line without a start or an end date on an open-ended contract.
- **Yearly value**: the twelve-month value of a recurring line (quantity x unit price x 12 / months of the unit).

Months are counted as whole calendar months plus the leftover days divided by the days of the month in which the range ends: 1 January to 20 March is 2 + 20/31 months. Amounts are rounded once, at the end, to two decimals.

### Lock once invoiced

As soon as a contract has an invoice (draft, posted or canceled), its contract lines can no longer be added or deleted, and their contract terms (description, quantity, unit price, unit, currency, dates and custom fields) can no longer change: a new contract must be created. A contract line is also locked as soon as an invoice line references it, even when its own contract (a non-billable child) has no invoice. Deleting the contract itself still deletes its lines.

### Amending a price or quantity

When the price or the quantity of a recurring or usage-based line changes during the contract (for example a yearly indexation, or more licences), use **Amend price or quantity** on the contract line page. Enter the date the new terms apply from, the new unit price and/or quantity, and a reason. The line then ends the day before that date, and a new line with the new terms replaces it from that date; the new line keeps the unit, currency, accounting dimensions and end date, and shows which line it replaces.

- The date must be after the end of the last invoiced period of the line (draft and posted invoices count, canceled ones do not), so invoiced periods never change price.
- The reason is required. It is recorded as the change-log message of both lines and added to the comments of the new line.
- One-time lines cannot be amended.
- The yearly values of the contract count only the current line; the total contract value counts each line over its own dates. An invoice whose period spans the change gets both lines, each prorated to its days.
- The same action is available in the REST API: `POST contract-lines/{id}/amend/`.

The accounting dimensions, comments and tags of a locked line can still be edited, since they are internal classification rather than contract terms; the edit form shows the other fields disabled. Invoice lines already created keep their own dimensions; new invoice lines take the new ones.
