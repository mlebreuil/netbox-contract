from datetime import timedelta
from decimal import Decimal

from dcim.choices import DeviceStatusChoices, SiteStatusChoices
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from netbox.choices import ColorChoices
from netbox.models import NetBoxModel
from netbox.models.features import ContactsMixin
from utilities.choices import ChoiceSet
from utilities.exceptions import AbortRequest
from utilities.fields import ColorField
from virtualization.choices import VirtualMachineStatusChoices

from . import calculations

LOCKED_CONTRACT_MESSAGE = _(
    'This contract already has invoices: its lines cannot be added, changed or deleted. '
    'A new contract must be created.'
)
REFERENCED_LINE_MESSAGE = _(
    'This contract line is used by invoice lines: it cannot be changed or deleted. A new contract must be created.'
)
INTERNAL_FIELDS_NOTE = _('Its accounting dimensions, comments and tags can still be edited.')

# Contract terms of a contract line, locked once it is invoiced (FR-029); its accounting dimensions, comments
# and tags are internal classification and stay editable (decision I9)
CONTRACT_LINE_LOCKED_FIELDS = (
    'contract',
    'description',
    'quantity',
    'unit_price',
    'unit',
    'currency',
    'start_date',
    'end_date',
    'custom_field_data',
)


def _format_date(value, default):
    return value.isoformat() if value else default


def _first_names(names, limit=5):
    names = [str(name) for name in names]
    text = ', '.join(names[:limit])
    return f'{text}, ...' if len(names) > limit else text


def _contract_period(contract):
    return _('{start} to {end}').format(
        start=_format_date(contract.start_date, _('no start date')),
        end=_format_date(contract.end_date, _('no end date')),
    )


class StatusChoices(ChoiceSet):
    key = 'Contract.status'

    STATUS_ACTIVE = 'active'
    STATUS_CANCELED = 'canceled'

    CHOICES = [
        (STATUS_ACTIVE, 'Active', 'green'),
        (STATUS_CANCELED, 'Canceled', 'red'),
    ]


class AccountingDimensionStatusChoices(ChoiceSet):
    key = 'AccountingDimension.status'

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'

    CHOICES = [
        (STATUS_ACTIVE, 'Active', 'green'),
        (STATUS_INACTIVE, 'Inactive', 'red'),
    ]


class InternalEntityChoices(ChoiceSet):
    key = 'Contract.internal_party'

    ENTITY = 'Default entity'

    CHOICES = [
        (ENTITY, 'Default entity', 'green'),
    ]


class CurrencyChoices(ChoiceSet):
    key = 'Contract.currency'
    CURRENCY_USD = 'usd'

    CHOICES = [
        (CURRENCY_USD, 'USD'),
        ('eur', 'EUR'),
        ('chf', 'CHF'),
    ]


class InvoiceStatusChoices(ChoiceSet):
    key = 'Invoice.status'

    STATUS_DRAFT = 'draft'
    STATUS_POSTED = 'posted'
    STATUS_CANCELED = 'canceled'

    CHOICES = [
        (STATUS_DRAFT, 'Draft', 'yellow'),
        (STATUS_POSTED, 'Posted', 'green'),
        (STATUS_CANCELED, 'Canceled', 'red'),
    ]


class BillingMethodChoices(ChoiceSet):
    key = 'Unit.billing_method'

    ONE_TIME = calculations.ONE_TIME
    RECURRING = calculations.RECURRING
    USAGE = calculations.USAGE

    CHOICES = [
        (ONE_TIME, 'One-time', 'blue'),
        (RECURRING, 'Recurring', 'green'),
        (USAGE, 'Usage-based', 'orange'),
    ]


CURRENCY_DEFAULT = CurrencyChoices.CHOICES[0][0]


class ContractType(NetBoxModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_('name'))
    description = models.TextField(blank=True, verbose_name=_('description'))
    color = ColorField(default=ColorChoices.COLOR_GREY, verbose_name=_('color'))

    class Meta:
        ordering = ('name',)
        verbose_name = _('contract type')
        verbose_name_plural = _('contract types')

    def __str__(self):
        return self.name

    def get_color(self):
        return self.color

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:contracttype', args=[self.pk])


