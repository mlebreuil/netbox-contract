from circuits.models import Circuit, VirtualCircuit
from dcim.models import Device, Site
from django.contrib.contenttypes.models import ContentType
from netbox.plugins import PluginTemplateExtension
from virtualization.models import VirtualMachine

from . import tables
from .models import ContractAssignment


class CircuitContractAssignments(PluginTemplateExtension):
    models = ['circuits.circuit']

    def full_width_page(self):
        circuit = self.context['object']
        circuit_type = ContentType.objects.get_for_model(Circuit)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=circuit_type.id, object_id=circuit.id
        )
        assignments_table = tables.ContractAssignmentObjectTable(contract_assignments)
        assignments_table.configure(self.context['request'])

        return self.render(
            'contract_assignments_bottom.html',
            extra_context={
                'assignments_table': assignments_table,
            },
        )


class DeviceContractAssignments(PluginTemplateExtension):
    models = ['dcim.device']

    def full_width_page(self):
        device = self.context['object']
        device_type = ContentType.objects.get_for_model(Device)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=device_type.id, object_id=device.id
        )
        assignments_table = tables.ContractAssignmentObjectTable(contract_assignments)
        assignments_table.configure(self.context['request'])

        return self.render(
            'contract_assignments_bottom.html',
            extra_context={
                'assignments_table': assignments_table,
            },
        )


class VMContractAssignments(PluginTemplateExtension):
    models = ['virtualization.virtualmachine']

    def full_width_page(self):
        vm = self.context['object']
        vm_type = ContentType.objects.get_for_model(VirtualMachine)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=vm_type.id, object_id=vm.id
        )
        assignments_table = tables.ContractAssignmentObjectTable(contract_assignments)
        assignments_table.configure(self.context['request'])

        return self.render(
            'contract_assignments_bottom.html',
            extra_context={
                'assignments_table': assignments_table,
            },
        )


class SiteContractAssignments(PluginTemplateExtension):
    models = ['dcim.site']

    def full_width_page(self):
        site = self.context['object']
        site_type = ContentType.objects.get_for_model(Site)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=site_type.id, object_id=site.id
        )
        assignments_table = tables.ContractAssignmentObjectTable(contract_assignments)
        assignments_table.configure(self.context['request'])

        return self.render(
            'contract_assignments_bottom.html',
            extra_context={
                'assignments_table': assignments_table,
            },
        )


class VirtualCircuitContractAssignments(PluginTemplateExtension):
    models = ['circuits.virtualcircuit']

    def full_width_page(self):
        virtualcircuit = self.context['object']
        virtualcircuit_type = ContentType.objects.get_for_model(VirtualCircuit)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=virtualcircuit_type.id, object_id=virtualcircuit.id
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
    CircuitContractAssignments,
    DeviceContractAssignments,
    VMContractAssignments,
    SiteContractAssignments,
    VirtualCircuitContractAssignments,
]
