from django.urls import path
from .views import login_user, warehouse_list_create, warehouse_update_delete, upload_product_master, get_product_master, get_data_sources_status, trigger_sync

urlpatterns = [
    path('login/', login_user),  # ✅ This exposes /api/login/
    path('warehouses/', warehouse_list_create),
    path('warehouses/<int:pk>/', warehouse_update_delete),
    path('product-master/upload/', upload_product_master),
    path('product-master/', get_product_master),
    path('sync/status/', get_data_sources_status),
    path('sync/<str:key>/', trigger_sync),
]
