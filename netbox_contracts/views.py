from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, F, When
from netbox.views import generic
from utilities.query import count_related
from utilities.querydict import normalize_querydict
from utilities.views import register_model_view, GetRelatedModelsMixin, ViewTab
from circuits.models import Circuit, Provider, ProviderAccount, VirtualCircuit
from circuits.tables import ProviderTable, ProviderAccountTable
from circuits.filtersets import ProviderFilterSet, ProviderAccountFilterSet
from circuits.forms import ProviderImportForm, ProviderAccountImportForm, ProviderFilterForm, ProviderForm, ProviderBulkEditForm, ProviderAccountFilterForm, ProviderAccountForm, ProviderAccountBulkEditForm
from dcim.models import Device
from . import filtersets, forms, tables
from .models import (
    Contract,
    ContractAssignment,
    ContractType,
    ServiceLevelAgreement,
    Currency,
    LicenseAssignment,
    LicenseType,
    SoftwareLicense,
)
from ipam.models import ASN
from django.db.models.functions import Round
from virtualization.models import VirtualMachine



# from .constants import (
#     CONTRACT_STATUS_ACTIVE,
#     CONTRACT_STATUS_EXPIRED,
#     CONTRACT_STATUS_FUTURE,
#     CONTRACT_STATUS_UNSPECIFIED,
# )

plugin_settings = settings.PLUGINS_CONFIG['netbox_contracts']

#
# ContractType views
#
@register_model_view(ContractType)
class ContractTypeView(generic.ObjectView):
    queryset = ContractType.objects.all()

@register_model_view(ContractType, name='list')
class ContractTypeListView(generic.ObjectListView):
    queryset = ContractType.objects.all()
    table = tables.ContractTypeListTable
    filterset = filtersets.ContractTypeFilterSet
    filterset_form = forms.ContractTypeFilterForm

@register_model_view(ContractType, name='edit')
class ContractTypeEditView(generic.ObjectEditView):
    queryset = ContractType.objects.all()
    form = forms.ContractTypeForm

@register_model_view(ContractType, name='bulk_import')
class ContractTypeBulkImportView(generic.BulkImportView):
    queryset = ContractType.objects.all()
    model_form = forms.ContractTypeCSVForm
    table = tables.ContractTypeListTable

@register_model_view(ContractType, name='bulk_edit')
class ContractTypeBulkEditView(generic.BulkEditView):
    queryset = ContractType.objects.annotate()
    filterset = filtersets.ContractTypeFilterSet
    table = tables.ContractTypeListTable
    form = forms.ContractTypeBulkEditForm

@register_model_view(ContractType, name='delete')
class ContractTypeDeleteView(generic.ObjectDeleteView):
    queryset = ContractType.objects.all()

@register_model_view(ContractType, name='bulk_delete')
class ContractTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = ContractType.objects.annotate()
    filterset = filtersets.ContractTypeFilterSet
    table = tables.ContractTypeListTable
#
# Contract assignment view
#
@register_model_view(ContractAssignment)
class ContractAssignmentView(generic.ObjectView):
    queryset = ContractAssignment.objects.all()

@register_model_view(ContractAssignment, name='list')
class ContractAssignmentListView(generic.ObjectListView):
    queryset = ContractAssignment.objects.all()
    table = tables.ContractAssignmentListTable
    filterset = filtersets.ContractAssignmentFilterSet
    filterset_form = forms.ContractAssignmentFilterForm

@register_model_view(ContractAssignment, name='edit')
class ContractAssignmentEditView(generic.ObjectEditView):
    queryset = ContractAssignment.objects.all()
    form = forms.ContractAssignmentForm

    def alter_object(self, obj, request, url_args, url_kwargs):
        """
        When this method is called after a Post,
        it is used here to set the external party object id for exiting objects,
        In any case, this happens before the form is instanciated.

        Args:
            obj: The object being edited
            request: The current request
            url_args: URL path args
            url_kwargs: URL path kwargs
        """

        if request.method == 'POST':
            data = normalize_querydict(request.POST)
            obj.object_id = data['object']
            object_type_id = data['object_type']
            obj.object_type = ContentType.objects.get(
                id=object_type_id
            )

        return obj

