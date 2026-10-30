# Permissions

The plugin uses NetBox's standard [object permissions](https://netboxlabs.com/docs/netbox/administration/permissions/)
(*Admin → Authentication → Object permissions*). It adds one custom action, **amend**, on contract lines. Everything else
follows the usual `view`, `add`, `change` and `delete` actions, with optional constraints, on the plugin's object types.

## Object types

Select these object types (all listed as *Netbox contract | ...*) in an object permission:

| Object type | Content type | Actions |
|---|---|---|
| Contract | `netbox_contract.contract` | view, add, change, delete |
| Contract line | `netbox_contract.contractline` | view, add, change, delete, **amend** |
| Contract type | `netbox_contract.contracttype` | view, add, change, delete |
| Contract assignment | `netbox_contract.contractassignment` | view, add, change, delete |
| Invoice | `netbox_contract.invoice` | view, add, change, delete |
| Invoice line | `netbox_contract.invoiceline` | view, add, change, delete |
| Unit | `netbox_contract.unit` | view, add, change, delete |
| Accounting dimension | `netbox_contract.accountingdimension` | view, add, change, delete |
| Service provider | `netbox_contract.serviceprovider` | view, add, change, delete |

The permissions apply to the web interface, the REST API and GraphQL alike. Constraints (for example
`{"contract__tenant__name": "ACME"}`) limit the objects an action covers in all three.

## Actions

| Action | Allows |
|---|---|
| `view` | Seeing the object in lists, detail pages, the REST API and GraphQL. Without it the object is hidden everywhere, including in tables of other objects, and GraphQL relations to it come back empty. |
| `add` | Creating objects: add form, CSV import, bulk import, `POST` to the REST endpoint. |
| `change` | Editing objects: edit form, bulk edit, `PUT` / `PATCH`. |
| `delete` | Deleting objects: delete page, bulk delete, `DELETE`. The business rules still apply (see [Contract lines](contract_lines.md) and [Invoice](invoice.md)). |
| `amend` | Amending the price or quantity of an invoiced contract line (contract lines only). |

Like any NetBox user, an operator also needs the standard permissions of NetBox itself for what they do next to the
plugin: for example *journal entries* (add) to write journal entries on a plugin object, and *view* on the NetBox objects
(tenant, provider, device, ...) that contracts reference or are assigned to.

## The amend action

Amending a contract line ends it and creates a successor line with the new unit price or quantity (see
[Contract lines](contract_lines.md#amending-a-contract-line)). It has its own permission because it is neither a plain add
nor a plain change.

- Tick **amend** on *Netbox contract | contract line*, **together with `view`**. The add and change actions are not
  needed and are not enough.
- Constraints are honoured per line: a user who may amend only the lines of some contracts sees the **Amend** button
  only on those lines, and gets *not found* on the others.
- A line outside the user's `view` constraints is invisible to them, so it cannot be amended even if the `amend` action
  covers it.
- REST: `POST /api/plugins/contracts/contract-lines/{id}/amend/` needs `view` and `amend` on the line and a write-enabled
  token. A user without any amend permission gets 403; a line they cannot see or amend returns 404.

## Other things that depend on permissions

**Navigation.** The *Contracts* menu entries are shown with `view` on their object type, and the "add" buttons of the
menu with `add` on it (*Invoices* and its entries use the invoice permissions, *Contract assignments* uses
`view_contractassignment`).

**Creating an invoice.** The new-invoice form proposes values and a preview of the lines to generate, taken from the
contract in the page address or selected in the form. Only a contract the user may **view** (constraints included) is
used; for any other contract nothing is proposed. The preview is refreshed with a POST that needs the **add**
permission on invoices and saves nothing. The invoice lines are generated when the invoice is saved, so the `add`
permission on *Invoice* is enough; no `add` on *Invoice line* is needed for the generated lines. The pre-fill of a new
invoice line from the invoice in the page address works the same way, and needs `view` on that invoice.

**Contracts tab and assignments.** The **Contracts** tab on devices, sites, racks, circuits, virtual machines, clusters
and virtual circuits appears with `view` on *Contract assignment*. The contract list inside the tab needs `view` on
*Contract*, and the **Add** button there needs `add` on *Contract assignment*.

**Detail page panels.** Related tables on a contract page (lines, invoices, assignments) are loaded separately and are
hidden when the user lacks `view` on the related type.

**Custom scripts.** The plugin ships custom scripts (*Update expired contracts status*, *Report currency mismatches*,
*Replace accounting dimension*, *Check contract end*). Scripts are governed by NetBox, not by the plugin: the user needs
the **run** action on *Extras | script* (and the script is run with that user's rights; the changes it makes are logged
under their name). Scripts that change contract data (for example *Update expired contracts status* and *Replace accounting dimension*) should be given only to roles that may change that data; *Report currency mismatches* is read-only.

**Management command.** `manage.py convert_contract_lines` is a server-side command for administrators. It does not
go through object permissions.

## Troubleshooting

- **A user does not see the Contracts menu or a list is empty.** Check the `view` action on the object type and its
  constraints.
- **The Amend button is missing.** The user needs `view` and `amend` on contract lines (not `add` + `change`), the line
  must be amendable (a recurring or usage-based line with an invoice), and the line must be inside the constraints of
  the amend permission.
- **`403` on `POST .../amend/` with a valid token.** The token is read-only, or the user has no amend permission at all.
- **`404` on the same call.** The line is outside the view or amend constraints of the user.
