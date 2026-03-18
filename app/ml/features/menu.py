import pandas as pd
import numpy as np
from typing import List, Dict, Any

class MenuEngineeringFeature:
    """
    메뉴 엔지니어링 분석을 위한 피처 추출기
    Popularity (인기도)와 Profitability (수익성)을 계산합니다.
    """
    
    @staticmethod
    def calculate_metrics(sales_df: pd.DataFrame, lineup_df: pd.DataFrame) -> pd.DataFrame:
        """
        판매 데이터와 메뉴 마스터를 결합하여 핵심 지표 산출
        """
        # 1. 데이터 결합 (매장별/메뉴별 판매량 합산)
        menu_sales = sales_df.groupby('menu_name')['qty'].sum().reset_index()
        
        # 2. 마스터 데이터와 병합
        df = pd.merge(menu_sales, lineup_df, on='menu_name', how='inner')
        
        # 3. 메뉴별 마진 계산 (판매가 - 원가)
        df['unit_margin'] = df['sales_price'] - df['cost_price']
        df['total_margin'] = df['unit_margin'] * df['qty']
        
        # 4. 인기도 지표 (전체 판매량 대비 비중)
        total_qty = df['qty'].sum()
        df['popularity_index'] = df['qty'] / total_qty
        
        # 5. 수익성 지표 (메뉴별 마진 / 평균 마진)
        avg_margin = df['unit_margin'].mean()
        df['profitability_index'] = df['unit_margin'] / avg_margin
        
        return df

    @staticmethod
    def categorize_menu(df: pd.DataFrame) -> pd.DataFrame:
        """
        4분면 분석 기준에 따라 카테고리 분류
        기준: 인기도(70% rule), 수익성(평균 마진)
        """
        # 기준선 설정
        # 인기도 기준: (1 / 메뉴 수) * 0.7 (간단한 기준)
        pop_threshold = (1 / len(df)) * 0.7 if len(df) > 0 else 0
        # 수익성 기준: 평균 마진액
        prof_threshold = 1.0 # 인덱스 기준 1.0 (평균)
        
        def assign_category(row):
            is_high_pop = row['popularity_index'] >= pop_threshold
            is_high_prof = row['profitability_index'] >= prof_threshold
            
            if is_high_pop and is_high_prof:
                return "Star"
            elif is_high_pop and not is_high_prof:
                return "Plowhorse"
            elif not is_high_pop and is_high_prof:
                return "Puzzle"
            else:
                return "Dog"
        
        df['category'] = df.apply(assign_category, axis=1)
        return df
