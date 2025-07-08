# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.shortcuts import redirect
from apps.home.crud.product import *
from apps.home.crud.inventory import *
from apps.home.crud.delivery import *
from apps.home.crud.category import *
from apps.home.crud.customer import *
from apps.home.crud.purchase import *
from apps.home.crud.order import *
from apps.home.crud.voucher import *
from apps.home.crud.supplier import *
from apps.home.crud.quotation import *
from apps.home.crud.instock import *
from apps.home.crud.address import *
from apps.home.forms.discountform import DiscountSchemeForm, CouponForm, PromotionForm, PromoCodeForm
from apps.home.forms.transactionform import TransactionForm
from apps.home.model.discount import DiscountScheme, Coupon, Promotion, PromoCode
from apps.home.models import SystemParameters, SystemParametersForId
from apps.home.crud import utils, manager
from django.utils.safestring import mark_safe
import traceback
from apps.home.crud import transaction as transaction_crud


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    # html_template = loader.get_template('home/product-list.html')
    # return HttpResponse(html_template.render(context, request))

    return redirect("supplier-list")


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


def error_500(request):
    return render(request, 'home/page-500.html')

def error_404(request,  exception):
    return render(request, 'home/page-404.html')


# 前台展示页面 - 无需登录
def frontend_home(request):
    """前台首页 - 产品展示页面"""
    try:
        # 获取产品数据用于展示
        from apps.home.models import Product
        featured_products = Product.objects.filter(is_deleted=False)[:6]  # 获取6个产品展示

        context = {
            'featured_products': featured_products,
            'page_title': 'Beautiland - 美容保健专家'
        }
        return render(request, 'frontend/home.html', context)
    except Exception as e:
        # 如果出错，返回简单页面
        return render(request, 'frontend/home.html', {'page_title': 'Beautiland'})


def frontend_products(request):
    """前台产品列表页面 - 无需登录"""
    try:
        from apps.home.models import Product
        products = Product.objects.filter(is_deleted=False)

        context = {
            'products': products,
            'page_title': 'Beautiland - 产品展示'
        }
        return render(request, 'frontend/products.html', context)
    except Exception as e:
        return render(request, 'frontend/products.html', {'page_title': 'Beautiland - 产品展示'})


