from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
import pymysql

def connect_db():
    connection = pymysql.connect(
        host='localhost',
        user='django_user',
        password='123456',
        database='smartloan_db',
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8'
    )
    return connection

# 登录页面视图
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 查询用户是否存在
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM custom_user WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            if password == user['password']:
                request.session['username'] = user['username']
                return redirect('dashboard')
            else:
                return HttpResponse("密码错误！")
        else:
            return HttpResponse("用户名不存在！")

    return render(request, 'users/login.html')

def loan_dashboard():
    try:
        connection = connect_db()
        print("Database connection successful")
        cursor = connection.cursor()

        # 总申请数
        cursor.execute("SELECT COUNT(*) FROM LoanApplication")
        res = cursor.fetchone()
        total_applications = res['COUNT(*)']
        print(f"Total Applications: {total_applications}")

        # 审批通过率
        cursor.execute("SELECT COUNT(*) FROM LoanApplication WHERE status='approved'")
        res = cursor.fetchone()
        approved_applications = res['COUNT(*)']
        approval_rate = round((approved_applications / total_applications) * 100, 2) if total_applications > 0 else 0
        print(f"Approved Applications: {approved_applications}, Approval Rate: {approval_rate}%")

        # 平均信用评分
        cursor.execute("SELECT AVG(credit_score) FROM CreditRating")
        res = cursor.fetchone()
        avg_credit_score = round(res['AVG(credit_score)'], 2) if res['AVG(credit_score)'] is not None else 0
        print(f"Average Credit Score: {avg_credit_score}")

        # 逾期率
        cursor.execute("SELECT COUNT(*) FROM LoanApplication WHERE overdue=1")
        res = cursor.fetchone()
        overdue_count = res['COUNT(*)']
        overdue_rate = round((overdue_count / total_applications) * 100, 2) if total_applications > 0 else 0
        print(f"Overdue Applications: {overdue_count}, Overdue Rate: {overdue_rate}%")

        # 信用评分分布
        cursor.execute("SELECT credit_score_range, COUNT(*) FROM CreditRating GROUP BY credit_score_range")
        score_distribution_raw = cursor.fetchall()
        score_distribution = [
            {'credit_score_range': row['credit_score_range'], 'count': row['COUNT(*)']}
            for row in score_distribution_raw
        ]
        print(f"Credit Score Distribution: {score_distribution}")

        # 贷款申请趋势（近30天）
        cursor.execute("""
            SELECT DATE_FORMAT(application_date, '%Y-%m-%d') AS formatted_date, COUNT(*) 
            FROM LoanApplication 
            GROUP BY formatted_date 
            ORDER BY formatted_date DESC 
            LIMIT 30
        """)
        application_trend_raw = cursor.fetchall()
        application_trend = [
            {'formatted_date': row['formatted_date'], 'count': row['COUNT(*)']}
            for row in application_trend_raw
        ]
        print(f"Application Trend: {application_trend}")

        # 风险评分分布
        cursor.execute("SELECT risk_score_range, COUNT(*) FROM CreditRating GROUP BY risk_score_range")
        risk_score_distribution_raw = cursor.fetchall()
        risk_score_distribution = [
            {'risk_score_range': row['risk_score_range'], 'count': row['COUNT(*)']}
            for row in risk_score_distribution_raw
        ]
        print(f"Risk Score Distribution: {risk_score_distribution}")

        # 审批状态分布
        cursor.execute("SELECT status, COUNT(*) FROM LoanApplication GROUP BY status")
        approval_status_raw = cursor.fetchall()
        approval_status_distribution = [
            {'status': row['status'], 'count': row['COUNT(*)']}
            for row in approval_status_raw
        ]
        print(f"Approval Status Distribution: {approval_status_distribution}")

        # 贷款申请信用评分趋势（按月统计）
        cursor.execute("""
            SELECT MONTH(application_date) AS month, AVG(CreditRating.credit_score) AS avg_score 
            FROM LoanApplication
            JOIN CreditRating ON LoanApplication.customer_id = CreditRating.customer_id
            GROUP BY month
            ORDER BY month ASC  -- 确保按月份升序排序
        """)
        score_trend_raw = cursor.fetchall()
        score_trend = [
            {'month': f"{row['month']}月", 'avg_score': round(row['avg_score'], 2) if row['avg_score'] is not None else 0}
            for row in score_trend_raw
        ]
        print(f"Credit Score Trend: {score_trend}")

        # 近期贷款申请（近5条记录）
        cursor.execute("""
            SELECT loan_id, customer_name, application_amount, CreditRating.credit_score, status, application_date 
            FROM LoanApplication
            JOIN Customer ON LoanApplication.customer_id = Customer.customer_id
            JOIN CreditRating ON LoanApplication.customer_id = CreditRating.customer_id
            ORDER BY application_date DESC LIMIT 5
        """)
        recent_loans_raw = cursor.fetchall()
        recent_loans = [
            {'loan_id': row['loan_id'], 'customer_name': row['customer_name'], 'application_amount': row['application_amount'],
             'credit_score': row['credit_score'], 'status': row['status'], 'application_date': row['application_date']}
            for row in recent_loans_raw
        ]
        print(f"Recent Loans: {recent_loans}")

    except Exception as e:
        print(f"Error occurred while fetching loan data: {e}")
        return {}

    finally:
        connection.close()

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
    username = request.session.get('username', '访客')  # 默认值是“访客”

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
    connection = connect_db()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT customer_id, customer_name, gender, birth_date,
                   occupation, email, phone_number, address, created_at
            FROM Customer
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

    # 重命名键为模板中需要的字段名
    customers = []
    for row in rows:
        customers.append({
            'id': row['customer_id'],
            'name': row['customer_name'],
            'gender': row['gender'],
            'birth_date': row['birth_date'],
            'occupation': row['occupation'],
            'email': row['email'],
            'phone': row['phone_number'],
            'address': row['address'],
            'created_at': row['created_at'],
        })

    return render(request, 'users/customer_list.html', {
        'customers': customers,
        'username': username
    })


# views.py
def customer_detail(request, customer_id):
    connection = connect_db()
    with connection.cursor() as cursor:
        cursor.execute("SELECT customer_name FROM Customer WHERE customer_id = %s", (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            return JsonResponse({'error': '客户不存在'}, status=404)

        cursor.execute("SELECT * FROM CreditRating WHERE customer_id = %s ORDER BY evaluation_date DESC LIMIT 1", (customer_id,))
        credit = cursor.fetchone() or {}

        cursor.execute("SELECT COUNT(*) as count FROM LoanApplication WHERE customer_id = %s", (customer_id,))
        loan_count = cursor.fetchone()['count']

        cursor.execute("""
            SELECT status FROM LoanStatus
            WHERE loan_id IN (SELECT loan_id FROM LoanApplication WHERE customer_id = %s)
            ORDER BY processing_date DESC LIMIT 1
        """, (customer_id,))
        status = cursor.fetchone()

    return JsonResponse({
        'customer_name': customer['customer_name'],
        'credit_score': credit.get('credit_score'),
        'credit_score_range': credit.get('credit_score_range'),
        'risk_score': credit.get('risk_score'),
        'risk_score_range': credit.get('risk_score_range'),
        'loan_count': loan_count,
        'latest_loan_status': status['status'] if status else None,
    })
