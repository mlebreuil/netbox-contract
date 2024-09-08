# Invoice

New invoices shoold be created from the corresponding contract. Most of their fields will be derived from the contract invoice template. An invoice template is an invoice object which "Template" field is set to true. There can be only one invoice per contract.
Each invoice will be linked to one or more invoice line.

![Invoice](img/invoice.png "invoice")

- Number: The invoice number. Should correspond to your accounting sysstem invoice number.
- Template: Whether this isvoice is an invoice template for the corresponding contract(s). There can be only one invoice template per contract. The template will be used to define automatically the fields of a nre invoice, including the correpsonding accounting lines with their dimensions.
- Date: the date of the invoice
- Contracts: The contracts linked to the invoice.
- Period_start: The start of the contract periode covered by this invoice.
- Period_end: The end of the contract period covered by this invoice.
- currency: The currency of the invoice
- accounting_dimensions: The use of this field is deprecated. Invoice lines and the corresponding accounting dimensions should be used instead.
- Amount: The amount of the invoice
- Documents: A link to the corresponding document. This field is deprecated and the document plugin should be used instead.
- Comments: self explanatory.

Linked objects:  

![Invoice linked objects](img/invoice_linked_objects.png "invoice linked objects")
