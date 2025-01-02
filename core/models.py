from django.db import models
from core.utils import generate_tracking_number, get_cities
from django.urls import reverse_lazy
from core.transactions import chapa
from django.contrib.auth.models import User
import uuid


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TransactionStatus(models.TextChoices):
    CREATED = "Created", "CREATED"
    PENDING = "Pending", "PENDING"
    SUCCESS = "Success", "SUCCESS"
    FAILED = "Failed", "FAILED"


class Transaction(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.FloatField()
    currency = models.CharField(max_length=25, default="ETB")

    payment_title = models.CharField(max_length=255, default="Payment")
    description = models.TextField(null=True, blank=True)

    status = models.CharField(
        max_length=50,
        choices=TransactionStatus.choices,
        default=TransactionStatus.CREATED,
    )

    response_dump = models.JSONField(
        default=dict, blank=True
    )  # incase the response is valuable in the future
    checkout_url = models.URLField(null=True, blank=True)

    @staticmethod
    def initialize(user: User, amount: float, shipment: "Shipment"):
        transaction = Transaction(user=user, amount=amount)
        transaction.save()
        shipment.transaction = transaction
        shipment.save()
        response = chapa.initialize(
            email=user.email,
            amount=amount,
            first_name=user.first_name,
            last_name=user.last_name,
            tx_ref=transaction.id,
            customization={"title": "SluiceStore"},
            return_url="http://localhost:8000" + reverse_lazy("index"),
            callback_url="http://localhost:8000" + reverse_lazy("transaction_success"),
        )
        if response["status"] == "failed":
            transaction.status = TransactionStatus.FAILED
            transaction.save()
            return transaction

        transaction.checkout_url = response["data"]["checkout_url"]
        transaction.save()
        return transaction


class ShipmentStatus(models.TextChoices):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"


class Shipment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, null=True, blank=True
    )
    shipment_status = models.CharField(
        choices=ShipmentStatus.choices, max_length=50, default=ShipmentStatus.PENDING
    )
    estimated_delivery_date = models.DateField()
    actual_delivery_date = models.DateField(null=True, blank=True)
    shipment_address = models.TextField(
        choices=list(map(lambda c: (c.city, c.city), get_cities()))
    )
    shipment_cost = models.DecimalField(max_digits=10, decimal_places=2)
    item_count = models.PositiveIntegerField(verbose_name="Number of units")

    @property
    def total_cost(self):
        return self.shipment_cost + (8_000 * self.item_count)

    @property
    def material_cost(self):
        return 8_000
