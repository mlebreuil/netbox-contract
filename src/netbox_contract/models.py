from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from utilities.choices import ChoiceSet
from netbox.models import NetBoxModel
from circuits.models import Circuit

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

    ENTITY_CH1 = 'Nagravision Sarl'
    ENTITY_US1 = 'Nagra USA'

    CHOICES = [
        (ENTITY_CH1, 'Nagravision Sarl', 'green'),
        (ENTITY_US1, 'Nagra USA', 'red'),
    ]

class ServiceProvider(NetBoxModel):
    name = models.CharField(
        max_length=100
    )
    slug = models.SlugField(
        max_length=100,
        unique=True
    )
    contacts = GenericRelation(
        to='tenancy.ContactAssignment'
    )
    portal_url = models.URLField(
        blank=True,
        verbose_name='Portal URL'
    )
    comments = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:serviceprovider', args=[self.pk])

class Contract(NetBoxModel):
    name = models.CharField(
        max_length=100
    )
    external_partie = models.ForeignKey(
        to=ServiceProvider,
        on_delete=models.CASCADE,
        related_name='contracts'
    )
    internal_partie = models.CharField(
        max_length=50,
        choices=InternalEntityChoices,
        default=StatusChoices.STATUS_ACTIVE
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='contracts',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=50,
        choices=StatusChoices,
        default=StatusChoices.STATUS_ACTIVE
    )
    start_date = models.DateField()
    initial_term = models.IntegerField(
        help_text = "In month",
        default = 12
    )
    renewal_term = models.IntegerField(
        help_text = "In month",
        default = 12
    )
    mrc = models.DecimalField(
        verbose_name = "Monthly recuring cost",
        max_digits = 10,
        decimal_places= 2
    )
    nrc = models.DecimalField(
        verbose_name = "None recuring cost",
        default = 0,
        max_digits = 10,
        decimal_places= 2
    )
    invoice_frequency = models.IntegerField(
        help_text = "The frequency of invoices in month",
        default = 1
    )
    circuit = models.ManyToManyField(Circuit,
        related_name='contracts'
    )
    comments = models.TextField(
        blank=True
    )

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:contract', args=[self.pk])

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

class Invoice(NetBoxModel):
    number = models.CharField(
        max_length=100
    )

    contract = models.ForeignKey(
        to=Contract,
        on_delete=models.CASCADE,
        related_name='invoice'
    )

    period_start = models.DateField()

    period_end = models.DateField()

    amount = models.DecimalField(
        max_digits = 10,
        decimal_places= 2
    )

    class Meta:
        ordering = ('-period_start',)

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse('plugins:netbox_contract:invoice', args=[self.pk])