class AccountingDimension(NetBoxModel):
    name = models.CharField(
        max_length=20,
        verbose_name=_('dimension name'),
        help_text=_('Accounting dimension name. Ex: Department, Location, etc.'),
    )
    value = models.CharField(max_length=20, verbose_name=_('value'))
    status = models.CharField(
        max_length=50,
        choices=AccountingDimensionStatusChoices,
        default=StatusChoices.STATUS_ACTIVE,
        verbose_name=_('status'),
    )
    comments = models.TextField(blank=True, verbose_name=_('comments'))

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:accountingdimension', args=[self.pk])

    @property
    def dimension(self):
        return ''.join([self.name, ':', self.value])

    def __str__(self):
        return self.dimension

    def get_status_color(self):
        return AccountingDimensionStatusChoices.colors.get(self.status)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['name', 'value'], name='unique_accounting_dimension')]
        ordering = ('name', 'value')
        verbose_name = _('accounting dimension')
        verbose_name_plural = _('accounting dimensions')


class ServiceProvider(ContactsMixin, NetBoxModel):
    name = models.CharField(max_length=100, verbose_name=_('name'))
    slug = models.SlugField(max_length=100, unique=True, verbose_name=_('slug'))
    portal_url = models.URLField(blank=True, verbose_name=_('portal URL'))
    comments = models.TextField(blank=True, verbose_name=_('comments'))

    class Meta:
        ordering = ('name',)
        verbose_name = _('service provider')
        verbose_name_plural = _('service providers')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:serviceprovider', args=[self.pk])


class ContractAssignment(NetBoxModel):
    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE, verbose_name=_('content type'))
    object_id = models.PositiveBigIntegerField(verbose_name=_('object ID'))
    content_object = GenericForeignKey(ct_field='content_type', fk_field='object_id')
    contract = models.ForeignKey(
        to='Contract',
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_('contract'),
    )
    clone_fields = ('content_type', 'object_id', 'contract')

    class Meta:
        ordering = ('contract',)
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
        verbose_name = _('contract assignment')
        verbose_name_plural = _('contract assignments')

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:contractassignment', args=[self.pk])

    def get_contract__status_color(self):
        return StatusChoices.colors.get(self.contract.status)

    def get_content_object__status_color(self):
        STATUS_MAPPING = {
            'virtualmachine': VirtualMachineStatusChoices.colors,
            'device': DeviceStatusChoices.colors,
            'site': SiteStatusChoices.colors,
        }
        status_colors = STATUS_MAPPING.get(self.content_type.model, StatusChoices.colors)
        return status_colors.get(self.content_object.status)


