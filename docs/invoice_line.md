# Invoice line

An invoice line correspond to the accouning lines for the invoice.
You can define several accounting lines for an invoice but the sum of each line amount should match the invoice amount. this is enforced if you create the invoice line through the web ui.

![Invoice line](img/invoice_line.png "invoice line")

- Invoice: The corresponding invoice.
- Currency: The currency of the invoice
- Amount: the amount of the invoice. Whether you take into account VAT in this amount depends on the way your budget is contructed.
- Accounting dimensions: The accounting dimensions for the invoice.
- Comments: Self explanatory