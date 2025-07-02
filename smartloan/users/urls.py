from django.urls import path
from . import views
from .views import login_view, dashboard_view, customer_list,customer_detail

urlpatterns = [
    path('', views.login_view),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('customers/', customer_list, name='customer_list'),
    path('customer_detail/<int:customer_id>/', customer_detail, name='customer_detail'),
]
