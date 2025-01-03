import json
from chapa import verify_webhook
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView
from core.forms import ShipmentForm
from core.models import Shipment, ShipmentStatus, Transaction, TransactionStatus
from dotenv import dotenv_values

config = dotenv_values()


# Create your views here.
def index(request):
    print(reverse_lazy("admin_list_delivered_orders"))
    return render(request, "home.html")


def order(request):
    return render(request, "order.html")


class ShipmentCreateView(LoginRequiredMixin, CreateView):
    model = Shipment
    form_class = ShipmentForm
    template_name_suffix = "_create"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("confirm_order", kwargs={"pk": str(self.object.id)})


class ShipmentConfirmView(LoginRequiredMixin, DetailView):
    model = Shipment
    template_name_suffix = "_confirm"
    context_object_name = "shipment"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.shipment_status == "IN_PROGRESS":
            return redirect("order_detail", kwargs={"pk": str(self.object.id)})
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        transaction = Transaction.initialize(
            self.request.user, amount=self.object.total_cost, shipment=self.object
        )
        if transaction.status == TransactionStatus.FAILED:
            messages.error(self.request, "Transaction Failed")
            return redirect("order_detail", kwargs={"pk": str(self.object.id)})
        else:
            return HttpResponseRedirect(transaction.checkout_url)


class ShipmentListView(LoginRequiredMixin, ListView):
    model = Shipment
    template_name_suffix = "_list"
    context_object_name = "shipments"


class GroupRequiredMixin(UserPassesTestMixin):
    group_name = None

    def test_func(self):
        return self.request.user.groups.filter(name=self.group_name).exists()

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized to access this page")
        referrer = self.request.META.get("HTTP_REFERER")
        if referrer:
            return redirect(referrer)
        return redirect("index")


class AdminDeliveredShipmentListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Shipment
    template_name_suffix = "_list"
    context_object_name = "shipments"
    group_name = "admin"
    queryset = Shipment.objects.filter(shipment_status=ShipmentStatus.DELIVERED)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["title"] = "Delivered Shipments"
        return context


class AdminPendingShipmentListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    model = Shipment
    template_name_suffix = "_admin_list"
    context_object_name = "shipments"
    group_name = "admin"
    queryset = Shipment.objects.filter(shipment_status=ShipmentStatus.IN_PROGRESS)

    def post(self, request, *args, **kwargs):
        shipment_id = request.POST.get("shipment_id")
        shipment = Shipment.objects.get(id=shipment_id)
        shipment.shipment_status = ShipmentStatus.DELIVERED
        shipment.actual_delivery_date = timezone.now()
        shipment.save()

        return redirect(reverse_lazy("admin_list_pending_orders"))


def handle_successful_payment(request: HttpRequest):
    if not verify_webhook(
        secret_key=config.get("WEBHOOK_SECRET_KEY"),
        body=request.body,
        chapa_signature=request.headers.get("Chapa-Signature"),
    ):
        return HttpResponse("Invalid signature", status=400)
    body = request.body
    print(body)
    data = json.loads(body)
    if data["event"] != "charge.success" or data["event"] != "payout.success":
        return HttpResponse("Invalid event", status=400)

    transaction_id = data["tx_ref"]
    transaction = Transaction.objects.get(id=transaction_id)
    transaction.status = TransactionStatus.SUCCESS
    shipment = transaction.shipment
    shipment.status = ShipmentStatus.IN_PROGRESS
    shipment.save()
    transaction.save()
    return HttpResponse("Success", status=200)


def about_us(request):
    return render(request, "about_us.html")