@register_model_view(ContractAssignment, name='delete')
class ContractAssignmentDeleteView(generic.ObjectDeleteView):
    queryset = ContractAssignment.objects.all()

@register_model_view(ContractAssignment, name='bulk_import')
class ContractAssignmentBulkImportView(generic.BulkImportView):
    queryset = ContractAssignment.objects.all()
    model_form = forms.ContractAssignmentImportForm
    table = tables.ContractAssignmentListTable

@register_model_view(ContractAssignment, name='bulk_edit')
class ContractAssignmentBulkEditView(generic.BulkEditView):
    queryset = ContractAssignment.objects.annotate()
    filterset = filtersets.ContractAssignmentFilterSet
    table = tables.ContractAssignmentListTable
    form = forms.ContractAssignmentBulkEditForm

@register_model_view(ContractAssignment, name='bulk_delete')
class ContractAssignmentBulkDeleteView(generic.BulkDeleteView):
    queryset = ContractAssignment.objects.annotate()
    filterset = filtersets.ContractAssignmentFilterSet
    table = tables.ContractAssignmentListTable
#
# Contract views
#
@register_model_view(Contract)
class ContractView(generic.ObjectView):
    queryset = Contract.objects.annotate(
        count_circuits=count_related(Circuit, 'id'),
        count_devices=count_related(Device,'id')
    )

@register_model_view(Contract, name='list')
class ContractListView(generic.ObjectListView):
    queryset = Contract.objects.annotate(
        calculated_rc=Round(
            Case(When(yrc__gt=0, then=F('yrc') / 12), default=F('yrc') / 12),
            precision=2,
        ),
        assgined_count=count_related(ContractAssignment, 'contract'),
    )
    table = tables.ContractListTable
    filterset = filtersets.ContractFilterSet
    filterset_form = forms.ContractFilterForm

@register_model_view(Contract, name='edit')
class ContractEditView(generic.ObjectEditView):
    queryset = Contract.objects.all()
    form = forms.ContractForm

@register_model_view(Contract, name='delete')
class ContractDeleteView(generic.ObjectDeleteView):
    queryset = Contract.objects.all()

@register_model_view(Contract, name='bulk_import')
class ContractBulkImportView(generic.BulkImportView):
    queryset = Contract.objects.all()
    model_form = forms.ContractCSVForm
    table = tables.ContractListTable

@register_model_view(Contract, name='bulk_edit')
class ContractBulkEditView(generic.BulkEditView):
    queryset = Contract.objects.all()
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable
    form = forms.ContractBulkEditForm

@register_model_view(Contract, name='bulk_delete')
class ContractBulkDeleteView(generic.BulkDeleteView):
    queryset = Contract.objects.all()
    filterset = filtersets.ContractFilterSet
    table = tables.ContractListTable
#
# Provider views
#
@register_model_view(Provider, 'list', path='', detail=False)
class ProviderListView(generic.ObjectListView):
    queryset = Provider.objects.annotate(
        count_circuits=count_related(Circuit, 'id'),
        asn_count=count_related(ASN, 'id'),
        account_count=count_related(ProviderAccount, 'id'),
        count_devices=count_related(Device,'id')
    )
    filterset = ProviderFilterSet
    filterset_form = ProviderFilterForm
    table = ProviderTable

@register_model_view(Provider)
class ProviderView(GetRelatedModelsMixin, generic.ObjectView):
    queryset = Provider.objects.all()

    def get_extra_context(self, request, instance):
        return {
            'related_models': self.get_related_models(
                request,
                instance,
                omit=(),
                extra=(
                    (
                        VirtualCircuit.objects.restrict(request.user, 'view').filter(
                            provider_network__provider=instance
                        ),
                        'provider_id',
                    ),
                ),
                ),
        }

