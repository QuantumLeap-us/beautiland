from datetime import datetime
from django.http import HttpRequest
from apps.home.models import Product
from apps.home.crud import utils, manager
import traceback


class CustomProductStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self.change_product_status_acc_onboarddate(request)
        return response

    def change_product_status_acc_onboarddate(self, request):
        try:
            last_execution_date = utils.get_cache("last_execution_date")
            today_date = datetime.now().date()
            if not last_execution_date or last_execution_date != today_date:
                Product.objects.filter(onboarding_date__lte=today_date).exclude(status__in=["draft", "in sales"]).update(status="in sales")
                end_of_day = datetime.combine(today_date, datetime.max.time())
                time_until_midnight = end_of_day - datetime.now()
                utils.set_cache("last_execution_date", datetime.now().date(), time_until_midnight.seconds)
        except Exception as e:
            manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
