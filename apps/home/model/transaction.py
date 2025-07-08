from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.authentication.models import User
from apps.home.models import Order, Orderitems
import django.utils.timezone

class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        PAYMENT = 'Payment', _('Payment')
        REFUND = 'Refund', _('Refund')
        ADJUSTMENT = 'Adjustment', _('Adjustment')
        DISCOUNT = 'Discount', _('Discount')

    class TransactionStatus(models.TextChoices):
        PENDING = 'Pending', _('Pending')
        AWAITING_APPROVAL = 'Awaiting Approval', _('Awaiting Approval')
        APPROVED = 'Approved', _('Approved')
        COMPLETED = 'Completed', _('Completed')
        FAILED = 'Failed', _('Failed')
        CANCELLED = 'Cancelled', _('Cancelled')

    class PaymentStatus(models.TextChoices):
        UNPAID = 'Unpaid', _('Unpaid')
        PARTIAL = 'Partial', _('Partial')
        PAID = 'Paid', _('Paid')

    transaction_id = models.CharField(max_length=50, unique=True, verbose_name=_("Transaction ID"))
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("Order"))
    order_item = models.ForeignKey(Orderitems, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='transactions', verbose_name=_("Order Item"))
    transaction_type = models.CharField(max_length=50, choices=TransactionType.choices,
                                        verbose_name=_("Transaction Type"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Amount"))
    currency = models.CharField(max_length=10, default='HKD', verbose_name=_("Currency"))
    payment_method = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("Payment Method"))
    status = models.CharField(max_length=50, choices=TransactionStatus.choices, default=TransactionStatus.PENDING,
                              verbose_name=_("Status"))
    payment_status = models.CharField(max_length=50, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID,
                                      verbose_name=_("Payment Status"))
    customer_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_("Customer ID"))
    customer_name = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Customer Name"))
    sales_person = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Sales Person"))
    upload_date = models.DateTimeField(default=django.utils.timezone.now, verbose_name=_("Upload Date"))
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Refund Amount"))
    refund_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Refund Date"))
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Net Amount"))
    delivery_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Delivery Date"))
    transaction_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Transaction Date"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    remarks = models.TextField(null=True, blank=True, verbose_name=_("Remarks"))
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Created By"))
    is_deleted = models.BooleanField(default=False, verbose_name=_("Is Deleted"))
    attachment = models.FileField(upload_to='transaction_attachments/', null=True, blank=True, verbose_name=_("Attachment"))

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['order_id']),
        ]

    def __str__(self):
        return f"{self.transaction_id} - {self.transaction_type} ({self.amount} {self.currency})"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            last_transaction = Transaction.objects.order_by('-id').first()
            next_num = 1
            if last_transaction:
                last_num = int(last_transaction.transaction_id[-2:])
                next_num = last_num + 1
            self.transaction_id = f"TX{self.transaction_date.strftime('%Y%m%d')}{next_num:02d}"

        if self.order and hasattr(self.order, 'customer') and self.order.customer:
            self.customer_id = self.order.customer.customer_id
            self.customer_name = self.order.customer.name

        if self.order and hasattr(self.order, 'sales_person') and self.order.sales_person:
            self.sales_person = self.order.sales_person

        self.net_amount = self.amount - self.refund_amount

        super().save(*args, **kwargs)