class Contract(ContactsMixin, NetBoxModel):
    name = models.CharField(max_length=100, verbose_name=_('name'))
    contract_type = models.ForeignKey(
        to='netbox_contract.ContractType',
        on_delete=models.PROTECT,
        related_name='contracts',
        blank=True,
        null=True,
        verbose_name=_('contract type'),
    )
    external_party_object_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name=_('external party object type'),
    )
    external_party_object_id = models.PositiveBigIntegerField(
        blank=True, null=True, verbose_name=_('external party object ID')
    )
    external_party_object = GenericForeignKey(
        ct_field='external_party_object_type', fk_field='external_party_object_id'
    )
    external_party_object.editable = True
    external_reference = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('external reference'))
    internal_party = models.CharField(max_length=50, choices=InternalEntityChoices, verbose_name=_('internal party'))
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='contracts',
        blank=True,
        null=True,
        verbose_name=_('tenant'),
    )
    status = models.CharField(
        max_length=50,
        choices=StatusChoices,
        default=StatusChoices.STATUS_ACTIVE,
        verbose_name=_('status'),
    )
    start_date = models.DateField(blank=True, null=True, verbose_name=_('start date'))
    end_date = models.DateField(blank=True, null=True, verbose_name=_('end date'))
    initial_term = models.IntegerField(
        help_text=_('In month'),
        default=12,
        blank=True,
        null=True,
        verbose_name=_('initial term'),
    )
    renewal_term = models.IntegerField(
        help_text=_('In month'),
        default=12,
        blank=True,
        null=True,
        verbose_name=_('renewal term'),
    )
    notice_period = models.IntegerField(
        help_text=_('Contract notice period. Default to 90 days'),
        default=90,
        verbose_name=_('notice period'),
    )
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices,
        default=CURRENCY_DEFAULT,
        verbose_name=_('currency'),
    )
    yrc = models.DecimalField(
        verbose_name=_('yearly recuring cost'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Deprecated: replaced by contract lines. Use either this field of the monthly recuring cost field'),
    )
    mrc = models.DecimalField(
        verbose_name=_('monthly recuring cost'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Deprecated: replaced by contract lines. Use either this field of the yearly recuring cost field'),
    )
    nrc = models.DecimalField(
        verbose_name=_('none recuring cost'),
        default=0,
        max_digits=10,
        decimal_places=2,
        help_text=_('Deprecated: replaced by contract lines'),
    )
    invoice_frequency = models.IntegerField(
        help_text=_('The frequency of invoices in month'),
        default=1,
        verbose_name=_('invoice frequency'),
    )
    documents = models.URLField(
        blank=True,
        verbose_name=_('documents'),
        help_text=_('URL to the contract documents'),
    )
    comments = models.TextField(blank=True, verbose_name=_('comments'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='childs',
        null=True,
        blank=True,
        verbose_name=_('parent'),
    )
    billable = models.BooleanField(
        default=True,
        verbose_name=_('billable'),
        help_text=_('Whether invoices are issued for this contract. The lines of a non-billable contract are '
                    'invoiced through its closest billable parent.'),
    )

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:contract', args=[self.pk])

    def get_status_color(self):
        return StatusChoices.colors.get(self.status)

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(fields=['external_party_object_type', 'external_party_object_id']),
        ]
        verbose_name = _('contract')
        verbose_name_plural = _('contracts')

    @property
    def notice_date(self):
        return self.end_date - timedelta(days=self.notice_period)

    def __str__(self):
        return self.name

    # Hierarchy

    def ancestors(self):
        """Parent, grand-parent, ... of this contract."""
        result, seen, parent = [], {self.pk}, self.parent
        while parent is not None and parent.pk not in seen:
            result.append(parent)
            seen.add(parent.pk)
            parent = parent.parent
        return result

    def descendants(self):
        """Children, grand-children, ... of this contract."""
        result, seen, level = [], {self.pk}, [self.pk]
        while level:
            children = [child for child in Contract.objects.filter(parent__in=level) if child.pk not in seen]
            result.extend(children)
            seen.update(child.pk for child in children)
            level = [child.pk for child in children]
        return result

    def billing_scope(self):
        """
        Contracts invoiced under this contract: itself and its non-billable descendants, stopping at any
        billable child, which invoices itself and its own non-billable descendants (FR-022).
        """
        result, seen, level = [self], {self.pk}, [self.pk]
        while level:
            children = [
                child for child in Contract.objects.filter(parent__in=level, billable=False) if child.pk not in seen
            ]
            result.extend(children)
            seen.update(child.pk for child in children)
            level = [child.pk for child in children]
        return result

    # Computed values (FR-006, FR-007)

    def _lines(self):
        return self.lines.select_related('unit')

    def _current_lines(self):
        """Lines not replaced by an amendment: the yearly values count only the current price (FR-030)."""
        return self._lines().filter(replaced_by__isnull=True)

    @property
    def total_contract_value(self):
        """Total value of the contract's own lines; None when not available (open-ended recurring line)."""
        total = Decimal(0)
        for line in self._lines():
            value = line.total_value
            if value is None:
                return None
            total += value
        return calculations.round_amount(total)

    @property
    def yearly_contract_value(self):
        """Twelve-month equivalent of the contract's own recurring lines."""
        annotated = self.__dict__.get('yearly_value')
        if annotated is not None:
            return annotated
        return calculations.round_amount(sum((line.yearly_value for line in self._current_lines()), Decimal(0)))

    @property
    def yearly_billable_value(self):
        """Yearly value of the lines invoiced under this contract; zero for a non-billable contract."""
        if not self.billable:
            return calculations.round_amount(0)
        lines = ContractLine.objects.filter(
            contract__in=self.billing_scope(), replaced_by__isnull=True
        ).select_related('unit')
        return calculations.round_amount(sum((line.yearly_value for line in lines), Decimal(0)))

    # Validation

    def clean(self):
        super().clean()
        errors = {}
        if self.pk:
            errors.update(self._clean_line_dates())
            errors.update(self._clean_billable())
            errors.update(self._clean_currency_change())
        errors.update(self._clean_parent_currency())
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        previous_currency = self._original('currency').get('currency') if self.pk else None
        super().save(*args, **kwargs)
        # The contract lines follow a new currency (FR-009a). A queryset update skips the per-line validation
        # and the lock, which is safe because clean() only allows the change when the contract has no invoice.
        if previous_currency and previous_currency != self.currency and not self.invoices.exists():
            ContractLine.objects.filter(contract=self.pk).exclude(currency=self.currency).update(
                currency=self.currency
            )

    def _clean_currency_change(self):
        """A contract's currency cannot change once it has invoices or invoice lines (FR-009a, FR-010)."""
        original = self._original('currency')
        if not original or original['currency'] == self.currency:
            return {}
        blocking = []
        invoices = list(Invoice.objects.filter(contracts=self.pk).values_list('number', flat=True)[:6])
        if invoices:
            blocking.append(_('invoices {numbers}').format(numbers=_first_names(invoices)))
        invoice_lines = list(
            InvoiceLine.objects.filter(contract_line__contract=self.pk)
            .values_list('invoice__number', flat=True)
            .distinct()[:6]
        )
        if invoice_lines:
            blocking.append(_('invoice lines of invoices {numbers}').format(numbers=_first_names(invoice_lines)))
        if blocking:
            return {
                'currency': _('The currency cannot change because this contract has {records}.').format(
                    records=_(' and ').join(str(item) for item in blocking)
                )
            }
        children = list(
            Contract.objects.filter(parent=self.pk, billable=False)
            .exclude(currency=self.currency)
            .values_list('name', flat=True)[:6]
        )
        if children:
            return {
                'currency': _(
                    'The currency cannot change: the non-billable child contracts {names} have the currency {found} '
                    'and must have the currency of their parent.'
                ).format(names=_first_names(children), found=original['currency'].upper())
            }
        return {}

    def _clean_parent_currency(self):
        """A non-billable child has the currency of its parent (FR-010)."""
        if not self.parent_id or self.billable:
            return {}
        original = self._original('parent', 'billable', 'currency') if self.pk else {}
        unchanged = original and (original['parent'], original['billable'], original['currency']) == (
            self.parent_id, self.billable, self.currency
        )
        if unchanged or self.parent.currency == self.currency:
            return {}
        return {
            'parent': _(
                'A non-billable contract must have the currency of its parent: {found} differs from {expected} '
                'of {parent}.'
            ).format(found=self.currency.upper(), expected=self.parent.currency.upper(), parent=self.parent)
        }

    def _original(self, *fields):
        return Contract.objects.filter(pk=self.pk).values(*fields).first() or {}

    def _clean_billable(self):
        """The billable flag cannot change once the contract's family is invoiced (FR-008a)."""
        original = self._original('billable')
        if not original or original['billable'] == self.billable:
            return {}
        family = [self.pk, *(c.pk for c in self.ancestors()), *(c.pk for c in self.descendants())]
        if (
            Invoice.objects.filter(contracts__in=family).exists()
            or InvoiceLine.objects.filter(contract_line__contract=self.pk).exists()
        ):
            return {
                'billable': _(
                    'The billable flag cannot change: this contract, one of its parents or one of its children '
                    'already has invoices. A new contract must be created.'
                )
            }
        return {}

    def _clean_line_dates(self):
        """Refuse contract dates that would leave existing contract lines outside them (FR-002a)."""
        errors = {}
        lines = ContractLine.objects.filter(contract=self.pk)
        if self.start_date and lines.filter(
            models.Q(start_date__lt=self.start_date) | models.Q(end_date__lt=self.start_date)
        ).exists():
            errors['start_date'] = _('Some contract lines start before this date; change their dates first.')
        if self.end_date and lines.filter(
            models.Q(end_date__gt=self.end_date) | models.Q(start_date__gt=self.end_date)
        ).exists():
            errors['end_date'] = _('Some contract lines end after this date; change their dates first.')
        return errors


class Invoice(NetBoxModel):
    number = models.CharField(max_length=100, verbose_name=_('number'))
    template = models.BooleanField(
        blank=True,
        null=True,
        default=False,
        verbose_name=_('template'),
        help_text=_('Deprecated: invoice lines are generated from the contract lines. Wether this invoice is a '
                    'template or not'),
    )
    status = models.CharField(
        max_length=50,
        choices=InvoiceStatusChoices,
        default=InvoiceStatusChoices.STATUS_POSTED,
        verbose_name=_('status'),
    )
    date = models.DateField(blank=True, null=True, verbose_name=_('date'))
    contracts = models.ManyToManyField(Contract, related_name='invoices', blank=True, verbose_name=_('contracts'))
    period_start = models.DateField(blank=True, null=True, verbose_name=_('period start'))
    period_end = models.DateField(blank=True, null=True, verbose_name=_('period end'))
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices,
        default=CURRENCY_DEFAULT,
        verbose_name=_('currency'),
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('amount'))
    documents = models.URLField(
        blank=True,
        verbose_name=_('documents'),
        help_text=_('URL to the contract documents'),
    )
    comments = models.TextField(blank=True, verbose_name=_('comments'))

    class Meta:
        ordering = ('-period_start',)
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')

    def __str__(self):
        return self.number

    def get_status_color(self):
        return InvoiceStatusChoices.colors.get(self.status)

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:invoice', args=[self.pk])

    @property
    def total_invoicelines_amount(self):
        """
        Calculates the total amount for all related InvoiceLines.
        """
        return sum(invoiceline.amount for invoiceline in self.invoicelines.all())


class Unit(NetBoxModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_('name'))
    description = models.TextField(blank=True, verbose_name=_('description'))
    billing_method = models.CharField(
        max_length=20,
        choices=BillingMethodChoices,
        verbose_name=_('billing method'),
    )
    months = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_('months'),
        help_text=_('Number of months covered by one unit price. Required for recurring units only.'),
    )
    comments = models.TextField(blank=True, verbose_name=_('comments'))

    class Meta:
        ordering = ('name',)
        verbose_name = _('unit')
        verbose_name_plural = _('units')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:unit', args=[self.pk])

    def get_billing_method_color(self):
        return BillingMethodChoices.colors.get(self.billing_method)

    def clean(self):
        super().clean()
        errors = {}
        if self.billing_method == BillingMethodChoices.RECURRING:
            if not self.months:
                errors['months'] = _('A recurring unit needs the number of months (at least 1) one unit price covers.')
        elif self.months is not None:
            errors['months'] = _('Only a recurring unit covers a number of months.')

        if self.pk and not errors:
            original = Unit.objects.filter(pk=self.pk).values('billing_method', 'months').first()
            changed = [
                field for field in ('billing_method', 'months')
                if original and original[field] != getattr(self, field)
            ]
            if changed and (self.invoiced_lines().exists() or InvoiceLine.objects.filter(unit=self.pk).exists()):
                message = _('This unit is used by contracts that have invoices: its billing method and months '
                            'cannot change. Create a new unit instead.')
                errors.update({field: message for field in changed})
        if errors:
            raise ValidationError(errors)

    def invoiced_lines(self):
        """Contract lines using this unit that are locked because of invoices (FR-001a, FR-029)."""
        return ContractLine.objects.filter(
            models.Q(contract__invoices__isnull=False) | models.Q(invoicelines__isnull=False), unit=self.pk
        )


