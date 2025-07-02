#!/usr/bin/env python
import os
import sys
import django
from django.db import connection

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartloan.settings')
django.setup()

def import_sql_file(filename):
    """读取并执行SQL文件"""
    with open(filename, 'r', encoding='utf-8') as file:
        sql_content = file.read()
    
    # 分割SQL语句（以分号分割）
    sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
    
    with connection.cursor() as cursor:
        for sql in sql_statements:
            if sql:
                try:
                    print(f"执行SQL: {sql[:50]}...")
                    cursor.execute(sql)
                    print("✓ 成功")
                except Exception as e:
                    print(f"✗ 错误: {e}")
                    print(f"SQL语句: {sql}")
    
    print("数据导入完成！")

if __name__ == '__main__':
    import_sql_file('database_setup.sql') 