"""SKU Rationalization Module - Identifies zombie products and bottom performers"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class SKURationalizationAnalyzer:
    """Identifies zombie products and calculates discontinue recommendations"""
    
    def __init__(self, threshold_percentile: int = 20):
        self.threshold_percentile = threshold_percentile
    
    def analyze(self, sales_data: pd.DataFrame, inventory_data: pd.DataFrame, 
                product_info: pd.DataFrame) -> Dict:
        """
        Analyze SKUs to identify zombie products and bottom performers
        
        Returns:
            Dict with recommendations and metrics
        """
        # Merge data
        merged = self._merge_data(sales_data, inventory_data, product_info)
        
        # Calculate metrics
        metrics = self._calculate_metrics(merged)
        
        # Identify zombie products
        zombies = self._identify_zombies(metrics)
        
        # Calculate financial impact
        financial_impact = self._calculate_financial_impact(zombies, inventory_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(zombies, financial_impact)
        
        return {
            'zombie_skus': zombies,
            'metrics': metrics,
            'financial_impact': financial_impact,
            'recommendations': recommendations,
            'summary': {
                'total_zombies': len(zombies),
                'capital_freed': financial_impact.get('working_capital_freed', 0),
                'bottom_percentile': self.threshold_percentile
            }
        }
    
    def _merge_data(self, sales_data: pd.DataFrame, inventory_data: pd.DataFrame,
                   product_info: pd.DataFrame) -> pd.DataFrame:
        """Merge sales, inventory, and product data"""
        # Aggregate sales by SKU
        sales_summary = sales_data.groupby('sku').agg({
            'revenue': 'sum',
            'units': 'sum',
            'fees': 'sum',
            'shipping_cost': 'sum'
        }).reset_index()
        
        # Merge with inventory
        merged = sales_summary.merge(
            inventory_data[['sku', 'quantity_on_hand', 'cost_per_unit']],
            on='sku',
            how='outer'
        )
        
        # Merge with product info
        merged = merged.merge(
            product_info[['sku', 'product_name', 'category', 'launch_date']],
            on='sku',
            how='left'
        )
        
        # Fill missing values
        merged['revenue'] = merged['revenue'].fillna(0)
        merged['units'] = merged['units'].fillna(0)
        merged['quantity_on_hand'] = merged['quantity_on_hand'].fillna(0)
        merged['cost_per_unit'] = merged['cost_per_unit'].fillna(0)
        
        return merged
    
    def _calculate_metrics(self, merged: pd.DataFrame) -> pd.DataFrame:
        """Calculate performance metrics for each SKU"""
        metrics = merged.copy()
        
        # Calculate profit margin
        metrics['profit'] = metrics['revenue'] - metrics['fees'] - metrics['shipping_cost']
        metrics['profit_margin'] = np.where(
            metrics['revenue'] > 0,
            metrics['profit'] / metrics['revenue'],
            0
        )
        
        # Calculate working capital tied up
        metrics['working_capital'] = metrics['quantity_on_hand'] * metrics['cost_per_unit']
        
        # Calculate revenue per unit
        metrics['revenue_per_unit'] = np.where(
            metrics['units'] > 0,
            metrics['revenue'] / metrics['units'],
            0
        )
        
        # Calculate velocity (units per day if we have date range)
        # For now, use total units as proxy
        metrics['velocity_score'] = metrics['units']
        
        # Composite score (lower is worse)
        metrics['composite_score'] = (
            metrics['revenue'].rank(pct=True, ascending=False) * 0.4 +
            metrics['profit'].rank(pct=True, ascending=False) * 0.4 +
            metrics['velocity_score'].rank(pct=True, ascending=False) * 0.2
        )
        
        return metrics
    
    def _identify_zombies(self, metrics: pd.DataFrame) -> pd.DataFrame:
        """Identify zombie products (bottom percentile performers)"""
        # Filter out products with no sales and no inventory
        active_skus = metrics[
            (metrics['revenue'] > 0) | (metrics['quantity_on_hand'] > 0)
        ].copy()
        
        if len(active_skus) == 0:
            return pd.DataFrame()
        
        # Identify bottom percentile
        threshold = np.percentile(active_skus['composite_score'], self.threshold_percentile)
        zombies = active_skus[active_skus['composite_score'] <= threshold].copy()
        
        # Sort by composite score (worst first)
        zombies = zombies.sort_values('composite_score')
        
        # Add status
        zombies['status'] = 'zombie'
        zombies['reason'] = zombies.apply(self._get_zombie_reason, axis=1)
        
        return zombies
    
    def _get_zombie_reason(self, row: pd.Series) -> str:
        """Generate reason why product is a zombie"""
        reasons = []
        
        if row['revenue'] == 0:
            reasons.append("No revenue")
        elif row['revenue'] < 100:
            reasons.append("Very low revenue")
        
        if row['profit'] < 0:
            reasons.append("Negative profit")
        elif row['profit_margin'] < 0.1:
            reasons.append("Low profit margin")
        
        if row['units'] == 0:
            reasons.append("No units sold")
        elif row['units'] < 5:
            reasons.append("Very slow moving")
        
        if row['quantity_on_hand'] > 0 and row['units'] == 0:
            reasons.append("Dead inventory")
        
        return "; ".join(reasons) if reasons else "Bottom performer"
    
    def _calculate_financial_impact(self, zombies: pd.DataFrame, 
                                   inventory_data: pd.DataFrame) -> Dict:
        """Calculate financial impact of discontinuing zombie products"""
        if len(zombies) == 0:
            return {
                'working_capital_freed': 0,
                'annual_revenue_lost': 0,
                'annual_profit_lost': 0,
                'net_benefit': 0
            }
        
        # Working capital freed up
        working_capital_freed = zombies['working_capital'].sum()
        
        # Annual revenue and profit lost (assuming current run rate)
        annual_revenue_lost = zombies['revenue'].sum() * 12  # Assuming monthly data
        annual_profit_lost = zombies['profit'].sum() * 12
        
        # Net benefit (capital freed - profit lost)
        net_benefit = working_capital_freed - annual_profit_lost
        
        return {
            'working_capital_freed': float(working_capital_freed),
            'annual_revenue_lost': float(annual_revenue_lost),
            'annual_profit_lost': float(annual_profit_lost),
            'net_benefit': float(net_benefit)
        }
    
    def _generate_recommendations(self, zombies: pd.DataFrame, 
                                 financial_impact: Dict) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if len(zombies) == 0:
            return recommendations
        
        # Main recommendation
        recommendations.append({
            'type': 'discontinue',
            'priority': 'high',
            'action': f"Discontinue {len(zombies)} zombie SKUs",
            'impact': f"Free ${financial_impact['working_capital_freed']:,.0f} in working capital",
            'details': f"Bottom {self.threshold_percentile}% of SKUs identified for discontinuation"
        })
        
        # Top 10 worst performers
        top_zombies = zombies.head(10)
        for idx, row in top_zombies.iterrows():
            recommendations.append({
                'type': 'discontinue_sku',
                'priority': 'high',
                'action': f"Discontinue SKU: {row['sku']}",
                'impact': f"Free ${row['working_capital']:,.0f} capital",
                'details': f"{row['reason']} - Revenue: ${row['revenue']:,.0f}, Profit: ${row['profit']:,.0f}"
            })
        
        return recommendations

