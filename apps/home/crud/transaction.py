import logging
from django.urls import reverse

from django.db import transaction as db_transaction
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
import django.utils.timezone
from apps.home.model.transaction import Transaction
from apps.home.models import Order
from apps.home.forms.transactionform import TransactionForm
from apps.authentication.models import Permissions
import pandas as pd
from datetime import datetime, timedelta
import pytz

def create_transaction(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        print(f"order_id:{order_id}")
        order = Order.objects.filter(id=order_id, is_deleted=False).first()
        if not order:
            return {"code": 0, "msg": _("Order does not exist")}  # 返回字典
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    transaction_instance = form.save(commit=False)
                    transaction_instance.order = order
                    transaction_instance.created_by = request.user
                    transaction_instance.status = Transaction.TransactionStatus.AWAITING_APPROVAL
                    if not transaction_instance.transaction_date:
                        transaction_instance.transaction_date = django.utils.timezone.now()
                    transaction_instance.save()
                    if transaction_instance.transaction_type == Transaction.TransactionType.PAYMENT and transaction_instance.status == Transaction.TransactionStatus.APPROVED:
                        order.payment_status = "Paid"
                        order.save()
                    return {"code": 1, "msg": _("Transaction created successfully, awaiting approval")}  # 返回字典
            except Exception as e:
                from . import manager
                import traceback
                manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
                return {"code": 0, "msg": str(e)}  # 返回字典
        else:
            return {"code": 0, "msg": _("Form validation failed")}  # 返回字典
    else:
        form = TransactionForm()
        orders = Order.objects.filter(is_deleted=False).select_related('customer')
        return {
            "form": form,
            "orders": orders,
            "role": request.user.role,
            "is_create": True
        }  # 返回字典


def transaction_create_with_redirect(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        print(f"order_id:{order_id}")
        order = Order.objects.filter(id=order_id, is_deleted=False).first()
        if not order:
            # 重定向到订单编辑页面并附带错误信息
            redirect_url = reverse('order-get', kwargs={'id': order_id}) if order_id else reverse('order-list')
            redirect_url += '?success=0&msg=' + _("Order does not exist")
            return HttpResponseRedirect(redirect_url)

        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    transaction_instance = form.save(commit=False)
                    transaction_instance.order = order
                    transaction_instance.created_by = request.user
                    transaction_instance.status = Transaction.TransactionStatus.AWAITING_APPROVAL
                    if not transaction_instance.transaction_date:
                        transaction_instance.transaction_date = django.utils.timezone.now()
                    transaction_instance.save()
                    if transaction_instance.transaction_type == Transaction.TransactionType.PAYMENT and transaction_instance.status == Transaction.TransactionStatus.APPROVED:
                        order.payment_status = "Paid"
                        order.save()
                    # 重定向到订单编辑页面，附带成功信息
                    redirect_url = reverse('order-get', kwargs={'id': order_id})
                    redirect_url += '?success=1&msg=' + _("Transaction created successfully, awaiting approval")
                    return HttpResponseRedirect(redirect_url)
            except Exception as e:
                from . import manager
                import traceback
                manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
                redirect_url = reverse('order-get', kwargs={'id': order_id}) if order_id else reverse('order-list')
                redirect_url += '?success=0&msg=' + str(e)
                return HttpResponseRedirect(redirect_url)
        else:
            redirect_url = reverse('order-get', kwargs={'id': order_id}) if order_id else reverse('order-list')
            redirect_url += '?success=0&msg=' + _("Form validation failed")
            return HttpResponseRedirect(redirect_url)
    else:
        # 非 POST 请求，重定向到订单列表
        return HttpResponseRedirect(reverse('order-list'))

def update_transaction(request, transaction_id):
    transaction_instance = Transaction.objects.filter(id=transaction_id, is_deleted=False).first()
    if not transaction_instance:
        return {"code": 0, "msg": _("Transaction does not exist")}

    if transaction_instance.status == Transaction.TransactionStatus.AWAITING_APPROVAL:
        return {"code": 0, "msg": _("Cannot update transaction in Awaiting Approval status")}

    if request.method == "POST":
        form = TransactionForm(request.POST, request.FILES, instance=transaction_instance)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    form.save()
                    return {"code": 1, "msg": _("Transaction updated successfully")}
            except Exception as e:
                from . import manager
                import traceback
                manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
                return {"code": 0, "msg": str(e)}
        else:
            return {"code": 0, "msg": _("Form validation failed")}
    else:
        form = TransactionForm(instance=transaction_instance)

    return {
        "form": form,
        "transaction": transaction_instance,
        "role": request.user.role,
        "is_create": False
    }


def approve_transaction(request, transaction_id):
    transaction_instance = Transaction.objects.filter(id=transaction_id, is_deleted=False).first()
    logging.info(f"当前状态{transaction_instance}")
    if not transaction_instance:
        return JsonResponse({"code": 0, "msg": _("Transaction does not exist")})

    if transaction_instance.status != Transaction.TransactionStatus.AWAITING_APPROVAL:
        return JsonResponse({"code": 0, "msg": _("Transaction is not in Awaiting Approval status")})

    try:
        with db_transaction.atomic():
            transaction_instance.status = Transaction.TransactionStatus.APPROVED
            transaction_instance.save()
            if transaction_instance.transaction_type == Transaction.TransactionType.PAYMENT:
                transaction_instance.order.payment_status = "Paid"
                transaction_instance.order.save()
            return JsonResponse({"code": 1, "msg": _("Transaction approved successfully")})
    except Exception as e:
        from . import manager
        import traceback
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return JsonResponse({"code": 0, "msg": str(e)})


def list_transactions(request):
    permission = Permissions.objects.filter(role=request.user.role, permission="can_export_transaction").values(
        "is_permission").first()
    can_export = permission["is_permission"] if permission else False

    transactions = Transaction.objects.filter(is_deleted=False).select_related('order', 'created_by')
    if request.user.role == "sales_person":
        transactions = transactions.filter(created_by=request.user)

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    customer_id = request.GET.get('customer_id')
    payment_status = request.GET.get('payment_status')
    invoice_id = request.GET.get('invoice_id')
    daterange = ""

    if from_date and to_date:
        try:
            # 解析日期
            from_date_dt = datetime.strptime(from_date, '%m/%d/%Y')
            to_date_dt = datetime.strptime(to_date, '%m/%d/%Y')
            # 将 to_date 设置为当天结束时间
            to_date_dt = to_date_dt + timedelta(days=1) - timedelta(microseconds=1)  # 23:59:59.999999

            # 假设输入是 HKT 时间，将其转换为 UTC（数据库存储的是 UTC 时间）
            hkt_tz = pytz.timezone('Asia/Hong_Kong')
            utc_tz = pytz.UTC
            from_date_hkt = hkt_tz.localize(from_date_dt)
            to_date_hkt = hkt_tz.localize(to_date_dt)
            from_date_utc = from_date_hkt.astimezone(utc_tz)
            to_date_utc = to_date_hkt.astimezone(utc_tz)

            print(f"Input range (HKT): {from_date_hkt} to {to_date_hkt}")
            print(f"Filtered range (UTC): {from_date_utc} to {to_date_utc}")
            transactions = transactions.filter(transaction_date__range=[from_date_utc, to_date_utc])
            daterange = f"{from_date} - {to_date}"
            print(f"Transactions count after date filter: {transactions.count()}")
            # 调试：打印第一条记录的 transaction_date
            if transactions.exists():
                print(f"First transaction date: {transactions.first().transaction_date}")
            else:
                print("No transactions found in this range.")
        except ValueError as e:
            print(f"Date parsing error: {e}")
            return {"code": 0, "msg": _("Invalid date format"), "transactions": [], "can_export": can_export,
                    "daterange": ""}

    if customer_id:
        transactions = transactions.filter(customer_id=customer_id)


    if payment_status:
        transactions = transactions.filter(payment_status=payment_status)

    # 添加 invoice_id 过滤逻辑
    if invoice_id:
        transactions = transactions.filter(order__order_id=invoice_id)

    if request.GET.get('export'):
        data = []
        for t in transactions:
            data.append({
                "Transaction ID": t.transaction_id,
                "Order ID": t.order.order_id,
                "Customer ID": t.customer_id or "-",
                "Customer Name": t.customer_name or "-",
                "Sales Person": t.sales_person or "-",
                "Type": t.get_transaction_type_display(),
                "Amount": t.amount,
                "Currency": t.currency,
                "Payment Method": t.payment_method or "-",
                "Payment Status": t.get_payment_status_display(),
                "Status": t.get_status_display(),
                "Upload Date": t.upload_date.strftime("%Y-%m-%d %H:%M:%S") if t.upload_date else "-",
                "Refund Amount": t.refund_amount,
                "Refund Date": t.refund_date.strftime("%Y-%m-%d %H:%M:%S") if t.refund_date else "-",
                "Net Amount": t.net_amount,
                "Delivery Date": t.delivery_date.strftime("%Y-%m-%d %H:%M:%S") if t.delivery_date else "-",
                "Transaction Date": t.transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
                "Updated At": t.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Created By": t.created_by.username if t.created_by else "-",
                "Remarks": t.remarks or "-",
                "Attachment": t.attachment.url if t.attachment else "-",
            })
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response[
            'Content-Disposition'] = f'attachment; filename="transactions_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        df.to_excel(response, index=False)
        return response

    return {
        "transactions": transactions.order_by('-transaction_date'),
        "role": request.user.role,
        "can_export": can_export,
        "daterange": daterange,
        "payment_status_choices": Transaction.PaymentStatus.choices,
    }


def delete_transaction(request, transaction_id):
    transaction_instance = Transaction.objects.filter(id=transaction_id, is_deleted=False).first()
    if not transaction_instance:
        return {"code": 0, "msg": _("Transaction does not exist")}

    if request.user.role == "seller":
        return {"code": 0, "msg": _("You do not have permission to delete transactions")}

    if transaction_instance.status in [Transaction.TransactionStatus.COMPLETED, Transaction.TransactionStatus.APPROVED]:
        return {"code": 0, "msg": _("Cannot delete completed or approved transactions")}

    try:
        with db_transaction.atomic():
            transaction_instance.is_deleted = True
            transaction_instance.save()
            return {"code": 1, "msg": _("Transaction deleted successfully")}
    except Exception as e:
        from . import manager
        import traceback
        manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
        return {"code": 0, "msg": str(e)}


def import_transactions(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        try:
            df = pd.read_excel(file)
            with db_transaction.atomic():
                for _, row in df.iterrows():
                    order = Order.objects.filter(order_id=row['Order ID']).first()
                    if not order:
                        return JsonResponse({"code": 0, "msg": f"Order {row['Order ID']} not found"})
                    Transaction.objects.create(
                        order=order,
                        transaction_type=row['Type'],
                        amount=row['Amount'],
                        currency=row.get('Currency', 'HKD'),
                        payment_method=row.get('Payment Method', None),
                        status=Transaction.TransactionStatus.AWAITING_APPROVAL,
                        payment_status=row.get('Payment Status', 'Unpaid'),
                        customer_id=row.get('Customer ID', None),
                        customer_name=row.get('Customer Name', None),
                        sales_person=row.get('Sales Person', None),
                        refund_amount=row.get('Refund Amount', 0),
                        refund_date=row.get('Refund Date', None),
                        delivery_date=row.get('Delivery Date', None),
                        remarks=row.get('Remarks', None),
                        created_by=request.user
                    )
            return JsonResponse({"code": 1, "msg": "Transactions imported successfully, awaiting approval"})
        except Exception as e:
            return JsonResponse({"code": 0, "msg": str(e)})
    return JsonResponse({"code": 0, "msg": "Invalid request"})


def create_dynamic_transaction(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        order = Order.objects.filter(id=order_id, is_deleted=False).first()
        if not order:
            return JsonResponse({"code": 0, "msg": _("Order does not exist")})

        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    transaction_instance = form.save(commit=False)
                    transaction_instance.order = order
                    transaction_instance.created_by = request.user
                    transaction_instance.status = Transaction.TransactionStatus.AWAITING_APPROVAL
                    if not transaction_instance.transaction_date:
                        transaction_instance.transaction_date = django.utils.timezone.now()
                    transaction_instance.save()

                    # 如果是支付类型交易且状态为已批准，更新订单支付状态
                    if (transaction_instance.transaction_type == Transaction.TransactionType.PAYMENT and
                            transaction_instance.status == Transaction.TransactionStatus.APPROVED):
                        order.payment_status = "Paid"
                        order.save()

                    return JsonResponse({"code": 1, "msg": _("Transaction created successfully, awaiting approval"),
                                         "payment_date": transaction_instance.transaction_date.strftime(
                                             "%Y-%m-%d %H:%M:%S") if transaction_instance.transaction_date else "",
                                         "attachment": transaction_instance.attachment.name if transaction_instance.attachment else ""})
            except Exception as e:
                from . import manager
                import traceback
                manager.create_from_exceptions(request.user.id, e, traceback.format_exc())
                return JsonResponse({"code": 0, "msg": str(e)})
        else:
            return JsonResponse({"code": 0, "msg": _("Form validation failed"), "errors": form.errors})
    return JsonResponse({"code": 0, "msg": _("Invalid request method")})