@register_model_view(Provider, 'add', detail=False)
@register_model_view(Provider, 'edit')
class ProviderEditView(generic.ObjectEditView):
    queryset = Provider.objects.all()
    form = ProviderForm

@register_model_view(Provider, 'delete')
class ProviderDeleteView(generic.ObjectDeleteView):
    queryset = Provider.objects.all()

@register_model_view(Provider, 'bulk_import', path='import', detail=False)
class ProviderBulkImportView(generic.BulkImportView):
    queryset = Provider.objects.all()
    model_form = ProviderImportForm

@register_model_view(Provider, 'bulk_edit', path='edit', detail=False)
class ProviderBulkEditView(generic.BulkEditView):
    queryset = Provider.objects.annotate(
        count_circuits=count_related(Circuit, 'provider')
    )
    filterset = ProviderFilterSet
    table = ProviderTable
    form = ProviderBulkEditForm

@register_model_view(Provider, 'bulk_rename', path='rename', detail=False)
class ProviderBulkRenameView(generic.BulkRenameView):
    queryset = Provider.objects.all()
    filterset = ProviderFilterSet

@register_model_view(Provider, 'bulk_delete', path='delete', detail=False)
class ProviderBulkDeleteView(generic.BulkDeleteView):
    queryset = Provider.objects.annotate(
        count_circuits=count_related(Circuit, 'provider')
    )
    filterset = ProviderFilterSet
    table = ProviderTable
#
# ProviderAccounts
#
@register_model_view(ProviderAccount)
class ProviderAccountView(GetRelatedModelsMixin, generic.ObjectView):
    queryset = ProviderAccount.objects.all()

    def get_extra_context(self, request, instance):
        return {
            'related_models': self.get_related_models(request, instance),
        }

@register_model_view(ProviderAccount, 'list', path='', detail=False)
class ProviderAccountListView(generic.ObjectListView):
    queryset = ProviderAccount.objects.annotate(
        count_circuits=count_related(Circuit, 'provider_account')
    )
    filterset = ProviderAccountFilterSet
    filterset_form = ProviderAccountFilterForm
    table = ProviderAccountTable

@register_model_view(ProviderAccount, 'add', detail=False)
@register_model_view(ProviderAccount, 'edit')
class ProviderAccountEditView(generic.ObjectEditView):
    queryset = ProviderAccount.objects.all()
    form = ProviderAccountForm

@register_model_view(ProviderAccount, 'delete')
class ProviderAccountDeleteView(generic.ObjectDeleteView):
    queryset = ProviderAccount.objects.all()

@register_model_view(ProviderAccount, 'bulk_import', path='import', detail=False)
class ProviderAccountBulkImportView(generic.BulkImportView):
    queryset = ProviderAccount.objects.all()
    model_form = ProviderAccountImportForm
    table = ProviderAccountTable

@register_model_view(ProviderAccount, 'bulk_edit', path='edit', detail=False)
class ProviderAccountBulkEditView(generic.BulkEditView):
    queryset = ProviderAccount.objects.annotate(
        count_circuits=count_related(Circuit, 'provider_account')
    )
    filterset = ProviderAccountFilterSet
    table = ProviderAccountTable
    form = ProviderAccountBulkEditForm

@register_model_view(ProviderAccount, 'bulk_rename', path='rename', detail=False)
class ProviderAccountBulkRenameView(generic.BulkRenameView):
    queryset = ProviderAccount.objects.all()
    filterset = ProviderAccountFilterSet

@register_model_view(ProviderAccount, 'bulk_delete', path='delete', detail=False)
class ProviderAccountBulkDeleteView(generic.BulkDeleteView):
    queryset = ProviderAccount.objects.annotate(
        count_circuits=count_related(Circuit, 'provider_account')
    )
    filterset = ProviderAccountFilterSet
    table = ProviderAccountTable
