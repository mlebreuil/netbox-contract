import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from circuits.models import Circuit, CircuitTermination
from dcim.models import Device, Rack, Region, Site
from dcim.models import Manufacturer
from netbox.filtersets import NetBoxModelFilterSet
from utilities.filters import ContentTypeFilter
from virtualization.models import Cluster, VirtualMachine
from .models import (
    Contract,
    ContractAssignment,
    ContractType,
    Currency,
    LicenseAssignment,
    LicenseType,
    ServiceLevelAgreement,
    SoftwareLicense,
)

__all__ = (
    'ContractFilterSet',
    'ContractTypeFilterSet',
    'ServiceLevelAgreementFilterSet',
    'ContractAssignmentFilterSet',
    'CurrencyFilterSet',
    'LicenseTypeFilterSet',
    'SoftwareLicenseFilterSet',
    'LicenseAssignmentFilterSet',
)


class ContractFilterSet(NetBoxModelFilterSet):

    contract_type = django_filters.ModelMultipleChoiceFilter(
        queryset=ContractType.objects.all(),
        method='filter_contract_type',
        label='Contract type',
    )

    class Meta:
        model = Contract
        fields = (
            'id',
            'name',
            'currency',
            'contract_type',
            'parent',
        )

    def filter_contract_type(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(contract_type__in=value)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        return queryset.filter(name__icontains=value)


class ContractTypeFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = ContractType
        fields = (
            'name',
            'description',
            'color',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        return queryset.filter(name__icontains=value)


class ServiceLevelAgreementFilterSet(NetBoxModelFilterSet):

    class Meta:
        model = ServiceLevelAgreement
        fields = (
            'name',
            'description',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        return queryset.filter(name__icontains=value)


class ContractAssignmentFilterSet(NetBoxModelFilterSet):

    region = django_filters.ModelMultipleChoiceFilter(
        method='filter_region',
        queryset=Region.objects.all(),
        label='Region',
    )
    contract = django_filters.ModelMultipleChoiceFilter(
        queryset=Contract.objects.all(),
        method='filter_contract',
        label='Contract',
    )
    contract_type = django_filters.ModelMultipleChoiceFilter(
        queryset=ContractType.objects.all(),
        method='filter_contract_type',
        label='Contract type',
    )

    class Meta:
        model = ContractAssignment
        fields = (
            'id',
            'contract',
            'provider',
            'fe',
            'object_type',
            'object_id',
            'region',
            'contract_type',
        )

    def filter_contract(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(contract__in=value)

    def filter_contract_type(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(contract__contract_type__in=value)

    def filter_region(self, queryset, name, regions):
        if not regions:
            return queryset

        region_ids = set()

        # Include selected regions and all descendant regions.
        for region in regions:
            region_ids.add(region.pk)
            region_ids.update(
                region.get_descendants(include_self=False)
                .values_list('pk', flat=True)
            )

        #
        # Sites in the selected region hierarchy
        #
        site_ids = Site.objects.filter(
            region_id__in=region_ids
        ).values_list('pk', flat=True)

        #
        # Devices and racks located directly at matching sites
        #
        device_ids = Device.objects.filter(
            site_id__in=site_ids
        ).values_list('pk', flat=True)

        rack_ids = Rack.objects.filter(
            site_id__in=site_ids
        ).values_list('pk', flat=True)

        #
        # NetBox 4.x: Cluster has no direct 'site' field. It's scoped via a
        # generic 'scope' (scope_type/scope_id), with '_region_id' cached
        # directly on the model for querying regardless of whether the
        # scope is a Region, Site Group, Site, or Location.
        #
        cluster_ids = Cluster.objects.filter(
            _region_id__in=region_ids
        ).values_list('pk', flat=True)

        vm_ids = VirtualMachine.objects.filter(
            Q(site_id__in=site_ids) | Q(cluster___region_id__in=region_ids)
        ).values_list('pk', flat=True)

        #
        # NetBox 4.3.1:
        #
        # CircuitTermination.termination is a GenericForeignKey backed by:
        #
        #   termination_type
        #   termination_id
        #
        # Only circuits whose A-side terminates directly at a Site are
        # included here.
        #
        site_content_type = ContentType.objects.get_for_model(
            Site,
            for_concrete_model=False,
        )

        circuit_ids = CircuitTermination.objects.filter(
            term_side='A',
            termination_type_id=site_content_type.pk,
            termination_id__in=site_ids,
        ).values_list('circuit_id', flat=True)

        #
        # object_id must always be evaluated together with object_type,
        # because primary keys can overlap across these models.
        #
        # NOTE: VirtualCircuit assignments are not matched here, since a
        # virtual circuit's region can only be derived by walking its
        # interface terminations to a device/site, which this filter does
        # not currently do.
        #
        content_type_matches = (
            (Site, site_ids),
            (Device, device_ids),
            (Rack, rack_ids),
            (Cluster, cluster_ids),
            (VirtualMachine, vm_ids),
            (Circuit, circuit_ids),
        )

        region_filter = Q()
        for model, ids in content_type_matches:
            content_type = ContentType.objects.get_for_model(model, for_concrete_model=False)
            region_filter |= Q(object_type_id=content_type.pk, object_id__in=ids)

        return queryset.filter(region_filter).distinct()

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        return queryset.filter(
            Q(contract__name__icontains=value)
        )


class CurrencyFilterSet(NetBoxModelFilterSet):

    country = django_filters.ModelMultipleChoiceFilter(
        method='filter_country',
        queryset=Region.objects.all(),
        label='Country (Region)',
    )

    class Meta:
        model = Currency
        fields = (
            'id',
            'currency_code',
            'currency_name',
            'country',
            'currency_number',
            'usd_rate',
        )

    def filter_country(self, queryset, name, regions):
        if not regions:
            return queryset

        region_ids = set()

        # Include selected regions and all descendant regions.
        for region in regions:
            region_ids.add(region.pk)
            region_ids.update(
                region.get_descendants(include_self=False)
                .values_list('pk', flat=True)
            )

        return queryset.filter(
            country_id__in=region_ids
        ).distinct()

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset

        return queryset.filter(
            Q(currency_code__icontains=value)
            | Q(currency_name__icontains=value)
            | Q(currency_number__icontains=value)
        )


#
# Software licensing
#
class LicenseTypeFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = LicenseType
        fields = ('id', 'name', 'description', 'color')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class SoftwareLicenseFilterSet(NetBoxModelFilterSet):
    manufacturer_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Manufacturer.objects.all(),
        label='Manufacturer (ID)',
    )
    license_type_id = django_filters.ModelMultipleChoiceFilter(
        queryset=LicenseType.objects.all(),
        label='License Type (ID)',
    )
    local_currency_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Currency.objects.all(),
        label='Local Currency (ID)',
    )

    class Meta:
        model = SoftwareLicense
        fields = (
            'id',
            'license_name',
            'friendly_name',
            'license_sku',
            'manufacturer_id',
            'license_type_id',
            'local_currency_id',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(license_name__icontains=value) | Q(friendly_name__icontains=value) | Q(license_sku__icontains=value)
        )


class LicenseAssignmentFilterSet(NetBoxModelFilterSet):
    software_license_id = django_filters.ModelMultipleChoiceFilter(
        queryset=SoftwareLicense.objects.all(),
        label='Software License (ID)',
    )
    object_type = ContentTypeFilter()

    class Meta:
        model = LicenseAssignment
        fields = ('id', 'software_license_id', 'object_type_id', 'object_id')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(software_license__license_name__icontains=value) | Q(software_license__license_sku__icontains=value)
        )
