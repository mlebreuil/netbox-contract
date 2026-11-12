# Testing Guide

## Test File Organization

```
tests/
├── test_models.py    # Model creation, validation, str(), get_absolute_url()
├── test_views.py     # UI view status codes, permissions
├── test_api.py       # REST API CRUD, filtering, permissions
└── test_forms.py     # Form validation, field behavior
```

## Running Tests

```bash
# From NetBox root directory
python manage.py test netbox_myplugin.tests -v 2

# Single test file
python manage.py test netbox_myplugin.tests.test_api -v 2

# Single test method
python manage.py test netbox_myplugin.tests.test_api.AccessListAPITest.test_list -v 2
```

## Model Tests

```python
from django.test import TestCase
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from .models import AccessList

class AccessListModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        site = Site.objects.create(name='Test Site', slug='test-site')
        manufacturer = Manufacturer.objects.create(name='Test', slug='test')
        device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='Test Model', slug='test-model'
        )
        role = DeviceRole.objects.create(name='Test Role', slug='test-role')
        cls.device = Device.objects.create(
            name='test-device', site=site, device_type=device_type, role=role
        )

    def test_create(self):
        acl = AccessList.objects.create(
            name='test-acl', device=self.device, type='standard'
        )
        self.assertEqual(str(acl), 'test-acl')
        self.assertIsNotNone(acl.pk)

    def test_get_absolute_url(self):
        acl = AccessList.objects.create(
            name='test-acl', device=self.device, type='standard'
        )
        self.assertIn('/plugins/', acl.get_absolute_url())

    def test_unique_constraint(self):
        AccessList.objects.create(name='acl1', device=self.device, type='standard')
        with self.assertRaises(Exception):
            AccessList.objects.create(name='acl1', device=self.device, type='standard')
```

## API Tests

```python
from django.urls import reverse
from rest_framework import status
from utilities.testing import APITestCase
from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from .models import AccessList

class AccessListAPITest(APITestCase):
    model = AccessList

    @classmethod
    def setUpTestData(cls):
        site = Site.objects.create(name='Test Site', slug='test-site')
        manufacturer = Manufacturer.objects.create(name='Test', slug='test')
        device_type = DeviceType.objects.create(
            manufacturer=manufacturer, model='Test Model', slug='test-model'
        )
        role = DeviceRole.objects.create(name='Test Role', slug='test-role')
        cls.device = Device.objects.create(
            name='test-device', site=site, device_type=device_type, role=role
        )

    def test_list(self):
        AccessList.objects.create(name='acl1', device=self.device, type='standard')
        url = reverse('plugins-api:netbox_myplugin-api:accesslist-list')
        response = self.client.get(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create(self):
        url = reverse('plugins-api:netbox_myplugin-api:accesslist-list')
        data = {'name': 'new-acl', 'device': self.device.pk, 'type': 'standard'}
        response = self.client.post(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AccessList.objects.count(), 1)

    def test_update(self):
        acl = AccessList.objects.create(name='acl1', device=self.device, type='standard')
        url = reverse('plugins-api:netbox_myplugin-api:accesslist-detail', args=[acl.pk])
        data = {'name': 'updated-acl', 'device': self.device.pk, 'type': 'extended'}
        response = self.client.put(url, data, format='json', **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete(self):
        acl = AccessList.objects.create(name='acl1', device=self.device, type='standard')
        url = reverse('plugins-api:netbox_myplugin-api:accesslist-detail', args=[acl.pk])
        response = self.client.delete(url, **self.header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_filter_by_device(self):
        AccessList.objects.create(name='acl1', device=self.device, type='standard')
        url = reverse('plugins-api:netbox_myplugin-api:accesslist-list')
        response = self.client.get(url, {'device_id': self.device.pk}, **self.header)
        self.assertEqual(response.data['count'], 1)
```

## View Tests

```python
from utilities.testing import ViewTestCases

class AccessListViewTest(ViewTestCases.PrimaryObjectViewTestCase):
    model = AccessList

    @classmethod
    def setUpTestData(cls):
        # Create prerequisite objects
        ...
        # Create test instances (required by ViewTestCases)
        AccessList.objects.create(name='acl1', device=device, type='standard')
        AccessList.objects.create(name='acl2', device=device, type='extended')
        AccessList.objects.create(name='acl3', device=device, type='standard')

        cls.form_data = {
            'name': 'new-acl',
            'device': device.pk,
            'type': 'standard',
            'tags': [],
        }
        cls.bulk_edit_data = {'type': 'extended'}
```

`ViewTestCases.PrimaryObjectViewTestCase` automatically tests list, detail, create,
edit, delete, and bulk operations. Provide `form_data` and `bulk_edit_data`.

## FilterSet Tests

The mixin checks that every model field has a filter and exercises the standard lookups.
NetBox 4.7 renamed it (`ChangeLoggedFilterSetTests` → `ChangeLoggedFilterSetTestMixin`,
`BaseFilterSetTests` → `BaseFilterSetTestMixin`); import version-safely when spanning 4.5–4.7:

```python
from django.test import TestCase
try:
    from utilities.testing import ChangeLoggedFilterSetTestMixin                 # 4.7+
except ImportError:
    from utilities.testing import ChangeLoggedFilterSetTests as ChangeLoggedFilterSetTestMixin  # 4.5/4.6
from .filtersets import AccessListFilterSet
from .models import AccessList

class AccessListFilterSetTest(TestCase, ChangeLoggedFilterSetTestMixin):
    queryset = AccessList.objects.all()
    filterset = AccessListFilterSet

    @classmethod
    def setUpTestData(cls):
        ...   # create ≥3 objects with distinct field values

    def test_type(self):
        params = {'type': ['standard']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)
```

## Search Index Assertions (4.7+)

Global search cache updates are deferred to after the transaction commits. Django `TestCase`
never runs on-commit callbacks on its own, so a test that saves an object and then asserts it
appears in `search_backend.search(...)` must execute them explicitly:

```python
from netbox.search.backends import search_backend

def test_searchable(self):
    with self.captureOnCommitCallbacks(execute=True):
        AccessList.objects.create(name='edge-acl', device=self.device, type='standard')
    self.assertTrue(any(r.object.name == 'edge-acl' for r in search_backend.search('edge-acl')))
```

(With no RQ worker listening — the usual case under `manage.py test` — the flush indexes inline.)

## Tips

- `APITestCase` provides `self.header` with a pre-authenticated admin token
- `setUpTestData` (classmethod) is faster than `setUp` — shared across tests in class
- Always create enough objects (≥3) for bulk operation tests
- Test permission enforcement: use `ObjectPermission` to verify restricted access
- NetBox 4.7 requires PostgreSQL 15+ — the system check fails under `manage.py test` on 14