#  
# Service Level Agreement views
#
@register_model_view(ServiceLevelAgreement)
class ServiceLevelAgreementView(generic.ObjectView):
    queryset = ServiceLevelAgreement.objects.all()  

@register_model_view(ServiceLevelAgreement, 'list')
class ServiceLevelAgreementListView(generic.ObjectListView):
    queryset = ServiceLevelAgreement.objects.all()
    table = tables.ServiceLevelAgreementListTable
    # filterset = filtersets.ServiceLevelAgreementFilterSet
    # filterset_form = forms.ServiceLevelAgreementFilterForm

@register_model_view(ServiceLevelAgreement, 'edit')
class ServiceLevelAgreementEditView(generic.ObjectEditView):
    queryset = ServiceLevelAgreement.objects.all()
    form = forms.ServiceLevelAgreementForm

@register_model_view(ServiceLevelAgreement, 'bulk_import')
class ServiceLevelAgreementBulkImportView(generic.BulkImportView):
    queryset = ServiceLevelAgreement.objects.all()
    model_form = forms.ServiceLevelAgreementImportForm
    table = tables.ServiceLevelAgreementListTable

@register_model_view(ServiceLevelAgreement, 'bulk_edit')
class ServiceLevelAgreementBulkEditView(generic.BulkEditView):
    queryset = ServiceLevelAgreement.objects.annotate()
    filterset = filtersets.ServiceLevelAgreementFilterSet
    table = tables.ServiceLevelAgreementListTable
    form = forms.ServiceLevelAgreementBulkEditForm

@register_model_view(ServiceLevelAgreement, 'delete')
class ServiceLevelAgreementDeleteView(generic.ObjectDeleteView):
    queryset = ServiceLevelAgreement.objects.all()
    table = tables.ServiceLevelAgreementListTable

@register_model_view(ServiceLevelAgreement, 'bulk_delete')
class ServiceLevelAgreementBulkDeleteView(generic.BulkDeleteView):
    queryset = ServiceLevelAgreement.objects.annotate()
    filterset = filtersets.ServiceLevelAgreementFilterSet
    table = tables.ServiceLevelAgreementListTable
#
# Currency views
#
@register_model_view(Currency)
class CurrencyView(generic.ObjectView):
    queryset = Currency.objects.all()

@register_model_view(Currency, name='list')
class CurrencyListView(generic.ObjectListView):
    queryset = Currency.objects.all()
    table = tables.CurrencyListTable
    filterset = filtersets.CurrencyFilterSet
    filterset_form = forms.CurrencyFilterForm

@register_model_view(Currency, name='edit')
class CurrencyEditView(generic.ObjectEditView):
    queryset = Currency.objects.all()
    form = forms.CurrencyForm

@register_model_view(Currency, name='delete')
class CurrencyDeleteView(generic.ObjectDeleteView):
    queryset = Currency.objects.all()

@register_model_view(Currency, name='bulk_import')
class CurrencyBulkImportView(generic.BulkImportView):
    queryset = Currency.objects.all()
    model_form = forms.CurrencyCSVForm
    table = tables.CurrencyListTable

@register_model_view(Currency, name='bulk_edit')
class CurrencyBulkEditView(generic.BulkEditView):
    queryset = Currency.objects.all()
    filterset = filtersets.CurrencyFilterSet
    table = tables.CurrencyListTable
    form = forms.CurrencyBulkEditForm

@register_model_view(Currency, name='bulk_delete')
class CurrencyBulkDeleteView(generic.BulkDeleteView):
    queryset = Currency.objects.all()
    filterset = filtersets.CurrencyFilterSet
    table = tables.CurrencyListTable
