from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from netbox.plugins import PluginTemplateExtension

from . import tables
from .constants import ASSIGNEMENT_TYPES
from .models import ContractAssignment


class ObjectContractAssignments(PluginTemplateExtension):
    models = ASSIGNEMENT_TYPES

    def full_width_page(self):
        display = settings.PLUGINS_CONFIG.get('netbox_contract', {}).get(
            'contract_assignments_display', 'both'
        )

        # 'tab' means only the contract tab is shown; inline table stays hidden.
        if display == 'tab':
            return ''

        # 'inline' or 'both' renders inline table; the tab is still built via ObjectChildrenView.
        if display in ('inline', 'both'):
            object = self.context['object']
            object_type = ContentType.objects.get_for_model(object)

            contract_assignments = ContractAssignment.objects.filter(
                content_type__pk=object_type.id, object_id=object.id
            )
            assignments_table = tables.ContractAssignmentObjectTable(contract_assignments)
            assignments_table.configure(self.context['request'])

            return self.render(
                'contract_assignments_bottom.html',
                extra_context={
                    'assignments_table': assignments_table,
                },
            )

        return ''


template_extensions = [
    ObjectContractAssignments,
]
