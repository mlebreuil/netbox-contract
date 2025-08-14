from datetime import timedelta

from dcim.choices import DeviceStatusChoices, SiteStatusChoices
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.choices import ColorChoices
from netbox.models import NetBoxModel
from netbox.models.features import ContactsMixin
from utilities.choices import ChoiceSet
from utilities.fields import ColorField
from virtualization.choices import VirtualMachineStatusChoices


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
        help_text=_('Use either this field of the monthly recuring cost field'),
    )
    mrc = models.DecimalField(
        verbose_name=_('monthly recuring cost'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Use either this field of the yearly recuring cost field'),
    )
    nrc = models.DecimalField(verbose_name=_('none recuring cost'), default=0, max_digits=10, decimal_places=2)
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


class Invoice(NetBoxModel):
    number = models.CharField(max_length=100, verbose_name=_('number'))
    template = models.BooleanField(
        blank=True,
        null=True,
        default=False,
        verbose_name=_('template'),
        help_text=_('Wether this invoice is a template or not'),
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


class InvoiceLine(NetBoxModel):
    invoice = models.ForeignKey(
        to='Invoice',
        on_delete=models.CASCADE,
        related_name='invoicelines',
        verbose_name=_('invoice'),
    )
    currency = models.CharField(
        max_length=3,
        choices=CurrencyChoices,
        default=CURRENCY_DEFAULT,
        verbose_name=_('currency'),
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('amount'))
    accounting_dimensions = models.ManyToManyField(
        AccountingDimension, blank=True, verbose_name=_('accounting dimensions')
    )
    comments = models.TextField(blank=True, verbose_name=_('comments'))

    class Meta:
        ordering = ('invoice',)
        verbose_name = _('invoice line')
        verbose_name_plural = _('invoice lines')

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:invoiceline', args=[self.pk])

    def clean(self):
        super().clean()
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
