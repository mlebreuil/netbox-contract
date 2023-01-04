from extras.plugins import PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices

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

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_contract:contract_list',
        link_text='Contracts',
        buttons=contract_buttons
    ),
    PluginMenuItem(
        link='plugins:netbox_contract:invoice_list',
        link_text='Invoices',
        buttons=invoice_buttons
    ),
    PluginMenuItem(
        link='plugins:netbox_contract:serviceprovider_list',
        link_text='Service Providers',
        buttons=serviceprovider_buttons
    ),
)
