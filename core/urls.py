from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "shipper/pending-orders",
        views.AdminPendingShipmentListView.as_view(),
        name="admin_list_pending_orders",
    ),
    path(
        "shipper/delivered-orders",
        views.AdminDeliveredShipmentListView.as_view(),
        name="admin_list_delivered_orders",
    ),
    path("order/", views.ShipmentCreateView.as_view(), name="order"),
    path("order/<slug:pk>/", views.ShipmentConfirmView.as_view(), name="confirm_order"),
    path(
        "order/detail/<slug:pk>/",
        views.ShipmentConfirmView.as_view(),
        name="order_detail",
    ),
    path("orders/", views.ShipmentListView.as_view(), name="list_orders"),
    path("about/", views.about_us, name="about_us"),
    path("test/", views.handle_successful_payment, name="transaction_success"),
]
