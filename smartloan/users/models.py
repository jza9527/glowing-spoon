from django.db import models
from django.contrib.auth.models import User

# 客户信息表
class Customer(models.Model):
    GENDER_CHOICES = [
        ('男', '男'),
        ('女', '女'),
        ('其他', '其他'),
    ]
    
    customer_id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    birth_date = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Customer'

    def __str__(self):
        return self.customer_name

# 信用评级表
class CreditRating(models.Model):
    credit_rating_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    credit_score = models.IntegerField(null=True, blank=True)
    credit_score_range = models.CharField(max_length=50, null=True, blank=True)
    risk_score = models.IntegerField(null=True, blank=True)
    risk_score_range = models.CharField(max_length=50, null=True, blank=True)
    evaluation_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'CreditRating'

    def __str__(self):
        return f"{self.customer.customer_name} - {self.credit_score_range}"

# 贷款申请表
class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('approved', '已批准'),
        ('pending', '待审核'),
        ('processing', '处理中'),
        ('rejected', '已拒绝'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('等额本息', '等额本息'),
        ('等额本金', '等额本金'),
        ('按月付息到期还本', '按月付息到期还本'),
        ('一次性还本付息', '一次性还本付息'),
    ]

    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    application_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    application_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    loan_term = models.IntegerField(null=True, blank=True)  # 贷款期限（月）
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True)
    overdue = models.IntegerField(default=0)  # 0=正常, 1=逾期
    denied_reason = models.TextField(null=True, blank=True)
    loan_purpose = models.CharField(max_length=100, null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'LoanApplication'

    def __str__(self):
        return f"{self.customer.customer_name} - {self.application_amount}"

# 担保人表
class Guarantor(models.Model):
    guarantor_id = models.AutoField(primary_key=True)
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    guarantor_name = models.CharField(max_length=255, null=True, blank=True)
    guarantor_relationship = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'Guarantor'

    def __str__(self):
        return f"{self.guarantor_name} - {self.guarantor_relationship}"

# 贷款状态表
class LoanStatus(models.Model):
    STATUS_CHOICES = [
        ('approved', '已批准'),
        ('pending', '待审核'),
        ('processing', '处理中'),
        ('rejected', '已拒绝'),
    ]

    status_id = models.AutoField(primary_key=True)
    loan = models.ForeignKey(LoanApplication, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True)
    processing_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'LoanStatus'

    def __str__(self):
        return f"{self.loan.customer.customer_name} - {self.status}"

# 如果需要自定义用户表，可以使用这个
class CustomUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # 注意：在生产环境中应该使用哈希密码
    email = models.EmailField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'custom_user'

    def __str__(self):
        return self.username