class ContractLine(NetBoxModel):
    contract = models.ForeignKey(
        to='Contract',
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_('contract'),
    )
    description = models.CharField(max_length=200, verbose_name=_('description'))
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1, verbose_name=_('quantity'))
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('unit price'))
    unit = models.ForeignKey(
        to='Unit',
        on_delete=models.PROTECT,
        related_name='contract_lines',
        verbose_name=_('unit'),
    )
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices,
        blank=True,
        verbose_name=_('currency'),
        help_text=_("Defaults to the contract's currency"),
    )
    start_date = models.DateField(
        blank=True, null=True, verbose_name=_('start date'), help_text=_("Defaults to the contract's start date")
    )
    end_date = models.DateField(
        blank=True, null=True, verbose_name=_('end date'), help_text=_("Defaults to the contract's end date")
    )
    accounting_dimensions = models.ManyToManyField(
        AccountingDimension, blank=True, related_name='contract_lines', verbose_name=_('accounting dimensions')
    )
    comments = models.TextField(blank=True, verbose_name=_('comments'))
    replaces = models.ForeignKey(
        to='self',
        on_delete=models.SET_NULL,
        related_name='replaced_by',
        blank=True,
        null=True,
        editable=False,
        verbose_name=_('replaces'),
        help_text=_('The line this line replaces after an amendment of its price or quantity'),
    )
    invoiced_at_conversion = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('invoiced at conversion'),
        help_text=_('Set by the upgrade conversion for a one-time line of a contract that already had a posted '
                    'invoice: the line is considered fully invoiced.'),
    )

    clone_fields = ('contract', 'unit', 'currency', 'start_date', 'end_date')

    class Meta:
        ordering = ('contract', 'start_date', 'description')
        verbose_name = _('contract line')
        verbose_name_plural = _('contract lines')

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:contractline', args=[self.pk])

    @property
    def effective_start_date(self):
        return self.start_date or self.contract.start_date

    @property
    def effective_end_date(self):
        return self.end_date or self.contract.end_date

    @property
    def total_value(self):
        return calculations.line_total_value(
            self.unit.billing_method,
            self.quantity,
            self.unit_price,
            self.unit.months,
            self.effective_start_date,
            self.effective_end_date,
        )

    @property
    def yearly_value(self):
        return calculations.line_yearly_value(
            self.unit.billing_method, self.quantity, self.unit_price, self.unit.months
        )

    @property
    def can_be_amended(self):
        """Whether the amend action applies: a saved recurring or usage-based line not replaced yet (FR-030)."""
        return (
            bool(self.pk)
            and self.unit.billing_method != BillingMethodChoices.ONE_TIME
            and not self.replaced_by.exists()
        )

    def apply_contract_defaults(self):
        """Take the dates and the currency of the contract when they are not set (FR-002)."""
        if not self.contract_id:
            return
        if not self.currency:
            self.currency = self.contract.currency
        if self.start_date is None:
            self.start_date = self.contract.start_date
        if self.end_date is None:
            self.end_date = self.contract.end_date

    def lock_message(self):
        """Why this line can no longer be changed or deleted (FR-029), or None."""
        if self.pk:
            if InvoiceLine.objects.filter(contract_line=self.pk).exists():
                return REFERENCED_LINE_MESSAGE
            original = ContractLine.objects.filter(pk=self.pk).values_list('contract', flat=True).first()
            if original and Invoice.objects.filter(contracts=original).exists():
                return LOCKED_CONTRACT_MESSAGE
        if self.contract_id and Invoice.objects.filter(contracts=self.contract_id).exists():
            return LOCKED_CONTRACT_MESSAGE
        return None

    def locked_fields_changed(self):
        """Whether a contract term of this saved line differs from the database."""
        attnames = [self._meta.get_field(name).attname for name in CONTRACT_LINE_LOCKED_FIELDS]
        original = ContractLine.objects.filter(pk=self.pk).values(*attnames).first()
        return original is None or any(original[name] != getattr(self, name) for name in attnames)

    def clean(self):
        super().clean()
        if not self.contract_id:
            return
        self.apply_contract_defaults()

        message = self.lock_message()
        if message and (not self.pk or self.locked_fields_changed()):
            raise ValidationError(f'{message} {INTERNAL_FIELDS_NOTE}' if self.pk else message)

        errors = {}
        contract = self.contract
        outside = _('A contract line must lie within the dates of its contract ({period}).').format(
            period=_contract_period(contract)
        )
        if self.start_date and (
            (contract.start_date and self.start_date < contract.start_date)
            or (contract.end_date and self.start_date > contract.end_date)
        ):
            errors['start_date'] = outside
        if self.end_date and (
            (contract.end_date and self.end_date > contract.end_date)
            or (contract.start_date and self.end_date < contract.start_date)
        ):
            errors['end_date'] = outside
        if self.start_date and self.end_date and self.end_date < self.start_date and 'end_date' not in errors:
            errors['end_date'] = _('The end date cannot be before the start date.')
        if self.currency != contract.currency:
            errors['currency'] = _(
                'The currency {found} of a contract line must be the currency {expected} of its contract.'
            ).format(found=self.currency.upper(), expected=contract.currency.upper())
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.apply_contract_defaults()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Checked here, before Django's deletion collector opens its transaction; the pre_delete
        # receiver in signals.py covers queryset deletions.
        message = self.lock_message()
        if message:
            raise AbortRequest(escape(message))
        return super().delete(*args, **kwargs)