#
# Extentions to existing components
#
@register_model_view(Contract, name='assignments')
class ContractAssignmentTabView(generic.ObjectChildrenView):
    template_name = 'netbox_contracts/contractassignmentlist.html'
    queryset = Contract.objects.all()
    child_model = ContractAssignment
    table = tables.ContractAssignmentListTable
    filterset = filtersets.ContractAssignmentFilterSet
    actions = {'add': {'add'}, 'edit': {'change'}, 'delete': {'delete'}}
    tab = ViewTab(
        label='Assignments',
        badge=lambda obj: ContractAssignment.objects.filter(
            contract=obj
        ).count(),
    )

    def get_children(self, request, parent):
        return self.child_model.objects.filter(contract=parent)
    
@register_model_view(Device, name='contracts', path='contracts')
class DeviceContractsView(generic.ObjectChildrenView):
    queryset = Device.objects.all()
    child_model = ContractAssignment
    table = tables.ContractAssignmentObjectTable
    filterset = filtersets.ContractAssignmentFilterSet
    template_name = 'generic/object_children.html' # Standard NetBox template

    tab = ViewTab(
        label='Contracts',
        badge=lambda obj: ContractAssignment.objects.filter(
            object_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk
        ).count(),
        permission='netbox_contracts.view_contractassignment'
    )

    def get_children(self, request, parent):
        # Manually filter using the content type of the parent (Device)
        content_type = ContentType.objects.get_for_model(parent)
        return self.child_model.objects.filter(
            object_type=content_type,
            object_id=parent.pk
        )

@register_model_view(Circuit, name='contracts', path='contracts')
class CircuitContractsView(generic.ObjectChildrenView):
    queryset = Circuit.objects.all()
    child_model = ContractAssignment
    table = tables.ContractAssignmentObjectTable
    filterset = filtersets.ContractAssignmentFilterSet
    template_name = 'generic/object_children.html' # Standard NetBox template

    tab = ViewTab(
        label='Contracts',
        badge=lambda obj: ContractAssignment.objects.filter(
            object_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk
        ).count(),
        permission='netbox_contracts.view_contractassignment'
    )

    def get_children(self, request, parent):
        # Manually filter using the content type of the parent (Device)
        content_type = ContentType.objects.get_for_model(parent)
        return self.child_model.objects.filter(
            object_type=content_type,
            object_id=parent.pk
        )

@register_model_view(VirtualCircuit, name='contracts', path='contracts')
class VCircuitContractsView(generic.ObjectChildrenView):
    queryset = VirtualCircuit.objects.all()
    child_model = ContractAssignment
    table = tables.ContractAssignmentObjectTable
    filterset = filtersets.ContractAssignmentFilterSet
    template_name = 'generic/object_children.html' # Standard NetBox template

    tab = ViewTab(
        label='Contracts',
        badge=lambda obj: ContractAssignment.objects.filter(
            object_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk
        ).count(),
        permission='netbox_contracts.view_contractassignment'
    )

    def get_children(self, request, parent):
        # Manually filter using the content type of the parent (Device)
        content_type = ContentType.objects.get_for_model(parent)
        return self.child_model.objects.filter(
            object_type=content_type,
            object_id=parent.pk
        )

@register_model_view(VirtualMachine, name='contracts', path='contracts')
class VMachineView(generic.ObjectChildrenView):
    queryset = VirtualMachine.objects.all()
    child_model = ContractAssignment
    table = tables.ContractAssignmentObjectTable
    filterset = filtersets.ContractAssignmentFilterSet
    template_name = 'generic/object_children.html' # Standard NetBox template

    tab = ViewTab(
        label='Contracts',
        badge=lambda obj: ContractAssignment.objects.filter(
            object_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk
        ).count(),
        permission='netbox_contracts.view_contractassignment'
    )

    def get_children(self, request, parent):
        # Manually filter using the content type of the parent (Device)
        content_type = ContentType.objects.get_for_model(parent)
        return self.child_model.objects.filter(
            object_type=content_type,
            object_id=parent.pk
        )

# class DeviceContractsHTMXView(LoginRequiredMixin, View):
#     """HTMX endpoint for device contract card content."""

