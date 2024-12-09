from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel
from netbox.models.features import ContactsMixin
from utilities.choices import ChoiceSet


class StatusChoices(ChoiceSet):
    key = 'Contract.status'

    STATUS_ACTIVE = 'Active'
    STATUS_CANCELED = 'Cancled'

    CHOICES = [
        (STATUS_ACTIVE, 'Active', 'green'),
        (STATUS_CANCELED, 'Canceled', 'red'),
    ]


class AccountingDimensionStatusChoices(ChoiceSet):
    key = 'AccountingDimension.status'

    STATUS_ACTIVE = 'Active'
    STATUS_INACTIVE = 'Inactive'

    CHOICES = [
        (STATUS_ACTIVE, 'Active', 'green'),
        (STATUS_INACTIVE, 'Inactive', 'red'),
    ]


class InternalEntityChoices(ChoiceSet):
    key = 'Contract.internal_partie'

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

CURRENCY_DEFAULT = CurrencyChoices.CHOICES[0][0]

class AccountingDimension(NetBoxModel):
    name = models.CharField(max_length=20)
    value = models.CharField(max_length=20)
    status = models.CharField(
        max_length=50,
        choices=AccountingDimensionStatusChoices,
        default=StatusChoices.STATUS_ACTIVE,
    )
    comments = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:accountingdimension', args=[self.pk])

    @property
    def dimension(self):
        return ''.join([self.name, ':', self.value])

    def __str__(self):
        return self.dimension

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'value'], name='unique_accounting_dimension'
            )
        ]


class ServiceProvider(ContactsMixin, NetBoxModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    portal_url = models.URLField(blank=True, verbose_name='Portal URL')
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:serviceprovider', args=[self.pk])


class ContractAssignment(NetBoxModel):
    content_type = models.ForeignKey(to=ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey(ct_field='content_type', fk_field='object_id')
    contract = models.ForeignKey(
        to='Contract', on_delete=models.CASCADE, related_name='assignments'
    )
    clone_fields = ('content_type', 'object_id', 'contract')

    class Meta:
        ordering = ('contract',)
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:contractassignment', args=[self.pk])


class Contract(NetBoxModel):
    name = models.CharField(max_length=100)

    external_partie_object_type = models.ForeignKey(
        to=ContentType, on_delete=models.CASCADE, blank=True, null=True
    )
    external_partie_object_id = models.PositiveBigIntegerField(blank=True, null=True)
    external_partie_object = GenericForeignKey(
        ct_field='external_partie_object_type', fk_field='external_partie_object_id'
    )

    external_reference = models.CharField(max_length=100, blank=True, null=True)
    internal_partie = models.CharField(
        max_length=50,
        choices=InternalEntityChoices,
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='contracts',
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=50, choices=StatusChoices, default=StatusChoices.STATUS_ACTIVE
    )
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    initial_term = models.IntegerField(
        help_text='In month', default=12, blank=True, null=True
    )
    renewal_term = models.IntegerField(
        help_text='In month', default=12, blank=True, null=True
    )
    currency = models.CharField(
        max_length=3, choices=CurrencyChoices, default=CURRENCY_DEFAULT
    )
    accounting_dimensions = models.JSONField(null=True, blank=True)
    yrc = models.DecimalField(
        verbose_name='yearly recuring cost',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    mrc = models.DecimalField(
        verbose_name='Monthly recuring cost',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    nrc = models.DecimalField(
        verbose_name='None recuring cost', default=0, max_digits=10, decimal_places=2
    )
    invoice_frequency = models.IntegerField(
        help_text='The frequency of invoices in month', default=1
    )
    documents = models.URLField(blank=True)
    comments = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name='childs', null=True, blank=True
    )

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:contract', args=[self.pk])

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(
                fields=['external_partie_object_type', 'external_partie_object_id']
            ),
        ]

    def __str__(self):
        return self.name


class Invoice(NetBoxModel):
    number = models.CharField(max_length=100)
    template = models.BooleanField(blank=True, null=True, default=False)
    date = models.DateField(blank=True, null=True)
    contracts = models.ManyToManyField(
        Contract,
        related_name='invoices',
        blank=True,
    )
    period_start = models.DateField(blank=True, null=True)
    period_end = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=3, choices=CurrencyChoices, default=CURRENCY_DEFAULT
    )
    accounting_dimensions = models.JSONField(null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    documents = models.URLField(blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ('-period_start',)

    def __str__(self):
        return self.number

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
        to='Invoice', on_delete=models.CASCADE, related_name='invoicelines'
    )
    currency = models.CharField(
        max_length=3, choices=CurrencyChoices, default=CURRENCY_DEFAULT
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    accounting_dimensions = models.ManyToManyField(AccountingDimension, blank=True)
    comments = models.TextField(blank=True)

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
                raise ValidationError(
                    'Sum of invoice line amount greater than invoice amount'
                )
        else:
            previous_amount = self.__class__.objects.get(pk=self.pk).amount
            if amount > (
                invoice.amount - invoice.total_invoicelines_amount + previous_amount
            ):
                raise ValidationError(
                    'Sum of invoice line amount greater than invoice amount'
                )
