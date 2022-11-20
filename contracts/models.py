from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.db import models
from netbox.models import NetBoxModel

class Contract(NetBoxModel):
    name = models.CharField(
        max_length=100
    )
    external_partie = models.CharField(
        max_length=30
    )

    internal_partie = models.CharField(
        max_length=30
    )

    circuit = models.ForeignKey(
        to='circuits.Circuit',
        on_delete=models.PROTECT,
        related_name='contract'
    )

    comments = models.TextField(
        blank=True
    )

    def get_absolute_url(self):
        return reverse('plugins:contracts:contract', args=[self.pk])

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

    class Meta:
        ordering = ('number',)

    def __str__(self):
        return self.number

    def get_absolute_url(self):
        return reverse('plugins:contracts:invoice', args=[self.pk])
