from django.conf import settings
from extras.plugins import PluginMenu, PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices

plugin_settings = settings.PLUGINS_CONFIG["netbox_contract"]

contract_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:contract_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

invoice_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:invoice_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

serviceprovider_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contract:serviceprovider_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]
 
contract_menu_item = PluginMenuItem(
        link='plugins:netbox_contract:contract_list',
        link_text='Contracts',
        buttons=contract_buttons
    )

invoices_menu_item = PluginMenuItem(
        link='plugins:netbox_contract:invoice_list',
        link_text='Invoices',
        buttons=invoice_buttons
    )

service_provider_menu_item = PluginMenuItem(
        link='plugins:netbox_contract:serviceprovider_list',
        link_text='Service Providers',
        buttons=serviceprovider_buttons
    )

items = (contract_menu_item,invoices_menu_item,service_provider_menu_item)

if plugin_settings.get("top_level_menu"):
    menu = PluginMenu(
        label="Contracts",
        groups=(("Contracts", items),),
        icon_class="mdi mdi-file-sign",
    )
else:
    menu_items = items