@login_required(login_url="/login/")
def system_parameters_list(request):
    try:
        system_params_data = []
        system_parameteres = SystemParameters.objects.filter(is_deleted=False).values("id", "system_parameter", "name", "created_by_id", "created_by__first_name", "created_by__last_name", "created_date").order_by("-id")
        for system_param in system_parameteres:
            created_by = "-"
            if system_param["created_by_id"]:
                first_name = system_param["created_by__first_name"]
                last_name = system_param["created_by__last_name"]
                created_by = utils.get_user_full_name(first_name, last_name)

            sales_persons = []
            if str(system_param["system_parameter"]).lower() == "sales person":
                if system_param["name"]:
                    users = User.objects.filter(id__in=system_param["name"].split(", "), is_active=True).values("id", "first_name", "last_name").order_by('-id')
                    for user in users:
                        sales_person = utils.get_user_full_name(user["first_name"], user["last_name"])
                        if sales_person not in sales_persons:
                            sales_persons.append(sales_person)

            system_params_data.append({
                "id": system_param["id"],
                "system_parameter": system_param["system_parameter"],
                "name": system_param["name"] if not sales_persons else ", ".join(sales_persons),
                "created_by": created_by if created_by else "-",
                "created_on": datetime.strptime(str(system_param["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d") if system_param["created_date"] else "-",
            })
        return render(request, "home/system_parameter_list.html", {"system_parameteres": system_params_data})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


@login_required(login_url="/login/")
def system_parameter(request, id=0):
    system_parameteres = ""
    sales_person_data = []
    sales_persons_ids = ""
    sys_param_prod_id_value = {}
    try:
        if id:
            system_parameteres = SystemParameters.objects.filter(id=id).first()

        sys_param_for_prod_id = SystemParametersForId.objects.filter(is_deleted=False, category__type="Product Category").values("category_id", "value")
        sys_param_prod_id_value = mark_safe(json.dumps((utils.get_dict_from_queryset(sys_param_for_prod_id, "category_id", "value"))))

        if system_parameteres and str(system_parameteres.system_parameter).lower() == "sales person":
            sales_persons_ids = system_parameteres.name
            sales_persons = User.objects.filter(is_active=True).values("id", "username", "first_name", "last_name").order_by('-id')
            for sale_person in sales_persons:
                first_name = sale_person["first_name"]
                last_name = sale_person["last_name"]
                sales_person = utils.get_user_full_name(first_name, last_name)

                sales_person_data.append({
                    "id": sale_person["id"],
                    "full_name": sales_person if sales_person else "",
                })

        categories = list(Category.objects.filter(type="Product Category", parent_id=None).values("id", "name").order_by("-id"))

        if request.method == "POST":
            system_param = request.POST.get("system_parameter")
            product_cat_id = request.POST.get("product_id")

            name = request.POST.get("name") if system_param != "Sales Person" else ", ".join(request.POST.getlist("sales_person"))
            if product_cat_id:
                create_product_id_pattern(request, product_cat_id, name)
                return redirect("system_parameters_list")

            if system_param.lower() == "currency":
                name = name.upper()

            if str(system_param).strip().lower() == "prefix":
                final_prefix_values = []
                prefix_values = str(name).strip().split(", ")
                for pre_val in prefix_values:
                    pre_value = pre_val
                    if "+" not in pre_val:
                        pre_value = "+" + pre_val
                    final_prefix_values.append(pre_value)
                name = ", ".join(final_prefix_values)

            if id == 0:
                exists_sys_param = SystemParameters.objects.filter(system_parameter__icontains=str(system_param).strip().lower(), is_deleted=False).first()
                if exists_sys_param:
                    return render(request, "home/system_parameter.html", {"id": id, "system_parameteres": system_parameteres, "sales_person_data": sales_person_data, "sales_persons_ids": sales_persons_ids, "categories": categories, "sys_param_prod_id_value": sys_param_prod_id_value, "error_msg": "system parameter `" + str(system_param) + "` already exist"})
                SystemParameters.objects.create(system_parameter=str(system_param).strip(), name=name, created_by=request.user)
            else:
                sys_param = SystemParameters.objects.filter(id=id).first()
                validate_msg = check_existed_system_parameters(sys_param, name)
                if validate_msg:
                    return render(request, "home/system_parameter.html", {"id": id, "system_parameteres": system_parameteres, "sales_person_data": sales_person_data, "sales_persons_ids": sales_persons_ids, "categories": categories, "sys_param_prod_id_value": sys_param_prod_id_value, "error_msg": ", ".join(validate_msg)})

                name_li = name.split(",")
                final_name_li = []
                for sys_name in name_li:
                    if sys_name and str(sys_name).strip().lower() not in final_name_li:
                        final_name_li.append(str(sys_name).strip().lower())

                name_data = []
                for final_name in final_name_li:
                    if final_name and str(sys_param.system_parameter).lower() != "sales person":
                        if str(sys_param.system_parameter).lower() in ["currency", "currency of cost"]:
                            name_data.append(final_name.upper())
                        else:
                            name_data.append(final_name.capitalize())

                sys_param.name = ", ".join(name_data) if str(sys_param.system_parameter).lower() != "sales person" else name
                sys_param.created_by = request.user
                sys_param.save()
            return redirect("system_parameters_list")

        return render(request, "home/system_parameter.html", {"id": id, "system_parameteres": system_parameteres, "sales_person_data": sales_person_data, "sales_persons_ids": sales_persons_ids, "categories": categories, "sys_param_prod_id_value": sys_param_prod_id_value})
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return render(request, "home/system_parameter.html", {"id": id, "system_parameteres": system_parameteres, "sales_person_data": sales_person_data, "sales_persons_ids": sales_persons_ids, "categories": categories, "sys_param_prod_id_value": sys_param_prod_id_value, "error_msg": str(e)})


@login_required(login_url="/login/")
def system_parameter_delete(request, id):
    try:
        if id:
            SystemParameters.objects.filter(id=id).update(is_deleted=True)
        return redirect("system_parameters_list")
    except Exception as e:
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return HttpResponse(json.dumps({"code": 0, "msg": str(e)}), content_type="json")


def create_product_id_pattern(request, product_cat_id, name):
    existed_sys_param = SystemParametersForId.objects.filter(category_id=int(product_cat_id)).first()
    if existed_sys_param:
        existed_sys_param.value = str(name).strip()
        existed_sys_param.created_by = request.user
        existed_sys_param.save()
    else:
        SystemParametersForId.objects.create(category_id=int(product_cat_id), value=str(name).strip(), created_by=request.user)


def check_existed_system_parameters(sys_param, name):
    validate_msg = []
    if str(sys_param.system_parameter).lower() == "sales person":
        check_sales_person = []
        old_sales_person = (sys_param.name).split(", ") if sys_param.name else []
        new_sales_person = name.split(", ")
        for old_sp in old_sales_person:
            if old_sp not in new_sales_person:
                check_sales_person.append(int(old_sp))

        if check_sales_person:
            validate_msg = get_existed_salesperson_validate_msg(check_sales_person)

    if str(sys_param.system_parameter).lower() == "prefix":
        check_prefix = []
        old_prefix = (sys_param.name).split(", ") if sys_param.name else []
        new_prefix = name.split(", ")
        for old_pr in old_prefix:
            if old_pr not in new_prefix:
                check_prefix.append(old_pr)

        if check_prefix:
            validate_msg = get_existed_prefix_validate_msg(check_prefix)

    if str(sys_param.system_parameter).lower() == "source":
        check_source = []
        old_source = (sys_param.name).split(", ") if sys_param.name else []
        new_source = name.split(", ")
        for old_sr in old_source:
            if old_sr not in new_source:
                check_source.append(old_sr)

        if check_source:
            validate_msg = get_existed_source_validate_msg(check_source)

    if str(sys_param.system_parameter).lower() == "district in hk":
        check_dt = []
        old_dt_hk = (sys_param.name).split(", ") if sys_param.name else []
        new_dt = name.split(", ")
        for old_dt in old_dt_hk:
            if old_dt not in new_dt:
                check_dt.append(old_dt)

        if check_dt:
            validate_msg = get_existed_district_validate_msg(check_dt)

    if str(sys_param.system_parameter).lower() == "country/district":
        check_country = []
        old_country_hk = (sys_param.name).split(", ") if sys_param.name else []
        new_country = name.split(", ")
        for old_country in old_country_hk:
            if old_country not in new_country:
                check_country.append(old_country)

        if check_country:
            validate_msg = get_existed_country_validate_msg(check_country)

    if str(sys_param.system_parameter).lower() == "industry type":
        check_sys_param = []
        old_sys_param = (sys_param.name).split(", ") if sys_param.name else []
        new_sys_param = name.split(", ")
        for old_sys in old_sys_param:
            if old_sys not in new_sys_param:
                check_sys_param.append(old_sys)

        if check_sys_param:
            validate_msg = get_existed_industry_type_validate_msg(check_sys_param)

    if str(sys_param.system_parameter).lower() == "contact type":
        check_sys_param = []
        old_sys_param = (sys_param.name).split(", ") if sys_param.name else []
        new_sys_param = name.split(", ")
        for old_sys in old_sys_param:
            if old_sys not in new_sys_param:
                check_sys_param.append(old_sys)

        if check_sys_param:
            validate_msg = get_existed_contact_type_validate_msg(check_sys_param)

    if str(sys_param.system_parameter).lower() == "location":
        check_sys_param = []
        old_sys_param = (sys_param.name).split(", ") if sys_param.name else []
        new_sys_param = name.split(", ")
        for old_sys in old_sys_param:
            if old_sys not in new_sys_param:
                check_sys_param.append(old_sys)

        if check_sys_param:
            validate_msg = get_existed_location_validate_msg(check_sys_param)

    if str(sys_param.system_parameter).lower() == "currency":
        check_sys_param = []
        old_sys_param = (sys_param.name).split(", ") if sys_param.name else []
        new_sys_param = name.split(", ")
        for old_sys in old_sys_param:
            if old_sys not in new_sys_param:
                check_sys_param.append(old_sys)

        if check_sys_param:
            validate_msg = get_existed_currency_validate_msg(check_sys_param)

    if str(sys_param.system_parameter).lower() == "unit of measurement":
        check_sys_param = []
        old_sys_param = (sys_param.name).split(", ") if sys_param.name else []
        new_sys_param = name.split(", ")
        for old_sys in old_sys_param:
            if old_sys not in new_sys_param:
                check_sys_param.append(old_sys)

        if check_sys_param:
            validate_msg = get_existed_uom_validate_msg(check_sys_param)

    if str(sys_param.system_parameter).lower() == "currency of cost":
        check_sys_param = []
        old_sys_param = (sys_param.name).split(", ") if sys_param.name else []
        new_sys_param = name.split(", ")
        for old_sys in old_sys_param:
            if old_sys not in new_sys_param:
                check_sys_param.append(old_sys)

        if check_sys_param:
            validate_msg = get_existed_coc_validate_msg(check_sys_param)

    if str(sys_param.system_parameter).lower() == "brand":
        check_sys_param = []
        old_sys_param = (sys_param.name).split(", ") if sys_param.name else []
        new_sys_param = name.split(", ")
        for old_sys in old_sys_param:
            if old_sys not in new_sys_param:
                check_sys_param.append(old_sys)

        if check_sys_param:
            validate_msg = get_existed_brand_validate_msg(check_sys_param)

    return validate_msg


def get_existed_salesperson_validate_msg(check_sales_person):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Customer.objects.filter(sale_person_id__in=check_sales_person).values("customer_id", "sale_person_id", "sale_person__first_name", "sale_person__last_name")
    for sys_param in in_use_sys_param:
        sales_person = utils.get_user_full_name(sys_param["sale_person__first_name"], sys_param["sale_person__last_name"])
        if sales_person not in existed_sys_param:
            existed_sys_param[sales_person] = [sys_param["customer_id"]]
        else:
            existed_sys_param[sales_person].append(sys_param["customer_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Sales person `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Sales person `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_prefix_validate_msg(check_prefix):
    validate_msg = []
    existed_prefix_in_customers = {}
    existed_prefix_in_suppliers = {}
    in_use_prefix_suppliers = Supplier.objects.filter(prefix__in=check_prefix).values("prefix", "supplier_id")
    for supplier in in_use_prefix_suppliers:
        if supplier["prefix"] not in existed_prefix_in_suppliers:
            existed_prefix_in_suppliers[supplier["prefix"]] = [supplier["supplier_id"]]
        else:
            existed_prefix_in_suppliers[supplier["prefix"]].append(supplier["supplier_id"])

    for key, value in existed_prefix_in_suppliers.items():
        msg = "Can't remove Prefix `<b>" + key + "</b>`. It is assigned in the supplier `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Prefix `<b>" + key + "</b>`. It is assigned in the suppliers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    in_use_prefix_customers = Customer.objects.filter(prefix__in=check_prefix).values("prefix", "customer_id")
    for customer in in_use_prefix_customers:
        if customer["prefix"] not in existed_prefix_in_customers:
            existed_prefix_in_customers[customer["prefix"]] = [customer["customer_id"]]
        else:
            existed_prefix_in_customers[customer["prefix"]].append(customer["customer_id"])

    for key, value in existed_prefix_in_customers.items():
        prefix = ""
        if validate_msg:
            prefix = "<br>"
        msg = prefix + "Can't remove Prefix `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = prefix + "Can't remove Prefix `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_source_validate_msg(check_source):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Customer.objects.filter(source__in=check_source).values("customer_id", "source")
    for sys_param in in_use_sys_param:
        if sys_param["source"] not in existed_sys_param:
            existed_sys_param[sys_param["source"]] = [sys_param["customer_id"]]
        else:
            existed_sys_param[sys_param["source"]].append(sys_param["customer_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Source `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Source `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_district_validate_msg(check_dt):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Customer.objects.filter(district_in_hk__in=check_dt).values("customer_id", "district_in_hk")
    for sys_param in in_use_sys_param:
        if sys_param["district_in_hk"] not in existed_sys_param:
            existed_sys_param[sys_param["district_in_hk"]] = [sys_param["customer_id"]]
        else:
            existed_sys_param[sys_param["district_in_hk"]].append(sys_param["customer_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove District in HK `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove District in HK `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_country_validate_msg(check_country):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Customer.objects.filter(country__in=check_country).values("customer_id", "country")
    for sys_param in in_use_sys_param:
        if sys_param["country"] not in existed_sys_param:
            existed_sys_param[sys_param["country"]] = [sys_param["customer_id"]]
        else:
            existed_sys_param[sys_param["country"]].append(sys_param["customer_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Country/District `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Country/District `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_industry_type_validate_msg(check_sys_param):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Customer.objects.filter(industry_type__in=check_sys_param).values("customer_id", "industry_type")
    for sys_param in in_use_sys_param:
        if sys_param["industry_type"] not in existed_sys_param:
            existed_sys_param[sys_param["industry_type"]] = [sys_param["customer_id"]]
        else:
            existed_sys_param[sys_param["industry_type"]].append(sys_param["customer_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Industry Type `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Industry Type `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_contact_type_validate_msg(check_sys_param):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Supplier.objects.filter(contact_type__in=check_sys_param).values("supplier_id", "contact_type")
    for sys_param in in_use_sys_param:
        if sys_param["contact_type"] not in existed_sys_param:
            existed_sys_param[sys_param["contact_type"]] = [sys_param["supplier_id"]]
        else:
            existed_sys_param[sys_param["contact_type"]].append(sys_param["supplier_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Contact Type `<b>" + key + "</b>`. It is assigned in the supplier `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Contact Type `<b>" + key + "</b>`. It is assigned in the suppliers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_location_validate_msg(check_sys_param):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Supplier.objects.filter(location__in=check_sys_param).values("supplier_id", "location")
    for sys_param in in_use_sys_param:
        if sys_param["location"] not in existed_sys_param:
            existed_sys_param[sys_param["location"]] = [sys_param["supplier_id"]]
        else:
            existed_sys_param[sys_param["location"]].append(sys_param["supplier_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Location `<b>" + key + "</b>`. It is assigned in the supplier `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Location `<b>" + key + "</b>`. It is assigned in the suppliers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_currency_validate_msg(check_sys_param):
    validate_msg = []
    existed_sys_param_in_customers = {}
    existed_sys_param_in_suppliers = {}
    existed_sys_param_in_products = {}

    in_use_sys_param_suppliers = Supplier.objects.filter(currency__in=check_sys_param).values("supplier_id", "currency")
    for sys_param_supp in in_use_sys_param_suppliers:
        if sys_param_supp["currency"] not in existed_sys_param_in_suppliers:
            existed_sys_param_in_suppliers[sys_param_supp["currency"]] = [sys_param_supp["supplier_id"]]
        else:
            existed_sys_param_in_suppliers[sys_param_supp["currency"]].append(sys_param_supp["supplier_id"])

    for key, value in existed_sys_param_in_suppliers.items():
        msg = "Can't remove Currency `<b>" + key + "</b>`. It is assigned in the supplier `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Currency `<b>" + key + "</b>`. It is assigned in the suppliers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    in_use_sys_param_customers = Customer.objects.filter(currency__in=check_sys_param).values("customer_id", "currency")

    for sys_param in in_use_sys_param_customers:
        if sys_param["currency"] not in existed_sys_param_in_customers:
            existed_sys_param_in_customers[sys_param["currency"]] = [sys_param["customer_id"]]
        else:
            existed_sys_param_in_customers[sys_param["currency"]].append(sys_param["customer_id"])

    for key, value in existed_sys_param_in_customers.items():
        prefix = ""
        if validate_msg:
            prefix = "<br>"
        msg = prefix + "Can't remove Currency `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = prefix + "Can't remove Currency `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    in_use_sys_param_products = Product.objects.filter(sales_currency__in=check_sys_param).values("product_id", "sales_currency")

    for sys_param in in_use_sys_param_products:
        if sys_param["sales_currency"] not in existed_sys_param_in_products:
            existed_sys_param_in_products[sys_param["sales_currency"]] = [sys_param["product_id"]]
        else:
            existed_sys_param_in_products[sys_param["sales_currency"]].append(sys_param["product_id"])

    for key, value in existed_sys_param_in_products.items():
        prefix = ""
        if validate_msg:
            prefix = "<br>"
        msg = prefix + "Can't remove Currency `<b>" + key + "</b>`. It is assigned in the product `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = prefix + "Can't remove Currency `<b>" + key + "</b>`. It is assigned in the products `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_uom_validate_msg(check_sys_param):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Product.objects.filter(unit_of_measurement__in=check_sys_param).values("product_id", "unit_of_measurement")
    for sys_param in in_use_sys_param:
        if sys_param["unit_of_measurement"] not in existed_sys_param:
            existed_sys_param[sys_param["unit_of_measurement"]] = [sys_param["product_id"]]
        else:
            existed_sys_param[sys_param["unit_of_measurement"]].append(sys_param["product_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Unit of Measurement `<b>" + key + "</b>`. It is assigned in the product `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Unit of Measurement `<b>" + key + "</b>`. It is assigned in the products `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_coc_validate_msg(check_sys_param):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Product.objects.filter(currency_of_cost__in=check_sys_param).values("product_id", "currency_of_cost")
    for sys_param in in_use_sys_param:
        if sys_param["currency_of_cost"] not in existed_sys_param:
            existed_sys_param[sys_param["currency_of_cost"]] = [sys_param["product_id"]]
        else:
            existed_sys_param[sys_param["currency_of_cost"]].append(sys_param["product_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Currency of Cost `<b>" + key + "</b>`. It is assigned in the product `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Currency of Cost `<b>" + key + "</b>`. It is assigned in the products `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg


def get_existed_brand_validate_msg(check_sys_param):
    validate_msg = []
    existed_sys_param = {}
    in_use_sys_param = Product.objects.filter(brand__in=check_sys_param).values("product_id", "brand")
    for sys_param in in_use_sys_param:
        if sys_param["brand"] not in existed_sys_param:
            existed_sys_param[sys_param["brand"]] = [sys_param["product_id"]]
        else:
            existed_sys_param[sys_param["brand"]].append(sys_param["product_id"])

    for key, value in existed_sys_param.items():
        msg = "Can't remove Brand `<b>" + key + "</b>`. It is assigned in the product `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Brand `<b>" + key + "</b>`. It is assigned in the products `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    return validate_msg

@login_required(login_url="/login/")
def transaction_create(request):
    result = transaction_crud.create_transaction(request)
    if isinstance(result, dict) and 'form' in result:
        return render(request, 'home/transaction_form.html', result)
    return JsonResponse(result)

@login_required(login_url="/login/")
def transaction_create_with_redirect(request):
    return transaction_crud.transaction_create_with_redirect(request)

@login_required(login_url="/login/")
def transaction_update(request, transaction_id):
    result = transaction_crud.update_transaction(request, transaction_id)
    if isinstance(result, dict) and 'form' in result:
        return render(request, 'home/transaction_form.html', result)
    return JsonResponse(result)

@login_required(login_url="/login/")
def transaction_detail(request, transaction_id):
    transaction = transaction_crud.Transaction.objects.filter(id=transaction_id, is_deleted=False).first()
    if not transaction:
        return render(request, 'home/page-404.html', {'msg': '事务不存在'})
    return render(request, 'home/transaction_detail.html', {'transaction': transaction, 'role': request.user.role})

@login_required(login_url="/login/")
def transaction_list(request):
    result = transaction_crud.list_transactions(request)
    if isinstance(result, HttpResponse):
        return result
    return render(request, 'home/transaction_list.html', result)

@login_required(login_url="/login/")
def transaction_delete(request, transaction_id):
    result = transaction_crud.delete_transaction(request, transaction_id)
    return JsonResponse(result)

@login_required(login_url="/login/")
def transaction_import(request):
    result = transaction_crud.import_transactions(request)
    return result

@login_required(login_url="/login/")
def transaction_approve(request, transaction_id):
    result = transaction_crud.approve_transaction(request, transaction_id)
    return result

# 新增的动态交易创建视图
@login_required(login_url="/login/")
def create_dynamic_transaction(request):
    result = transaction_crud.create_dynamic_transaction(request)
    if isinstance(result, dict):
        return JsonResponse(result)
    return JsonResponse({"code": 0, "msg": _("Invalid request")})


# 優惠方案管理
@login_required(login_url="/login/")
def discount_scheme_list(request):
    schemes = DiscountScheme.objects.all()
    return render(request, 'home/discount_scheme_list.html', {'schemes': schemes})

@login_required(login_url="/login/")
def discount_scheme_create(request):
    if request.method == "POST":
        form = DiscountSchemeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('discount_scheme_list')
    else:
        form = DiscountSchemeForm()
    return render(request, 'home/discount_scheme_form.html', {'form': form})

@login_required(login_url="/login/")
def discount_scheme_edit(request, pk):
    scheme = get_object_or_404(DiscountScheme, pk=pk)
    if request.method == "POST":
        form = DiscountSchemeForm(request.POST, instance=scheme)
        if form.is_valid():
            form.save()
            return redirect('discount_scheme_list')
    else:
        form = DiscountSchemeForm(instance=scheme)
    return render(request, 'home/discount_scheme_form.html', {'form': form})

@login_required(login_url="/login/")
def discount_scheme_delete(request, pk):
    scheme = get_object_or_404(DiscountScheme, pk=pk)
    scheme.delete()
    return redirect('discount_scheme_list')

# 優惠券管理
@login_required(login_url="/login/")
def coupon_list(request):
    coupons = Coupon.objects.all()
    return render(request, 'home/coupon_list.html', {'coupons': coupons})

@login_required(login_url="/login/")
def coupon_create(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
    else:
        form = CouponForm()
    return render(request, 'home/coupon_form.html', {'form': form})

@login_required(login_url="/login/")
def coupon_edit(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'home/coupon_form.html', {'form': form})

@login_required(login_url="/login/")
def coupon_delete(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.delete()
    return redirect('coupon_list')

# 促銷活動管理
@login_required(login_url="/login/")
def promotion_list(request):
    promotions = Promotion.objects.all()
    return render(request, 'home/promotion_list.html', {'promotions': promotions})

@login_required(login_url="/login/")
def promotion_create(request):
    if request.method == "POST":
        form = PromotionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('promotion_list')
    else:
        form = PromotionForm()
    return render(request, 'home/promotion_form.html', {'form': form})

@login_required(login_url="/login/")
def promotion_edit(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    if request.method == "POST":
        form = PromotionForm(request.POST, instance=promotion)
        if form.is_valid():
            form.save()
            return redirect('promotion_list')
    else:
        form = PromotionForm(instance=promotion)
    return render(request, 'home/promotion_form.html', {'form': form})

@login_required(login_url="/login/")
def promotion_delete(request, pk):
    promotion = get_object_or_404(Promotion, pk=pk)
    promotion.delete()
    return redirect('promotion_list')

# 促銷碼管理
@login_required(login_url="/login/")
def promo_code_list(request):
    promo_codes = PromoCode.objects.all()
    return render(request, 'home/promo_code_list.html', {'promo_codes': promo_codes})

@login_required(login_url="/login/")
def promo_code_create(request):
    if request.method == "POST":
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('promo_code_list')
    else:
        form = PromoCodeForm()
    return render(request, 'home/promo_code_form.html', {'form': form})

@login_required(login_url="/login/")
def promo_code_edit(request, pk):
    promo_code = get_object_or_404(PromoCode, pk=pk)
    if request.method == "POST":
        form = PromoCodeForm(request.POST, instance=promo_code)
        if form.is_valid():
            form.save()
            return redirect('promo_code_list')
    else:
        form = PromoCodeForm(instance=promo_code)
    return render(request, 'home/promo_code_form.html', {'form': form})

@login_required(login_url="/login/")
def promo_code_delete(request, pk):
    promo_code = get_object_or_404(PromoCode, pk=pk)
    promo_code.delete()
    return redirect('promo_code_list')