class InvoiceLine(NetBoxModel):
    invoice = models.ForeignKey(
        to='Invoice',
        on_delete=models.CASCADE,
        related_name='invoicelines',
        verbose_name=_('invoice'),
    )
    contract_line = models.ForeignKey(
        to='ContractLine',
        on_delete=models.SET_NULL,
        related_name='invoicelines',
        blank=True,
        null=True,
        verbose_name=_('contract line'),
    )
    unit = models.ForeignKey(
        to='Unit',
        on_delete=models.PROTECT,
        related_name='invoicelines',
        blank=True,
        null=True,
        verbose_name=_('unit'),
        help_text=_('Defaults to the unit of the contract line; fixed once the line is created'),
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('unit price'),
        help_text=_('Defaults to the unit price of the contract line; fixed once the line is created'),
    )
    quantity = models.DecimalField(
        max_digits=12, decimal_places=4, blank=True, null=True, verbose_name=_('quantity')
    )
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices,
        default=CURRENCY_DEFAULT,
        verbose_name=_('currency'),
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        verbose_name=_('amount'),
        help_text=_('Calculated from the quantity and the unit price when the line has a unit price; entered '
                    'manually otherwise'),
    )
    accounting_dimensions = models.ManyToManyField(
        AccountingDimension, blank=True, verbose_name=_('accounting dimensions')
    )
    comments = models.TextField(blank=True, verbose_name=_('comments'))

    class Meta:
        ordering = ('invoice',)
        verbose_name = _('invoice line')
        verbose_name_plural = _('invoice lines')

    def __str__(self):
        number = self.invoice.number if self.invoice_id else ''
        return f'{number} line {self.pk}' if self.pk else f'{number} new line'

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:invoiceline', args=[self.pk])

    def apply_contract_line_defaults(self):
        """A new line takes the unit and unit price of its contract line when they are not given (FR-024)."""
        if self.pk or not self.contract_line_id:
            return
        if self.unit_id is None:
            self.unit = self.contract_line.unit
        if self.unit_price is None:
            self.unit_price = self.contract_line.unit_price

    def calculate_amount(self):
        """
        Amount from the quantity and the unit price of the line (research D7, decision I11): recurring units
        are prorated to the invoice period and the dates of the contract line, as for the pre-fill; without an
        invoice period, a recurring line counts for one invoice frequency of the invoice's contract. None when
        the line has no unit price (manual amount).
        """
        if self.unit_price is None:
            return None
        line = self.contract_line if self.contract_line_id else None
        unit = self.unit if self.unit_id else None
        invoiced_contract = self.invoice.contracts.first() or (line.contract if line else None)
        return calculations.invoice_line_amount(
            unit.billing_method if unit else calculations.USAGE,
            self.quantity,
            self.unit_price,
            unit.months if unit else None,
            self.invoice.period_start,
            self.invoice.period_end,
            line.effective_start_date if line else None,
            line.effective_end_date if line else None,
            default_months=(invoiced_contract.invoice_frequency if invoiced_contract else None) or 1,
        )

    def clean(self):
        super().clean()
        if not self.invoice_id:
            return

        original = (
            InvoiceLine.objects.filter(pk=self.pk).values('invoice', 'currency', 'contract_line').first()
            if self.pk else None
        )

        self.apply_contract_line_defaults()

        if self.contract_line_id:
            if not original or (original['invoice'], original['contract_line']) != (
                self.invoice_id, self.contract_line_id
            ):
                allowed = {
                    contract.pk
                    for invoice_contract in self.invoice.contracts.all()
                    for contract in invoice_contract.billing_scope()
                }
                if self.contract_line.contract_id not in allowed:
                    raise ValidationError({
                        'contract_line': _(
                            'The contract line must belong to the contract of the invoice or to one of its '
                            'non-billable descendants.'
                        )
                    })
        if self.unit_price is not None:
            self.amount = self.calculate_amount()
        elif self.amount is None:
            raise ValidationError({'amount': _('This field is required when the line has no unit price.')})
        currency_changed = not original or (original['invoice'], original['currency']) != (
            self.invoice_id, self.currency
        )
        if currency_changed and self.currency != self.invoice.currency:
            raise ValidationError({
                'currency': _('The currency {found} of an invoice line must be the currency {expected} of its '
                              'invoice.').format(found=self.currency.upper(), expected=self.invoice.currency.upper())
            })

        # Check that the sum of the invoice line amount is not greater the invoice amount
        amount = self.amount
        invoice = self.invoice
        is_new = not bool(self.pk)
        if is_new:
            if amount > (invoice.amount - invoice.total_invoicelines_amount):
                raise ValidationError('Sum of invoice line amount greater than invoice amount')
        else:
            previous_amount = self.__class__.objects.get(pk=self.pk).amount
            if amount > (invoice.amount - invoice.total_invoicelines_amount + previous_amount):
                raise ValidationError('Sum of invoice line amount greater than invoice amount')

    def save(self, *args, **kwargs):
        self.apply_contract_line_defaults()
        if self.unit_price is not None:
            self.amount = self.calculate_amount()
        super().save(*args, **kwargs)


def yearly_value_annotation():
    """
    SQL expression of a contract's yearly value (sum of its current recurring lines, each rounded to two decimals),
    for list views and the API so that the value does not cost one query per contract (research D6).
    """
    line_yearly = models.functions.Round(
        models.ExpressionWrapper(
            models.F('quantity') * models.F('unit_price') * models.Value(12) / models.F('unit__months'),
            output_field=models.DecimalField(max_digits=24, decimal_places=8),
        ),
        precision=2,
    )
    per_contract = (
        ContractLine.objects.filter(
            contract=models.OuterRef('pk'),
            unit__billing_method=BillingMethodChoices.RECURRING,
            replaced_by__isnull=True,
        )
        .order_by()
        .values('contract')
        .annotate(total=models.Sum(line_yearly))
        .values('total')
    )
    return models.functions.Coalesce(
        models.Subquery(per_contract, output_field=models.DecimalField(max_digits=16, decimal_places=2)),
        models.Value(Decimal('0.00')),
        output_field=models.DecimalField(max_digits=16, decimal_places=2),
    )
