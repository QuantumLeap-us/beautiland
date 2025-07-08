import os, sys, shutil, traceback, requests, re
from apps.home.models import SystemParameters, Customer, Order, Product
from datetime import datetime, timedelta
from django.http import FileResponse
from django.core.cache import cache
from retry import retry
from apps.home.crud import manager
from googletrans import Translator


def remove_file(file_path):
    if os.path.exists(file_path):
        shutil.rmtree(file_path)
        response = "Success"
    else:
        response = "File not found"
    return response


def check_customer_activity():
    try:
        customer_sys_param = SystemParameters.objects.filter(system_parameter="Inactive Customer").values("name").first()
        before_months = int(customer_sys_param["name"])
        current_date = datetime.now()
        months_ago = current_date - timedelta(days=30*before_months)

        customer_ids = list(Customer.objects.filter(created_date__lt=months_ago).values_list("id", flat=True))
        inactive_customer_ids = []
        order_data = list(Order.objects.filter(customer_id__in=customer_ids, created_date__gt=months_ago).values_list("customer_id", flat=True))
        if order_data:
            for customer_id in customer_ids:
                if customer_id not in order_data and customer_id not in inactive_customer_ids:
                    inactive_customer_ids.append(customer_id)
        else:
            inactive_customer_ids = customer_ids

        if inactive_customer_ids:
            Customer.objects.filter(id__in=inactive_customer_ids).update(status="inactive customer")
    except Exception as e:
        manager.create_from_exceptions(1, e, traceback.format_exc())


def download_samplefile(full_file_path, file_name):
    if os.path.exists(full_file_path):
        response = FileResponse(open(full_file_path, 'rb'), content_type='text/xlsx')
        response['Content-Disposition'] = f'attachment; filename=' + str(file_name)
        return response
    

def get_user_full_name(first_name, last_name):
    user_full_name = ""
    if first_name and last_name:
        user_full_name = first_name + " " + last_name
    elif first_name and not last_name:
        user_full_name = first_name
    elif not first_name and last_name:
        user_full_name = last_name
    return user_full_name


def get_dict_from_queryset(queryset_data, key, value):
    dict_data = {}
    for query in queryset_data:
        dict_data[query[key]] = query[value]
    
    return dict_data


def set_cache(key, value, timeout=3600):
    cache.set(key, value, timeout) 


def get_cache(key):
    data = cache.get(key)
    return data


def delete_cache(key):
    cache.delete(key)


@retry(tries=3, delay=2)
def convert_currency(amount, from_currency, to_currency):
    # c = CurrencyRates()
    # conversion_rate = c.convert(from_currency, to_currency, amount)
    # return converted_amount

    response = requests.get(f"https://api.frankfurter.app/latest?amount={amount}&from={from_currency}&to={to_currency}")
    if response.status_code == 200:
        conversion_rate = response.json()["rates"][to_currency]
        return conversion_rate
    else:
        return None

    
def update_customer_accumulated_sales(customer_id):
    accumlated_sales = 0
    order_data_total_cost = Order.objects.filter(customer_id=customer_id, is_deleted=False).exclude(order_status__in=["cancelled", "rejected", "draft"]).values("id", "customer_id", "currency", "total_cost")
    for od_cost in order_data_total_cost:
        total_cost = od_cost["total_cost"]
        if str(od_cost["currency"]).lower() != "hkd":
            converted_price = convert_currency(total_cost, od_cost["currency"], "HKD")
            if converted_price:
                total_cost = converted_price

        accumlated_sales += float(total_cost)
    Customer.objects.filter(id=customer_id).update(accumlated_sales=accumlated_sales)


def translate_text(text, src_lang, dest_lang):
    translator = Translator()
    translation = translator.translate(text, src=src_lang, dest=dest_lang)
    return translation.text


def is_chinese(text):
    # Check if the text contains any Chinese characters
    return bool(re.search(r'[\u4e00-\u9FFF]', text))

def is_english(text):
    # Check if the text contains any English letters
    return bool(re.search(r'[a-zA-Z]', text))

class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value