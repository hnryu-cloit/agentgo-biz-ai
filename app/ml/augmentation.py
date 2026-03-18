import random
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

class SyntheticGenerator:
    @staticmethod
    def generate_sales_data(store_key: str = 'cj-demo', days: int = 7) -> List[Dict]:
        data = []
        now = datetime.now(timezone.utc)
        menus = ['소룡포', '탄탄면', '어긋난짜장', '우육면', '칠리새우', '유린기', '볶음밥']
        for d in range(days):
            current_date = (now - timedelta(days=d)).date()
            for h in range(11, 22):
                weight = 2.5 if h in [12, 13, 18, 19] else 1.0
                orders_count = int(random.randint(5, 15) * weight)
                for _ in range(orders_count):
                    menu = random.choice(menus)
                    qty = random.randint(1, 2)
                    price = random.randint(12000, 45000)
                    data.append({
                        'store_key': store_key,
                        'store_name': '크리스탈제이드 광화문점',
                        'sales_date': current_date.isoformat(),
                        'hour': h,
                        'menu_name': menu,
                        'qty': qty,
                        'revenue': price * qty,
                        'sales_price': price,
                        'cost_price': price * 0.3 # 가상 원가
                    })
        return data

    @staticmethod
    def generate_point_data(store_key: str = 'cj-demo', count: int = 100) -> List[Dict]:
        data = []
        now = datetime.now(timezone.utc)
        for i in range(count):
            cust_id = f'CUST-{random.randint(1000, 1500)}'
            data.append({
                'customer_id': cust_id,
                'store_key': store_key,
                'visit_date': (now - timedelta(days=random.randint(0, 30))).isoformat(),
                'payment_amount': random.randint(30000, 150000),
                'point_type': random.choice(['적립', '적립', '적립', '사용'])
            })
        return data

    @staticmethod
    def generate_receipt_data(store_key: str = 'cj-demo', count: int = 100) -> List[Dict]:
        data = []
        now = datetime.now(timezone.utc)
        for i in range(count):
            status = 'cancelled' if random.random() < 0.05 else 'completed'
            data.append({
                'receipt_no': f'R-{random.randint(10000, 99999)}',
                'store_key': store_key,
                'sales_date': (now - timedelta(days=random.randint(0, 7))).date().isoformat(),
                'sales_time': f'{random.randint(11, 21):02d}:{random.randint(0, 59):02d}',
                'total_amount': random.randint(20000, 200000),
                'status': status
            })
        return data
