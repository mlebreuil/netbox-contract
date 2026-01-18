from django.contrib.contenttypes.models import ContentType
from netbox.plugins import PluginTemplateExtension

from . import tables
from .models import ContractAssignment
from .constants import ASSIGNEMENT_TYPES


class ObjectContractAssignments(PluginTemplateExtension):
    models = ASSIGNEMENT_TYPES

    def full_width_page(self):
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


template_extensions = [
    ObjectContractAssignments,
]
