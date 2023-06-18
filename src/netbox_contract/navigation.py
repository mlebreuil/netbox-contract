from django.conf import settings
from extras.plugins import PluginMenu, PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices

plugin_settings = settings.PLUGINS_CONFIG["netbox_contract"]

contract_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:contract_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN,
        permissions=['netbox_contract.add_contract']
    )
]

invoice_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:invoice_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN,
        permissions=['netbox_contract.add_invoice']
    )
]

serviceprovider_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:serviceprovider_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN,
        permissions=['netbox_contract.add_serviceprovider']
    )
]

contract_menu_item = PluginMenuItem(
        link='plugins:netbox_contract:contract_list',
        link_text='Contracts',
        buttons=contract_buttons,
        permissions=['netbox_contract.view_contract']
    )

invoices_menu_item = PluginMenuItem(
        link='plugins:netbox_contract:invoice_list',
        link_text='Invoices',
        buttons=invoice_buttons,
        permissions=['netbox_contract.view_invoice']
    )

service_provider_menu_item = PluginMenuItem(
        link='plugins:netbox_contract:serviceprovider_list',
        link_text='Service Providers',
        buttons=serviceprovider_buttons,
        permissions=['netbox_contract.view_serviceprovider']
    )
contract_assignemnt_menu_item = PluginMenuItem(
        link='plugins:netbox_contract:contractassignement_list',
        link_text='Contract assignements',
        permissions=['netbox_contract.view_contractassignement']
    )

items = (contract_menu_item,invoices_menu_item,service_provider_menu_item, contract_assignemnt_menu_item)

if plugin_settings.get("top_level_menu"):
    menu = PluginMenu(
        label="Contracts",
        groups=(("Contracts", items),),
        icon_class="mdi mdi-file-sign",
    )
else:
    menu_items = items
