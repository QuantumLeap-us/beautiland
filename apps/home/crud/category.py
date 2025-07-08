from django.shortcuts import render, redirect
from apps.home.forms.categoryform import CategoryForm
from apps.home.model.product_category import Category
from django.contrib.auth.decorators import login_required
import sys
from django.utils.translation import gettext_lazy as _
from datetime import datetime
from apps.home.models import Product, Supplier
from django.db.models import Q


@login_required(login_url="/login/")
def categoryList(request):
    form = CategoryForm()
    category_data = get_category_data()

    return render(request, 'home/category.html', {"categories": category_data, 'form': form, "role": request.user.role})


def get_category_data():
    category_data = []
    categories = Category.objects.values("id", "name", "type", "parent_id", "parent__name", "parent__type", "created_date").order_by("-id")
    for category in categories:
        category_data.append({
            "id": category["id"],
            "name": category["name"],
            "type": category["type"],
            "parent_id": category["parent_id"],
            "parent__name": category["parent__name"],
            "parent__type": category["parent__type"],
            "created_date": datetime.strptime(str(category["created_date"]), "%Y-%m-%d %H:%M:%S.%f%z").strftime("%Y-%m-%d"),
        })
    
    return category_data


# @login_required(login_url="/login/")
# def categoryCreate(request):
#     form = CategoryForm(request.POST)
#     if form.is_valid():
#         parent_id = request.POST.get('parent_id')
#         if parent_id != '':
#             parent_category = Category.objects.get(pk=parent_id)
#             new_category = form.save(commit=False)
#             new_category.parent = parent_category
#             new_category.save()
#         else:
#             form.save()
#         msg = _("category added successfully")

#     else:
#         msg = _('Form is not valid')

#     categories = Category.objects.all()
#     form = CategoryForm()
#     return render(request, 'home/category.html', {'categories': categories, "msg": msg, 'form': form})


@login_required(login_url="/login/")
def categoryCreate(request):
    category_data = get_category_data()
    cat_form = CategoryForm()
    try:
        if request.method == "POST":
            name = request.POST.get('name')
            cat_type = request.POST.get('type')
            parent_id = request.POST.get('parent_id') if request.POST.get('parent_id') else None
            check_cat_exist = ""
            if parent_id:
                check_cat_exist = Category.objects.filter(name=name, type=cat_type, parent_id=parent_id).first()
            else:
                check_cat_exist = Category.objects.filter(name=name, type=cat_type).first()
            if check_cat_exist:
                return render(request, 'home/category.html', {'categories': category_data, "error_msg": "Category already exist.", 'form': cat_form})

            Category.objects.create(name=name, type=cat_type, parent_id=parent_id)
            return redirect("category")
        else:
            return render(request, 'home/category.html', {'categories': category_data, 'form': cat_form})
    except Exception as e:
        print("error---", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("Error on line:", exc_tb.tb_lineno)
        return render(request, 'home/category.html', {'categories': category_data, 'form': cat_form, "error_msg": str(e)})
    

# def categoryUpdate(request, id):
#     category = Category.objects.get(id=id)
#     form = CategoryForm(initial={'name': category.name, 'label': category.name, 'parent':category.parent})
#     msg=''
#     if request.method == "POST":
#         form = CategoryForm(request.POST, instance=category)
#         if form.is_valid():
#             try:
#                 form.save()
#                 model = form.instance
#                 msg = "category updated successfully"
#             except Exception as e:
#                 pass
#     categories = Category.objects.all()
#     return render(request, 'home/category.html',{'categories':categories,"msg":msg, 'form':form})


@login_required(login_url="/login/")
def categoryDelete(request, id):
    category_data = get_category_data()
    form = CategoryForm()
    try:
        if id:
            validate_msg = get_existed_category_validate_msg(id)
            if validate_msg:
                return render(request, "home/category.html", {"id": id, 'categories': category_data, "error_msg": ", ".join(validate_msg), 'form': form})  
            Category.objects.filter(id=id).delete()
            return redirect("category")
        else:
            return render(request, 'home/category.html', {'categories': category_data, "error_msg": "Category not found.", 'form': form})
    except Exception as e:
        print("error---", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print("Error on line:", exc_tb.tb_lineno)
        return render(request, 'home/category.html', {'categories': category_data, 'form': form, "error_msg": str(e)})
    

def get_existed_category_validate_msg(id):
    validate_msg = []
    existed_category_in_products = {}
    query = Q()
    query.add(Q(category_id=id) | Q(sub_category_id=id), query.connector)
    in_use_category_products = Product.objects.filter(query).values("id", "product_id", "category_id", "category__name", "sub_category_id", "sub_category__name")
    for product in in_use_category_products:
        cat_name_field = ""
        if product["category_id"] == id:
            cat_name_field = "category__name"
        if product["sub_category_id"] == id:
            cat_name_field = "sub_category__name"
        if cat_name_field:
            if product[cat_name_field] not in existed_category_in_products:
                existed_category_in_products[product[cat_name_field]] = [product["product_id"]]
            else:
                existed_category_in_products[product[cat_name_field]].append(product["product_id"])
    
    for key, value in existed_category_in_products.items():
        msg = "Can't remove Category `<b>" + key + "</b>`. It is assigned in the product `<b>" + ", ".join(value) + "</b>`"
        if len(value) > 1:
            msg = "Can't remove Category `<b>" + key + "</b>`. It is assigned in the products `<b>" + ", ".join(value) + "</b>`"
        validate_msg.append(msg)

    # cat_query = Q()
    # cat_query.add(Q(id=id) | Q(parent_id=id), cat_query.connector)
    # category_data = Category.objects.filter(cat_query).values("id", "name", "parent_id", "parent__name", "type")
    # cat_li = []
    # for category in category_data:
    #     if category["name"] not in cat_li:
    #         cat_li.append(category["name"])
    #     if category["parent__name"] not in cat_li:
    #         cat_li.append(category["parent__name"])
    
    # supplier_query = Q()
    # supplier_query.add(Q(supplier_type__in=cat_li) | Q(product_type__in=cat_li), supplier_query.connector)
    # Supplier.objects.filter(supplier_query).values("supplier_id", "")

    # in_use_prefix_customers = Customer.objects.filter(prefix__in=check_prefix).values("prefix", "customer_id")
    # for customer in in_use_prefix_customers:
    #     if customer["prefix"] not in existed_prefix_in_customers:
    #         existed_prefix_in_customers[customer["prefix"]] = [customer["customer_id"]]
    #     else:
    #         existed_prefix_in_customers[customer["prefix"]].append(customer["customer_id"])

    # for key, value in existed_prefix_in_customers.items():
    #     prefix = ""
    #     if validate_msg:
    #         prefix = "<br>"
    #     msg = prefix + "Can't remove Prefix `<b>" + key + "</b>`. It is assigned in the customer `<b>" + ", ".join(value) + "</b>`"
    #     if len(value) > 1:
    #         msg = prefix + "Can't remove Prefix `<b>" + key + "</b>`. It is assigned in the customers `<b>" + ", ".join(value) + "</b>`"
    #     validate_msg.append(msg)

    return validate_msg