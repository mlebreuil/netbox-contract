from extras.plugins import PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices

contract_buttons = [
    PluginMenuButton(
        link='plugins:contracts:contract_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

invoice_butons = [
    PluginMenuButton(
        link='plugins:contracts:invoice_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

menu_items = (
    PluginMenuItem(
        link='plugins:contracts:contract_list',
        link_text='Contracts',
        buttons=contract_buttons
    ),
    PluginMenuItem(
        link='plugins:contracts:invoice_list',
        link_text='Invoices',
        buttons=invoice_butons
    ),
)
