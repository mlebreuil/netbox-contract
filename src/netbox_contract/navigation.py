from django.conf import settings
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

plugin_settings = settings.PLUGINS_CONFIG['netbox_contract']

contract_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:contract_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_contract'],
    )
]

invoice_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:invoice_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_invoice'],
    )
]

invoiceline_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:invoiceline_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_invoice'],
    )
]

accountingdimension_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:accountingdimension_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_invoice'],
    )
]

serviceprovider_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:serviceprovider_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contract.add_serviceprovider'],
    )
]

contract_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:contract_list',
    link_text='Contracts',
    buttons=contract_buttons,
    permissions=['netbox_contract.view_contract'],
)

invoices_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:invoice_list',
    link_text='Invoices',
    buttons=invoice_buttons,
    permissions=['netbox_contract.view_invoice'],
)

invoicelines_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:invoiceline_list',
    link_text='Invoice lines',
    buttons=invoiceline_buttons,
    permissions=['netbox_contract.view_invoice'],
)

accounting_dimensions_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:accountingdimension_list',
    link_text='Accounting dimensions',
    buttons=accountingdimension_buttons,
    permissions=['netbox_contract.view_invoice'],
)

service_provider_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:serviceprovider_list',
    link_text='Service Providers',
    buttons=serviceprovider_buttons,
    permissions=['netbox_contract.view_serviceprovider'],
)
contract_assignemnt_menu_item = PluginMenuItem(
    link='plugins:netbox_contract:contractassignment_list',
    link_text='Contract assignments',
    permissions=['netbox_contract.view_contractassignment'],
)

items = (
    contract_menu_item,
    invoices_menu_item,
    invoicelines_menu_item,
    accounting_dimensions_menu_item,
    service_provider_menu_item,
    contract_assignemnt_menu_item,
)

if plugin_settings.get('top_level_menu'):
    menu = PluginMenu(
        label='Contracts',
        groups=(('Contracts', items),),
        icon_class='mdi mdi-file-sign',
    )
else:
    menu_items = items
