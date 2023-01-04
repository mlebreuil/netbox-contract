from django.urls import path
from netbox.views.generic import ObjectChangeLogView
from . import models, views

urlpatterns = (
    # Service Providers
    path('serviceproviders/', views.ServiceProviderListView.as_view(), name='serviceprovider_list'),
    path('serviceproviders/add/', views.ServiceProviderEditView.as_view(), name='serviceprovider_add'),
    path('serviceproviders/import/', views.ServiceProviderBulkImportView.as_view(), name='serviceprovider_import'),
    path('serviceproviders/edit/', views.ServiceProviderBulkEditView.as_view(), name='serviceprovider_bulk_edit'),
    path('serviceproviders/delete/', views.ServiceProviderBulkDeleteView.as_view(), name='serviceprovider_bulk_delete'),
    path('serviceproviders/<int:pk>/', views.ServiceProviderView.as_view(), name='serviceprovider'),
    path('serviceproviders/<int:pk>/edit/', views.ServiceProviderEditView.as_view(), name='serviceprovider_edit'),
    path('serviceproviders/<int:pk>/delete/', views.ServiceProviderDeleteView.as_view(), name='serviceprovider_delete'),
    path('serviceproviders/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='serviceprovider_changelog', kwargs={
        'model': models.ServiceProvider
    }),

    # Contracts
    path('contracts/', views.ContractListView.as_view(), name='contract_list'),
    path('contracts/add/', views.ContractEditView.as_view(), name='contract_add'),
    path('contracts/import/', views.ContractBulkImportView.as_view(), name='contract_import'),
    path('contracts/edit/', views.ContractBulkEditView.as_view(), name='contract_bulk_edit'),
    path('contracts/delete/', views.ContractBulkDeleteView.as_view(), name='contract_bulk_delete'),
    path('contracts/<int:pk>/', views.ContractView.as_view(), name='contract'),
    path('contracts/<int:pk>/edit/', views.ContractEditView.as_view(), name='contract_edit'),
    path('contracts/<int:pk>/delete/', views.ContractDeleteView.as_view(), name='contract_delete'),
    path('contracts/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='contract_changelog', kwargs={
        'model': models.Contract
    }),

    # Contract invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', views.InvoiceEditView.as_view(), name='invoice_add'),
    path('invoices/import/', views.InvoiceBulkImportView.as_view(), name='invoice_import'),
    path('invoices/edit/', views.InvoiceBulkEditView.as_view(), name='invoice_bulk_edit'),
    path('invoices/delete/', views.InvoiceBulkDeleteView.as_view(), name='invoice_bulk_delete'),
    path('invoices/<int:pk>/', views.InvoiceView.as_view(), name='invoice'),
    path('invoices/<int:pk>/edit/', views.InvoiceEditView.as_view(), name='invoice_edit'),
    path('invoices/<int:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/<int:pk>/changelog/', ObjectChangeLogView.as_view(), name='invoice_changelog', kwargs={
        'model': models.Invoice
    }),


)