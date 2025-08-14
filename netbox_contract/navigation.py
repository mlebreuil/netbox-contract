from django.conf import settings
from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']

contract_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:contract_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_contract'],
    )
]

contracttype_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:contracttype_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_contract'],
    )
]

invoice_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:invoice_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_invoice'],
    )
]

invoiceline_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:invoiceline_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_invoice'],
    )
]

accountingdimension_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:accountingdimension_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_invoice'],
    )
]

serviceprovider_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:serviceprovider_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_serviceprovider'],
    )
]

contract_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:contract_list',
    link_text=_('Contracts'),
    buttons=contract_buttons,
    permissions=['netbox_contract.view_contract'],
)

contracttype_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:contracttype_list',
    link_text=_('Contract type'),
    buttons=contracttype_buttons,
    permissions=['netbox_contract.view_contract'],
)

invoices_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:invoice_list',
    link_text=_('Invoices'),
    buttons=invoice_buttons,
    permissions=['netbox_contract.view_invoice'],
)

invoicelines_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:invoiceline_list',
    link_text=_('Invoice lines'),
    buttons=invoiceline_buttons,
    permissions=['netbox_contract.view_invoice'],
)

accounting_dimensions_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:accountingdimension_list',
    link_text=_('Accounting dimensions'),
    buttons=accountingdimension_buttons,
    permissions=['netbox_contract.view_invoice'],
)

service_provider_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:serviceprovider_list',
    link_text=_('Service providers'),
    buttons=serviceprovider_buttons,
    permissions=['netbox_contract.view_serviceprovider'],
)
contract_assignemnt_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:contractassignment_list',
    link_text=_('Contracts assignments'),
    permissions=['netbox_contract.view_contractassignment'],
)

items = (
    contract_menu_item,
    contracttype_menu_item,
    invoices_menu_item,
    invoicelines_menu_item,
    accounting_dimensions_menu_item,
    service_provider_menu_item,
    contract_assignemnt_menu_item,
)

if plugin_settings.get('top_level_menu'):
    menu = PluginMenu(
        label=_('Contracts'),
        groups=(('Contracts', items),),
        icon_class='mdi mdi-file-sign',
    )
else:
    menu_items = items
