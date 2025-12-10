from circuits.models import Circuit, VirtualCircuit, Provider
from dcim.models import Device, Site, Rack
from django.contrib.contenttypes.models import ContentType
from netbox.plugins import PluginTemplateExtension
from virtualization.models import VirtualMachine, Cluster

from . import tables
from .models import ContractAssignment, Contract


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


class ProviderContracts(PluginTemplateExtension):
    models = ['circuits.provider']

    def full_width_page(self):
        provider = self.context['object']
        provider_type = ContentType.objects.get_for_model(Provider)
        contracts = Contract.objects.filter(
            external_party_object_type__pk=provider_type.id,
            external_party_object_id=provider.id
        )

        contracts_table = tables.ContractProviderBottomTable(contracts)
        contracts_table.configure(self.context['request'])

        return self.render(
            'contract_list_bottom.html',
            extra_context={
                'contracts_table': contracts_table,
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


class RackContractAssignments(PluginTemplateExtension):
    models = ['dcim.rack']

    def full_width_page(self):
        rack = self.context['object']
        rack_type = ContentType.objects.get_for_model(Rack)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=rack_type.id, object_id=rack.id
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


class ClusterContractAssignments(PluginTemplateExtension):
    models = ['virtualization.cluster']

    def full_width_page(self):
        cluster = self.context['object']
        cluster_type = ContentType.objects.get_for_model(Cluster)
        contract_assignments = ContractAssignment.objects.filter(
            content_type__pk=cluster_type.id, object_id=cluster.id
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
    VirtualCircuitContractAssignments,
    ProviderContracts,
    DeviceContractAssignments,
    SiteContractAssignments,
    RackContractAssignments,
    VMContractAssignments,
    ClusterContractAssignments,
]
