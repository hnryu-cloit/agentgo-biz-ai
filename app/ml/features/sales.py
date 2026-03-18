import pandas as pd
import numpy as np
from typing import List, Dict, Any

class SalesTrendFeature:
    """
    시간대별 매출 추이 분석 및 피크 타임 식별
    """
    
    @staticmethod
    def analyze_hourly_trends(sales_df: pd.DataFrame) -> Dict[str, Any]:
        """
        시간대별 매출 데이터를 분석하여 해석된 정보를 반환
        """
        if sales_df.empty:
            return {}

        # 1. 시간대별 집계
        hourly_stats = sales_df.groupby('hour')['revenue'].agg(['mean', 'sum', 'count']).reset_index()
        
        # 2. 피크 타임 식별 (상위 20% 매출 시간대)
        threshold = hourly_stats['sum'].quantile(0.8)
        peak_hours = hourly_stats[hourly_stats['sum'] >= threshold]['hour'].tolist()
        
        # 3. 추세 분석 (이동 평균 등을 통한 평활화)
        hourly_stats['moving_avg'] = hourly_stats['sum'].rolling(window=3, center=True, min_periods=1).mean()
        
        # 4. 상태 판별
        total_rev = hourly_stats['sum'].sum()
        avg_rev = hourly_stats['sum'].mean()
        
        # 가장 매출이 높은 시간과 낮은 시간 격차
        max_hour = hourly_stats.loc[hourly_stats['sum'].idxmax()]
        min_hour = hourly_stats.loc[hourly_stats['sum'].idxmin()]
        
        return {
            "hourly_data": hourly_stats.to_dict(orient='records'),
            "peak_hours": peak_hours,
            "best_hour": int(max_hour['hour']),
            "worst_hour": int(min_hour['hour']),
            "volatility": float(hourly_stats['sum'].std() / avg_rev) if avg_rev > 0 else 0,
            "summary": f"오늘의 주요 피크 타임은 {', '.join(map(str, peak_hours))}시이며, {int(max_hour['hour'])}시에 최대 매출이 발생했습니다."
        }
