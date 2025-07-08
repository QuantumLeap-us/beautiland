from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.home.models import Commons  # 假設 Commons 是一個抽象基類

class DiscountScheme(Commons):
    name = models.CharField(max_length=128, verbose_name=_('方案名稱'))
    type = models.CharField(max_length=50, choices=[
        ('滿減', '滿減'),
        ('折扣', '折扣'),
        ('贈品', '贈品'),
    ], verbose_name=_('類型'))
    condition_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('條件金額'))
    start_date = models.DateField(verbose_name=_('開始日期'))
    end_date = models.DateField(verbose_name=_('結束日期'))
    usage_limit = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('使用次數限制'))
    status = models.CharField(max_length=20, choices=[
        ('啟用', '啟用'),
        ('停用', '停用'),
    ], default='啟用', verbose_name=_('狀態'))

    class Meta:
        db_table = 'discount_scheme'
        verbose_name = _('優惠方案')
        verbose_name_plural = _('優惠方案')

    def __str__(self):
        return self.name

class Coupon(Commons):
    code = models.CharField(max_length=50, unique=True, verbose_name=_('優惠券代碼'))
    type = models.CharField(max_length=50, choices=[
        ('滿減券', '滿減券'),
        ('折扣券', '折扣券'),
        ('兌換券', '兌換券'),
    ], verbose_name=_('類型'))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('折扣值'))
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('最低消費額'))
    start_date = models.DateField(verbose_name=_('開始日期'))
    end_date = models.DateField(verbose_name=_('結束日期'))
    usage_limit = models.PositiveIntegerField(verbose_name=_('使用次數限制'))
    used_count = models.PositiveIntegerField(default=0, verbose_name=_('已使用次數'))

    class Meta:
        db_table = 'coupon'
        verbose_name = _('優惠券')
        verbose_name_plural = _('優惠券')

    def __str__(self):
        return self.code

class Promotion(Commons):
    name = models.CharField(max_length=128, verbose_name=_('活動名稱'))
    type = models.CharField(max_length=50, choices=[
        ('限時折扣', '限時折扣'),
        ('買一送一', '買一送一'),
        ('組合套餐', '組合套餐'),
    ], verbose_name=_('類型'))
    start_date = models.DateTimeField(verbose_name=_('開始時間'))
    end_date = models.DateTimeField(verbose_name=_('結束時間'))
    description = models.TextField(verbose_name=_('活動描述'))

    class Meta:
        db_table = 'promotion'
        verbose_name = _('促銷活動')
        verbose_name_plural = _('促銷活動')

    def __str__(self):
        return self.name

class PromoCode(Commons):
    code = models.CharField(max_length=50, unique=True, verbose_name=_('促銷碼'))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('折扣值'))
    start_date = models.DateField(verbose_name=_('開始日期'))
    end_date = models.DateField(verbose_name=_('結束日期'))
    usage_limit = models.PositiveIntegerField(verbose_name=_('使用次數限制'))
    used_count = models.PositiveIntegerField(default=0, verbose_name=_('已使用次數'))

    class Meta:
        db_table = 'promo_code'
        verbose_name = _('促銷碼')
        verbose_name_plural = _('促銷碼')

    def __str__(self):
        return self.code