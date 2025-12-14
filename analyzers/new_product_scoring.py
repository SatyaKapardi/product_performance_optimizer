"""New Product Success Scoring - Compares new launches to historical winners"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class NewProductScoringAnalyzer:
    """Scores new product launches against historical performance"""
    
    def __init__(self, analysis_windows: List[int] = [30, 60, 90]):
        self.analysis_windows = analysis_windows
    
    def analyze(self, sales_data: pd.DataFrame, product_info: pd.DataFrame,
                current_date: datetime = None) -> Dict:
        """
        Analyze new product performance vs historical benchmarks
        
        Returns:
            Dict with new product scores and recommendations
        """
        if current_date is None:
            current_date = datetime.now()
        
        # Identify new products
        new_products = self._identify_new_products(product_info, current_date)
        
        if len(new_products) == 0:
            return {
                'new_products': pd.DataFrame(),
                'benchmarks': {},
                'scores': pd.DataFrame(),
                'recommendations': [],
                'summary': {'new_products_count': 0}
            }
        
        # Calculate historical benchmarks
        benchmarks = self._calculate_benchmarks(sales_data, product_info, current_date)
        
        # Score new products
        scores = self._score_new_products(new_products, sales_data, benchmarks, current_date)
        
        # Identify underperformers
        underperformers = self._identify_underperformers(scores)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(scores, underperformers, product_info)
        
        return {
            'new_products': new_products,
            'benchmarks': benchmarks,
            'scores': scores,
            'underperformers': underperformers,
            'recommendations': recommendations,
            'summary': {
                'new_products_count': len(new_products),
                'underperformers_count': len(underperformers),
                'winners_count': len(scores[scores['overall_score'] >= 0.7])
            }
        }
    
    def _identify_new_products(self, product_info: pd.DataFrame, 
                               current_date: datetime) -> pd.DataFrame:
        """Identify products launched within analysis windows"""
        if 'launch_date' not in product_info.columns:
            return pd.DataFrame()
        
        product_info = product_info.copy()
        product_info['launch_date'] = pd.to_datetime(product_info['launch_date'], errors='coerce')
        
        # Find products launched within max analysis window
        max_window = max(self.analysis_windows)
        cutoff_date = current_date - timedelta(days=max_window)
        
        new_products = product_info[
            product_info['launch_date'] >= cutoff_date
        ].copy()
        
        # Calculate days since launch
        new_products['days_since_launch'] = (
            current_date - new_products['launch_date']
        ).dt.days
        
        return new_products
    
    def _calculate_benchmarks(self, sales_data: pd.DataFrame, 
                             product_info: pd.DataFrame, current_date: datetime) -> Dict:
        """Calculate historical performance benchmarks"""
        benchmarks = {}
        
        # Merge sales with product info
        merged = sales_data.merge(
            product_info[['sku', 'launch_date']],
            on='sku',
            how='left'
        )
        
        merged['launch_date'] = pd.to_datetime(merged['launch_date'], errors='coerce')
        merged['date'] = pd.to_datetime(merged['date'], errors='coerce')
        
        # Calculate days since launch for each sale
        merged['days_since_launch'] = (
            merged['date'] - merged['launch_date']
        ).dt.days
        
        # Calculate benchmarks for each window
        for window in self.analysis_windows:
            # Get sales within window for all products
            window_sales = merged[
                (merged['days_since_launch'] >= 0) &
                (merged['days_since_launch'] <= window)
            ]
            
            # Aggregate by SKU
            window_summary = window_sales.groupby('sku').agg({
                'revenue': 'sum',
                'units': 'sum'
            }).reset_index()
            
            # Calculate percentiles
            benchmarks[f'{window}_day'] = {
                'revenue_p50': window_summary['revenue'].quantile(0.5),
                'revenue_p75': window_summary['revenue'].quantile(0.75),
                'revenue_p90': window_summary['revenue'].quantile(0.9),
                'units_p50': window_summary['units'].quantile(0.5),
                'units_p75': window_summary['units'].quantile(0.75),
                'units_p90': window_summary['units'].quantile(0.9)
            }
        
        return benchmarks
    
    def _score_new_products(self, new_products: pd.DataFrame, sales_data: pd.DataFrame,
                           benchmarks: Dict, current_date: datetime) -> pd.DataFrame:
        """Score new products against benchmarks"""
        scores = new_products.copy()
        
        # Merge with sales data
        merged = sales_data.merge(
            new_products[['sku', 'launch_date', 'days_since_launch']],
            on='sku',
            how='left'
        )
        
        merged['date'] = pd.to_datetime(merged['date'], errors='coerce')
        merged['launch_date'] = pd.to_datetime(merged['launch_date'], errors='coerce')
        merged['days_since_launch'] = (
            merged['date'] - merged['launch_date']
        ).dt.days
        
        # Calculate scores for each window
        window_scores = []
        
        for window in self.analysis_windows:
            window_data = merged[
                (merged['days_since_launch'] >= 0) &
                (merged['days_since_launch'] <= window)
            ]
            
            window_summary = window_data.groupby('sku').agg({
                'revenue': 'sum',
                'units': 'sum'
            }).reset_index()
            
            window_summary['window'] = window
            
            window_scores.append(window_summary)
        
        # Combine window scores
        all_window_scores = pd.concat(window_scores, ignore_index=True)
        
        # Calculate performance scores
        score_results = []
        
        for sku in new_products['sku'].unique():
            sku_scores = {}
            sku_scores['sku'] = sku
            
            for window in self.analysis_windows:
                window_key = f'{window}_day'
                window_data = all_window_scores[
                    (all_window_scores['sku'] == sku) &
                    (all_window_scores['window'] == window)
                ]
                
                if len(window_data) > 0:
                    revenue = window_data['revenue'].iloc[0]
                    units = window_data['units'].iloc[0]
                    
                    # Score against benchmarks
                    bench = benchmarks.get(window_key, {})
                    revenue_p50 = bench.get('revenue_p50', 0)
                    revenue_p75 = bench.get('revenue_p75', 0)
                    units_p50 = bench.get('units_p50', 0)
                    units_p75 = bench.get('units_p75', 0)
                    
                    # Calculate score (0-1 scale)
                    if revenue_p50 > 0:
                        revenue_score = min(revenue / revenue_p75, 1.0) if revenue_p75 > 0 else 0
                    else:
                        revenue_score = 0
                    
                    if units_p50 > 0:
                        units_score = min(units / units_p75, 1.0) if units_p75 > 0 else 0
                    else:
                        units_score = 0
                    
                    sku_scores[f'{window}_revenue'] = revenue
                    sku_scores[f'{window}_units'] = units
                    sku_scores[f'{window}_revenue_score'] = revenue_score
                    sku_scores[f'{window}_units_score'] = units_score
                else:
                    sku_scores[f'{window}_revenue'] = 0
                    sku_scores[f'{window}_units'] = 0
                    sku_scores[f'{window}_revenue_score'] = 0
                    sku_scores[f'{window}_units_score'] = 0
            
            # Calculate overall score (weighted average)
            revenue_scores = [sku_scores.get(f'{w}_revenue_score', 0) for w in self.analysis_windows]
            units_scores = [sku_scores.get(f'{w}_units_score', 0) for w in self.analysis_windows]
            
            sku_scores['overall_score'] = (np.mean(revenue_scores) * 0.6 + np.mean(units_scores) * 0.4)
            
            score_results.append(sku_scores)
        
        scores_df = pd.DataFrame(score_results)
        
        # Merge back with product info
        scores = scores.merge(scores_df, on='sku', how='left')
        
        # Categorize performance
        scores['performance_category'] = scores['overall_score'].apply(self._categorize_performance)
        
        return scores
    
    def _categorize_performance(self, score: float) -> str:
        """Categorize product performance"""
        if pd.isna(score):
            return 'insufficient_data'
        elif score >= 0.8:
            return 'winner'
        elif score >= 0.6:
            return 'solid'
        elif score >= 0.4:
            return 'underperforming'
        else:
            return 'poor'
    
    def _identify_underperformers(self, scores: pd.DataFrame) -> pd.DataFrame:
        """Identify underperforming new products"""
        underperformers = scores[
            scores['performance_category'].isin(['underperforming', 'poor'])
        ].copy()
        
        underperformers = underperformers.sort_values('overall_score')
        
        return underperformers
    
    def _generate_recommendations(self, scores: pd.DataFrame, underperformers: pd.DataFrame,
                                 product_info: pd.DataFrame) -> List[Dict]:
        """Generate recommendations for new products"""
        recommendations = []
        
        # Winners
        winners = scores[scores['performance_category'] == 'winner']
        if len(winners) > 0:
            recommendations.append({
                'type': 'success',
                'priority': 'low',
                'action': f"{len(winners)} new products performing well",
                'impact': 'Consider increasing inventory and marketing for these winners',
                'details': 'These products are meeting or exceeding historical benchmarks'
            })
        
        # Underperformers
        if len(underperformers) > 0:
            recommendations.append({
                'type': 'warning',
                'priority': 'high',
                'action': f"{len(underperformers)} new products underperforming",
                'impact': 'Early intervention needed - increase marketing or cut losses',
                'details': 'These products are below historical benchmarks'
            })
            
            # Individual recommendations
            top_underperformers = underperformers.head(10)
            product_names = product_info.set_index('sku')['product_name'].to_dict()
            
            for idx, row in top_underperformers.iterrows():
                product_name = product_names.get(row['sku'], row['sku'])
                score = row['overall_score']
                
                recommendations.append({
                    'type': 'new_product_action',
                    'priority': 'high' if score < 0.3 else 'medium',
                    'action': f"SKU {row['sku']} ({product_name}): Score {score:.2f}",
                    'impact': 'Review marketing strategy or consider discontinuation',
                    'details': f"Performance category: {row['performance_category']}"
                })
        
        return recommendations

