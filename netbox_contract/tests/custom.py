from django.urls import reverse
from utilities.testing.api import APITestCase as NetBoxAPITestCase
from utilities.testing.views import ModelViewTestCase as NetBoxModelViewTestCase


class ModelViewTestCase(NetBoxModelViewTestCase):
    def _get_base_url(self):
        return f'plugins:{self.model._meta.app_label}:{self.model._meta.model_name}_{{}}'


class APITestCase(NetBoxAPITestCase):
    def _get_detail_url(self, instance):
        viewname = f'plugins-api:{self._get_view_namespace()}:{instance._meta.model_name}-detail'
        return reverse(viewname, kwargs={'pk': instance.pk})

    def _get_list_url(self):
        viewname = f'plugins-api:{self._get_view_namespace()}:{self.model._meta.model_name}-list'
        return reverse(viewname)
