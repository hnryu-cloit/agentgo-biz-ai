import pandas as pd
import numpy as np
from typing import List, Dict, Any

class AnomalyFeature:
    """
    운영 리스크 및 이상 결제 탐지를 위한 피처 추출기
    """
    
    @staticmethod
    def detect_cancellation_anomalies(receipt_df: pd.DataFrame) -> pd.DataFrame:
        """
        영수증 데이터를 기반으로 비정상 취소 패턴 탐지
        """
        # 1. 일별/시간대별 취소율 계산
        receipt_df['sales_date'] = pd.to_datetime(receipt_df['sales_date'])
        receipt_df['hour'] = receipt_df['sales_time'].str.split(':').str[0].astype(int)
        
        # 전체 건수 대비 취소 건수 (status='cancelled' 가정)
        daily_stats = receipt_df.groupby(['sales_date', 'hour']).agg({
            'receipt_no': 'count',
            'status': lambda x: (x == 'cancelled').sum()
        }).rename(columns={'receipt_no': 'total_count', 'status': 'cancel_count'})
        
        daily_stats['cancel_rate'] = daily_stats['cancel_count'] / daily_stats['total_count']
        
        # 2. Z-score 기반 이상치 계산 (평균에서 얼마나 벗어났는가)
        mean_rate = daily_stats['cancel_rate'].mean()
        std_rate = daily_stats['cancel_rate'].std()
        
        # std가 0인 경우 처리
        if std_rate > 0:
            daily_stats['anomaly_score'] = (daily_stats['cancel_rate'] - mean_rate) / std_rate
        else:
            daily_stats['anomaly_score'] = 0
            
        return daily_stats.reset_index()

    @staticmethod
    def identify_high_risk_receipts(receipt_df: pd.DataFrame) -> pd.DataFrame:
        """
        고액 취소나 반복 취소 등 개별 영수증 리스크 식별
        """
        cancelled = receipt_df[receipt_df['status'] == 'cancelled'].copy()
        
        if cancelled.empty:
            return pd.DataFrame()
            
        # 평균 결제액 대비 3배 이상인 고액 취소건
        avg_payment = receipt_df['total_amount'].mean()
        cancelled['is_high_value'] = cancelled['total_amount'] > (avg_payment * 3)
        
        return cancelled[cancelled['is_high_value']]
