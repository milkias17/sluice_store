from django import forms
from django.utils import timezone

from core.models import Shipment
from core.utils import get_city, haversine


class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            class_str = None
            print(visible.widget_type)
            match visible.widget_type:
                case "text" | "number":
                    class_str = "input input-bordered"
                case "checkbox":
                    class_str = "checkbox"
                case "select" | "selectmultiple":
                    class_str = "select select-bordered"
                case "clearablefile":
                    class_str = "file-input file-input-bordered"
                case _:
                    class_str = "input input-bordered"

            visible.field.widget.attrs["class"] = class_str


# 100 KM = 7 Liters
# 1 Liter = 100Birr
# 1 day = 20 KM
class ShipmentForm(BaseModelForm):
    class Meta:
        model = Shipment
        fields = ["shipment_address", "item_count"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        city = get_city(instance.shipment_address)
        if not city:
            raise forms.ValidationError("Invalid city")

        current_location = 9.0300, 38.7400
        distance_diff = haversine(
            current_location[0], current_location[1], city.lat, city.lng
        )
        if distance_diff == 0:
            distance_diff = 5
        num_liters = (distance_diff * 7) / 100
        cost = num_liters * 100
        instance.shipment_cost = cost
        instance.estimated_delivery_date = timezone.now() + timezone.timedelta(
            days=distance_diff // 20
        )
        if commit:
            instance.save()
        return instance