#     def get(self, request, pk):
#         device = get_object_or_404(Device, pk=pk)
#         assignments = ContractAssignment.objects.filter(
#             device=device
#         ).select_related(
#             'contract', 'contract__provider', 'end_date'
#         )

#         grouped = {
#             CONTRACT_STATUS_ACTIVE: [],
#             CONTRACT_STATUS_FUTURE: [],
#             CONTRACT_STATUS_UNSPECIFIED: [],
#             CONTRACT_STATUS_EXPIRED: [],
#         }
#         for assignment in assignments:
#             grouped[assignment.status].append(assignment)

#         return render(
#             request,
#             'netbox_contracts/device_contracts.html',
#             {
#                 'device': device,
#                 'active': grouped[CONTRACT_STATUS_ACTIVE],
#                 'future': grouped[CONTRACT_STATUS_FUTURE],
#                 'unspecified': grouped[CONTRACT_STATUS_UNSPECIFIED],
#                 'expired_count': len(grouped[CONTRACT_STATUS_EXPIRED]),
#             },
#         )

# class DeviceContractsExpiredHTMXView(LoginRequiredMixin, View):
#     """HTMX endpoint for expired contracts only."""

#     def get(self, request, pk):
#         device = get_object_or_404(Device, pk=pk)
#         expired = [
#             a
#             for a in ContractAssignment.objects.filter(
#                 device=device
#             ).select_related(
#                 'contract', 'contract__provider', 'end_date'
#             )
#             if a.status == CONTRACT_STATUS_EXPIRED
#         ]

#         return render(
#             request,
#             'netbox_contracts/contract_list.html',
#             {
#                 'assignments': expired,
#             },
#         )

# class VirtualMachineContractsHTMXView(LoginRequiredMixin, View):
#     """HTMX endpoint for virtual machine contract card content."""

#     def get(self, request, pk):
#         virtual_machine = get_object_or_404(VirtualMachine, pk=pk)
#         assignments = ContractAssignment.objects.filter(
#             virtual_machine=virtual_machine
#         ).select_related(
#             'contract', 'contract__vendor', 'sku', 'sku__manufacturer', 'license'
#         )

#         grouped = {
#             CONTRACT_STATUS_ACTIVE: [],
#             CONTRACT_STATUS_FUTURE: [],
#             CONTRACT_STATUS_UNSPECIFIED: [],
#             CONTRACT_STATUS_EXPIRED: [],
#         }
#         for assignment in assignments:
#             grouped[assignment.status].append(assignment)

#         return render(
#             request,
#             'netbox_contracts/virtualmachine_contracts.html',
#             {
#                 'virtual_machine': virtual_machine,
#                 'active': grouped[CONTRACT_STATUS_ACTIVE],
#                 'future': grouped[CONTRACT_STATUS_FUTURE],
#                 'unspecified': grouped[CONTRACT_STATUS_UNSPECIFIED],
#                 'expired_count': len(grouped[CONTRACT_STATUS_EXPIRED]),
#             },
#         )

# class VirtualMachineContractsExpiredHTMXView(LoginRequiredMixin, View):
#     """HTMX endpoint for expired contracts only (virtual machine)."""

#     def get(self, request, pk):
#         virtual_machine = get_object_or_404(VirtualMachine, pk=pk)
#         expired = [
#             a
#             for a in ContractAssignment.objects.filter(
#                 virtual_machine=virtual_machine
#             ).select_related(
#                 'contract', 'contract__vendor', 'sku', 'sku__manufacturer', 'license'
#             )
#             if a.status == CONTRACT_STATUS_EXPIRED
#         ]

#         return render(
#             request,
#             'netbox_contracts/contract_list.html',
#             {
#                 'assignments': expired,
#             },
#         )


#
# Software licensing
#
@register_model_view(LicenseType)
class LicenseTypeView(generic.ObjectView):
    queryset = LicenseType.objects.all()


