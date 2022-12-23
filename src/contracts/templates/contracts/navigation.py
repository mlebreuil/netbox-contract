from extras.plugins import PluginMenuItem
from extras.plugins import PluginMenuButton, PluginMenuItem
from utilities.choices import ButtonColorChoices

menu_items = (
    PluginMenuItem(
        link='plugins:contracts:contract_list',
        link_text='Contracts',
        buttons=contract_buttons
    ),
    PluginMenuItem(
        link='plugins:contracts:contractinvoice_list',
        link_text='Contracts invoices',
        buttons=contractinvoice_butons  
    ),
)

contract_buttons = [
    PluginMenuButton(
        link='plugins:contracts:contract_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]

contractinvoice_butons = [
    PluginMenuButton(
        link='plugins:contracts:contractinvoice_add',
        title='Add',
        icon_class='mdi mdi-plus-thick',
        color=ButtonColorChoices.GREEN
    )
]
