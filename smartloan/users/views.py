from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import Avg, Count
from django.db.models.functions import Extract
from .models import Customer, CreditRating, LoanApplication, Guarantor, LoanStatus, CustomUser
import datetime

# 登录页面视图
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # 查询用户是否存在
            user = CustomUser.objects.get(username=username)
            if password == user.password:
                request.session['username'] = user.username
                return redirect('dashboard')
            else:
                return HttpResponse("密码错误！")
        except CustomUser.DoesNotExist:
            return HttpResponse("用户名不存在！")

    return render(request, 'users/login.html')

def loan_dashboard():
    try:
        # 总申请数
        total_applications = LoanApplication.objects.count()
        print(f"Total Applications: {total_applications}")

        # 审批通过率
        approved_applications = LoanApplication.objects.filter(status='approved').count()
        approval_rate = round((approved_applications / total_applications) * 100, 2) if total_applications > 0 else 0
        print(f"Approved Applications: {approved_applications}, Approval Rate: {approval_rate}%")

        # 平均信用评分
        avg_credit_score_result = CreditRating.objects.aggregate(avg_score=Avg('credit_score'))
        avg_credit_score = round(avg_credit_score_result['avg_score'], 2) if avg_credit_score_result['avg_score'] is not None else 0
        print(f"Average Credit Score: {avg_credit_score}")

        # 逾期率
        overdue_count = LoanApplication.objects.filter(overdue=1).count()
        overdue_rate = round((overdue_count / total_applications) * 100, 2) if total_applications > 0 else 0
        print(f"Overdue Applications: {overdue_count}, Overdue Rate: {overdue_rate}%")

        # 信用评分分布
        score_distribution_raw = CreditRating.objects.values('credit_score_range').annotate(count=Count('credit_score_range'))
        score_distribution = [
            {'credit_score_range': item['credit_score_range'], 'count': item['count']}
            for item in score_distribution_raw
        ]
        print(f"Credit Score Distribution: {score_distribution}")

        # 贷款申请趋势（近30天）
        # SQLite 不支持 DATE_FORMAT，所以我们使用 Python 来格式化日期
        application_trend_raw = (LoanApplication.objects
                               .filter(application_date__isnull=False)
                               .values('application_date')
                               .annotate(count=Count('application_date'))
                               .order_by('-application_date')[:30])
        
        application_trend = [
            {'formatted_date': str(item['application_date']), 'count': item['count']}
            for item in application_trend_raw
        ]
        print(f"Application Trend: {application_trend}")

        # 风险评分分布
        risk_score_distribution_raw = CreditRating.objects.values('risk_score_range').annotate(count=Count('risk_score_range'))
        risk_score_distribution = [
            {'risk_score_range': item['risk_score_range'], 'count': item['count']}
            for item in risk_score_distribution_raw
        ]
        print(f"Risk Score Distribution: {risk_score_distribution}")

        # 审批状态分布
        approval_status_raw = LoanApplication.objects.values('status').annotate(count=Count('status'))
        approval_status_distribution = [
            {'status': item['status'], 'count': item['count']}
            for item in approval_status_raw
        ]
        print(f"Approval Status Distribution: {approval_status_distribution}")

        # 贷款申请信用评分趋势（按月统计）
        # 使用 Django ORM 的 Extract 来提取月份
        score_trend_raw = (LoanApplication.objects
                          .filter(application_date__isnull=False)
                          .annotate(month=Extract('application_date', 'month'))
                          .values('month')
                          .annotate(avg_score=Avg('customer__creditrating__credit_score'))
                          .order_by('month'))
        
        score_trend = [
            {'month': f"{item['month']}月", 'avg_score': round(item['avg_score'], 2) if item['avg_score'] is not None else 0}
            for item in score_trend_raw
        ]
        print(f"Credit Score Trend: {score_trend}")

        # 近期贷款申请（近5条记录）
        recent_loans_raw = (LoanApplication.objects
                           .select_related('customer')
                           .prefetch_related('customer__creditrating_set')
                           .order_by('-application_date')[:5])
        
        recent_loans = []
        for loan in recent_loans_raw:
            credit_rating = loan.customer.creditrating_set.first()
            recent_loans.append({
                'loan_id': loan.loan_id,
                'customer_name': loan.customer.customer_name,
                'application_amount': loan.application_amount,
                'credit_score': credit_rating.credit_score if credit_rating else None,
                'status': loan.status,
                'application_date': loan.application_date
            })
        print(f"Recent Loans: {recent_loans}")

    except Exception as e:
        print(f"Error occurred while fetching loan data: {e}")
        return {}

    return {
        'total_applications': total_applications,
        'approval_rate': approval_rate,
        'avg_credit_score': avg_credit_score,
        'overdue_rate': overdue_rate,
        'score_distribution': score_distribution,
        'application_trend': application_trend,
        'risk_score_distribution': risk_score_distribution,
        'approval_status_distribution': approval_status_distribution,
        'score_trend': score_trend,
        'recent_loans': recent_loans,
    }


def dashboard_view(request):
    username = request.session.get('username', '访客')  # 默认值是"访客"

    # 调用 loan_dashboard 获取数据
    data = loan_dashboard()

    # 如果数据成功获取，则渲染页面
    if data:
        return render(request, 'users/dashboard.html', {
            'username': username,
            **data  # 将 data 字典解包并传递给模板
        })
    else:
        # 如果获取数据失败，则返回错误信息
        return HttpResponse("数据库查询失败")

def customer_list(request):
    username = request.session.get('username', '访客')
    
    # 使用 Django ORM 查询客户列表
    customers_raw = Customer.objects.all().order_by('-created_at')
    
    # 转换为模板需要的格式
    customers = []
    for customer in customers_raw:
        customers.append({
            'id': customer.customer_id,
            'name': customer.customer_name,
            'gender': customer.gender,
            'birth_date': customer.birth_date,
            'occupation': customer.occupation,
            'email': customer.email,
            'phone': customer.phone_number,
            'address': customer.address,
            'created_at': customer.created_at,
        })

    return render(request, 'users/customer_list.html', {
        'customers': customers,
        'username': username
    })


def customer_detail(request, customer_id):
    try:
        # 获取客户信息
        customer = Customer.objects.get(customer_id=customer_id)
        
        # 获取最新的信用评级
        credit = customer.creditrating_set.order_by('-evaluation_date').first()
        
        # 获取贷款申请数量
        loan_count = LoanApplication.objects.filter(customer=customer).count()
        
        # 获取最新的贷款状态
        latest_loan_status = None
        latest_loan = LoanApplication.objects.filter(customer=customer).order_by('-application_date').first()
        if latest_loan:
            latest_status = LoanStatus.objects.filter(loan=latest_loan).order_by('-processing_date').first()
            if latest_status:
                latest_loan_status = latest_status.status

        return JsonResponse({
            'customer_name': customer.customer_name,
            'credit_score': credit.credit_score if credit else None,
            'credit_score_range': credit.credit_score_range if credit else None,
            'risk_score': credit.risk_score if credit else None,
            'risk_score_range': credit.risk_score_range if credit else None,
            'loan_count': loan_count,
            'latest_loan_status': latest_loan_status,
        })
        
    except Customer.DoesNotExist:
        return JsonResponse({'error': '客户不存在'}, status=404)