@register_model_view(LicenseType, name='list')
class LicenseTypeListView(generic.ObjectListView):
    queryset = LicenseType.objects.all()
    table = tables.LicenseTypeTable
    filterset = filtersets.LicenseTypeFilterSet


@register_model_view(LicenseType, name='edit')
class LicenseTypeEditView(generic.ObjectEditView):
    queryset = LicenseType.objects.all()
    form = forms.LicenseTypeForm


@register_model_view(LicenseType, name='bulk_import')
class LicenseTypeBulkImportView(generic.BulkImportView):
    queryset = LicenseType.objects.all()
    model_form = forms.LicenseTypeCSVForm
    table = tables.LicenseTypeTable


@register_model_view(LicenseType, name='delete')
class LicenseTypeDeleteView(generic.ObjectDeleteView):
    queryset = LicenseType.objects.all()


@register_model_view(SoftwareLicense)
class SoftwareLicenseView(generic.ObjectView):
    queryset = SoftwareLicense.objects.all()


@register_model_view(SoftwareLicense, name='list')
class SoftwareLicenseListView(generic.ObjectListView):
    queryset = SoftwareLicense.objects.all()
    table = tables.SoftwareLicenseTable
    filterset = filtersets.SoftwareLicenseFilterSet


@register_model_view(SoftwareLicense, name='edit')
class SoftwareLicenseEditView(generic.ObjectEditView):
    queryset = SoftwareLicense.objects.all()
    form = forms.SoftwareLicenseForm


@register_model_view(SoftwareLicense, name='bulk_import')
class SoftwareLicenseBulkImportView(generic.BulkImportView):
    queryset = SoftwareLicense.objects.all()
    model_form = forms.SoftwareLicenseCSVForm
    table = tables.SoftwareLicenseTable


@register_model_view(SoftwareLicense, name='delete')
class SoftwareLicenseDeleteView(generic.ObjectDeleteView):
    queryset = SoftwareLicense.objects.all()


@register_model_view(SoftwareLicense, name='contracts', path='contracts')
class SoftwareLicenseContractsView(generic.ObjectChildrenView):
    queryset = SoftwareLicense.objects.all()
    child_model = ContractAssignment
    table = tables.ContractAssignmentObjectTable
    filterset = filtersets.ContractAssignmentFilterSet
    template_name = 'generic/object_children.html'

    # Always shown, even when the license has no contract assignments
    tab = ViewTab(
        label='Contracts',
        badge=lambda obj: ContractAssignment.objects.filter(
            object_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
        ).count(),
        permission='netbox_contracts.view_contractassignment',
    )

    def get_children(self, request, parent):
        return ContractAssignment.objects.filter(
            object_type=ContentType.objects.get_for_model(parent),
            object_id=parent.pk,
        )


@register_model_view(LicenseAssignment)
class LicenseAssignmentView(generic.ObjectView):
    queryset = LicenseAssignment.objects.all()


@register_model_view(LicenseAssignment, name='list')
class LicenseAssignmentListView(generic.ObjectListView):
    queryset = LicenseAssignment.objects.all()
    table = tables.LicenseAssignmentTable
    filterset = filtersets.LicenseAssignmentFilterSet


@register_model_view(LicenseAssignment, name='edit')
class LicenseAssignmentEditView(generic.ObjectEditView):
    queryset = LicenseAssignment.objects.all()
    form = forms.LicenseAssignmentForm


@register_model_view(LicenseAssignment, name='bulk_import')
class LicenseAssignmentBulkImportView(generic.BulkImportView):
    queryset = LicenseAssignment.objects.all()
    model_form = forms.LicenseAssignmentCSVForm
    table = tables.LicenseAssignmentTable


@register_model_view(LicenseAssignment, name='delete')
class LicenseAssignmentDeleteView(generic.ObjectDeleteView):
    queryset = LicenseAssignment.objects.all()
