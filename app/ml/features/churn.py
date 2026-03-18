import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any

class ChurnFeature:
    """
    고객 이탈 예측 및 RFM 분석을 위한 피처 추출기
    """
    
    @staticmethod
    def calculate_rfm(point_df: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
        """
        포인트 로그를 기반으로 고객별 RFM 산출
        """
        if reference_date is None:
            reference_date = datetime.now(timezone.utc)
            
        # 1. 날짜 형식 변환
        point_df['visit_date'] = pd.to_datetime(point_df['visit_date'])
        
        # 2. 고객별 집계 (마지막 방문일, 방문 횟수, 총 결제 금액)
        rfm = point_df.groupby('customer_id').agg({
            'visit_date': lambda x: (reference_date - x.max()).days, # Recency
            'customer_id': 'count', # Frequency
            'payment_amount': 'sum' # Monetary
        }).rename(columns={
            'visit_date': 'recency',
            'customer_id': 'frequency',
            'payment_amount': 'monetary'
        }).reset_index()
        
        # 3. 고객별 평균 방문 주기 계산
        # 방문이 2회 이상인 고객만 주기 계산 가능
        intervals = point_df.sort_values(['customer_id', 'visit_date']).groupby('customer_id')['visit_date'].diff().dt.days
        avg_intervals = intervals.groupby(point_df['customer_id']).mean().reset_index()
        avg_intervals.columns = ['customer_id', 'avg_interval']
        
        rfm = pd.merge(rfm, avg_intervals, on='customer_id', how='left')
        
        # 주기를 알 수 없는 고객(1회 방문)은 전체 평균으로 채움
        rfm['avg_interval'] = rfm['avg_interval'].fillna(rfm['avg_interval'].mean() if not rfm['avg_interval'].isna().all() else 30)
        
        # 4. 이탈 확률(Churn Probability) 계산
        # 공식: 현재 안 온 기간(Recency) / (평소 주기 * 1.5) -> 1.0에 가까울수록 위험
        rfm['churn_probability'] = np.clip(rfm['recency'] / (rfm['avg_interval'] * 1.5), 0, 1)
        
        return rfm

    @staticmethod
    def segment_customers(rfm_df: pd.DataFrame) -> pd.DataFrame:
        """
        RFM 점수를 기반으로 고객 세그먼트 분류
        """
        def get_segment(row):
            if row['churn_probability'] > 0.8:
                return "At Risk"
            elif row['recency'] > 90:
                return "Lost"
            elif row['frequency'] >= 5 and row['monetary'] >= rfm_df['monetary'].median():
                return "VIP"
            elif row['frequency'] >= 2:
                return "Loyal"
            else:
                return "New"
        
        rfm_df['segment'] = rfm_df.apply(get_segment, axis=1)
        return rfm_df
