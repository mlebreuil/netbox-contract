from django.conf import settings
from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

plugin_settings = settings.PLUGINS_CONFIG['netbox_contracts']

contract_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:contract_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_contract'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:contract_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_contract'],
    )
]

contracttype_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:contracttype_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_contract'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:contracttype_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_contract'],
    )
]

provider_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:provider_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['circuits.add_provider'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:provider_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['circuits.add_provider'],
    )
]

servicelevelagreement_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:servicelevelagreement_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_servicelevelagreement'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:servicelevelagreement_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_servicelevelagreement'],
    )
]

provideraccount_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:provideraccount_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['circuits.add_provideraccount'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:provideraccount_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['circuits.add_provideraccount'],
    )
]

contractassingmenttype_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:contractassignment_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_contractassignment'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:contractassignment_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_contractassignment'],
    )
]

currency_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:currency_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_contract'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:currency_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_contract'],
    )
]

softwarelicense_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:softwarelicense_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_softwarelicense'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:softwarelicense_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_softwarelicense'],
    )
]

licensetype_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:licensetype_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_licensetype'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:licensetype_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_licensetype'],
    )
]

licenseassignment_buttons = [
    PluginMenuButton(
        link='plugins:netbox_contracts:licenseassignment_add',
        title=_('Add'),
        icon_class='mdi mdi-plus-thick',
        permissions=['netbox_contracts.add_licenseassignment'],
    ),
    PluginMenuButton(
        link='plugins:netbox_contracts:licenseassignment_bulk_import',
        title=_('Import'),
        icon_class="mdi mdi-upload",
        permissions=['netbox_contracts.add_licenseassignment'],
    )
]

contract_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:contract_list',
    link_text=_('Contracts'),
    buttons=contract_buttons,
    permissions=['netbox_contracts.view_contract'],
)

contracttype_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:contracttype_list',
    link_text=_('Contract Types'),
    buttons=contracttype_buttons,
    permissions=['netbox_contracts.view_contract'],
)

provider_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:provider_list',
    link_text=_('Providers'),
    buttons=provider_buttons,
    permissions=['circuits.view_provider'],
)

provideraccount_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:provideraccount_list',
    link_text=_('Provider Accounts'),
    buttons=provideraccount_buttons,
    permissions=['circuits.view_provideraccount'],
)

contract_assignemnt_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:contractassignment_list',
    link_text=_('Contract Assignments'),
    buttons=contractassingmenttype_buttons,
    permissions=['netbox_contracts.view_contractassignment'],
)

servicelevelagreement_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:servicelevelagreement_list',
    link_text=_('Service Level Agreements'),
    buttons=servicelevelagreement_buttons,
    permissions=['netbox_contracts.view_servicelevelagreement'],
)

currency_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:currency_list',
    link_text=_('Currencies'),
    buttons=currency_buttons,
    permissions=['netbox_contracts.view_contract'],
)

softwarelicense_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:softwarelicense_list',
    link_text=_('Software Licenses'),
    buttons=softwarelicense_buttons,
    permissions=['netbox_contracts.view_softwarelicense'],
)

licenseassignment_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:licenseassignment_list',
    link_text=_('License Assignments'),
    buttons=licenseassignment_buttons,
    permissions=['netbox_contracts.view_licenseassignment'],
)

licensetype_menu_item = PluginMenuItem(
    link='plugins:netbox_contracts:licensetype_list',
    link_text=_('License Types'),
    buttons=licensetype_buttons,
    permissions=['netbox_contracts.view_licensetype'],
)

software_items = (
    softwarelicense_menu_item,
    licenseassignment_menu_item,
    licensetype_menu_item,
)

items = (
    contract_menu_item,
    contract_assignemnt_menu_item,
    contracttype_menu_item,
    provider_menu_item,
    provideraccount_menu_item,
    servicelevelagreement_menu_item,
    currency_menu_item,
)

if plugin_settings.get('top_level_menu'):
    menu = PluginMenu(
        label=_('SCB Operations'),
        groups=(
            ('Contracts', items),
            ('Software', software_items),
        ),
        icon_class='mdi mdi-file-sign',
    )
else:
    menu_items = items + software_items
