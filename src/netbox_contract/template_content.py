from circuits.models import Circuit
from dcim.models import Device, Site
from django.contrib.contenttypes.models import ContentType
from extras.plugins import PluginTemplateExtension
from virtualization.models import VirtualMachine

from . import tables
from .models import ContractAssignement


class CircuitContractAssignements(PluginTemplateExtension):
    model = 'circuits.circuit'

    def full_width_page(self):
        circuit = self.context['object']
        circuit_type = ContentType.objects.get_for_model(Circuit)
        contract_assignements = ContractAssignement.objects.filter(
            content_type__pk=circuit_type.id, object_id=circuit.id
        )
        assignements_table = tables.ContractAssignementObjectTable(
            contract_assignements
        )
        assignements_table.configure(self.context['request'])

        return self.render(
            'contract_assignements_bottom.html',
            extra_context={
                'assignements_table': assignements_table,
            },
        )


class DeviceContractAssignements(PluginTemplateExtension):
    model = 'dcim.device'

    def full_width_page(self):
        device = self.context['object']
        device_type = ContentType.objects.get_for_model(Device)
        contract_assignements = ContractAssignement.objects.filter(
            content_type__pk=device_type.id, object_id=device.id
        )
        assignements_table = tables.ContractAssignementObjectTable(
            contract_assignements
        )
        assignements_table.configure(self.context['request'])

        return self.render(
            'contract_assignements_bottom.html',
            extra_context={
                'assignements_table': assignements_table,
            },
        )


class VMContractAssignements(PluginTemplateExtension):
    model = 'virtualization.virtualmachine'

    def full_width_page(self):
        vm = self.context['object']
        vm_type = ContentType.objects.get_for_model(VirtualMachine)
        contract_assignements = ContractAssignement.objects.filter(
            content_type__pk=vm_type.id, object_id=vm.id
        )
        assignements_table = tables.ContractAssignementObjectTable(
            contract_assignements
        )
        assignements_table.configure(self.context['request'])

        return self.render(
            'contract_assignements_bottom.html',
            extra_context={
                'assignements_table': assignements_table,
            },
        )


class SiteContractAssignements(PluginTemplateExtension):
    model = 'dcim.site'

    def full_width_page(self):
        site = self.context['object']
        site_type = ContentType.objects.get_for_model(Site)
        contract_assignements = ContractAssignement.objects.filter(
            content_type__pk=site_type.id, object_id=site.id
        )
        assignements_table = tables.ContractAssignementObjectTable(
            contract_assignements
        )
        assignements_table.configure(self.context['request'])

        return self.render(
            'contract_assignements_bottom.html',
            extra_context={
                'assignements_table': assignements_table,
            },
        )


template_extensions = [
    CircuitContractAssignements,
    DeviceContractAssignements,
    VMContractAssignements,
    SiteContractAssignements,
]
