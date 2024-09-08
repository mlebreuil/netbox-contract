# Accounting dimensions

> [!NOTE]
> account is considered a accounting dimensions as any other.

It is possible through the plugin config  attribure 'mandatory_dimensions' to set some mandatory dimensions. the attribute will take a list of dimension names. For instance:

```python
# configuration.py
PLUGINS_CONFIG = {
    'netbox_contract': {
        'top_level_menu': True,
        'mandatory_contract_fields': [],
        'hidden_contract_fields': [],
        'mandatory_invoice_fields': [],
        'hidden_invoice_fields': [],
        'mandatory_dimensions': ['account','project'],
    }
}

```

Refer to the readme file for more information.

> [!WARNING]
> Accounting dimensions used to be set with a simple json field. Although the field is still available, it is recommended to add dimensions through invoice lines. You will find in the script folder a file which can be imported as netbox custom scripts module which contains a script to perform the migration. You wil need to adjust the script to your needs.

![Accounting dimensions](img/accrounting_dimensions.png "accounting dimensions")

- name: The name of the accounting dimensions (Account, Project, Entity ...)
- value: The value for this dimension.
- status: If the accounting dimension can still be used for new invoice lines.
- Comments: Self explanatory


