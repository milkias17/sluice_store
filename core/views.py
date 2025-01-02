import json
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView
from core.forms import ShipmentForm
from core.models import Shipment, ShipmentStatus, Transaction, TransactionStatus


# Create your views here.
def index(request):
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
            transaction.status = TransactionStatus.SUCCESS
            transaction.save()
            self.object.shipment_status = ShipmentStatus.IN_PROGRESS
            self.object.save()
            return HttpResponseRedirect(transaction.checkout_url)


class ShipmentListView(LoginRequiredMixin, ListView):
    model = Shipment
    template_name_suffix = "_list"
    context_object_name = "shipments"


def handle_successful_payment(request: HttpRequest):
    body = request.body
    print(body)
    data = json.loads(body)
    print(data)
    return HttpResponse(data, status=200)

def about_us(request):
    return render(request, "about_us.html")
