"""
Invoice checks shared by the invoice form and the invoice API serializer (research D4).

The many-to-many relation between invoices and contracts is saved after the invoice itself,
so these rules cannot live in Invoice.clean(). The functions take plain values and objects that
are already loaded, run no query, and return a list of error messages.
"""

from django.utils.translation import gettext as _


def currency_label(code):
    return (code or '').upper()


def check_invoice_contracts(is_new, contracts, currency, previous_contract_ids=(), previous_currency=None):
    """
    - a new invoice is linked to at most one contract (FR-011);
    - an existing invoice cannot be linked to more contracts than it had (at least one);
    - the invoice currency equals the currency of each of its contracts (FR-009), checked for a new invoice
      and whenever the currency or the contracts change, so that existing mismatches stay editable.
    """
    errors = []
    contracts = list(contracts or ())
    if is_new:
        if len(contracts) > 1:
            errors.append(_('A new invoice can be linked to one contract only.'))
    elif len(contracts) > max(len(previous_contract_ids), 1):
        errors.append(
            _('This invoice is linked to {count} contract(s); no contract can be added to it.').format(
                count=len(previous_contract_ids)
            )
        )

    contract_ids = {contract.pk for contract in contracts}
    if is_new or currency != previous_currency or contract_ids != set(previous_contract_ids):
        for contract in contracts:
            if contract.currency != currency:
                errors.append(
                    _('The invoice currency {found} differs from the currency {expected} of the contract {contract}.')
                    .format(
                        found=currency_label(currency),
                        expected=currency_label(contract.currency),
                        contract=contract,
                    )
                )
    return errors
