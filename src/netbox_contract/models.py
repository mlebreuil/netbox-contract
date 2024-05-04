from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
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


class ServiceProvider(ContactsMixin, NetBoxModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    contacts = GenericRelation(to='tenancy.ContactAssignment')
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
        max_length=3, choices=CurrencyChoices, default=CurrencyChoices.CURRENCY_USD
    )
    accounting_dimensions = models.JSONField(null=True, blank=True)
    mrc = models.DecimalField(
        verbose_name='Monthly recuring cost', max_digits=10, decimal_places=2
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
    date = models.DateField(blank=True, null=True)
    contracts = models.ManyToManyField(
        Contract,
        related_name='invoices',
        blank=True,
    )
    period_start = models.DateField()
    period_end = models.DateField()
    currency = models.CharField(
        max_length=3, choices=CurrencyChoices, default=CurrencyChoices.CURRENCY_USD
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
