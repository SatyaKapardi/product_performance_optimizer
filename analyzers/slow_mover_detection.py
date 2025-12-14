"""Slow Mover Detection - Calculates inventory turnover and alerts on slow movers"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class SlowMoverAnalyzer:
    """Detects slow-moving inventory and calculates days of supply"""
    
    def __init__(self, days_threshold: int = 180):
        self.days_threshold = days_threshold
    
    def analyze(self, sales_data: pd.DataFrame, inventory_data: pd.DataFrame,
                product_info: pd.DataFrame, analysis_period_days: int = 90) -> Dict:
        """
        Analyze inventory turnover and identify slow movers
        
        Args:
            analysis_period_days: Number of days to analyze sales velocity
        
        Returns:
            Dict with slow mover analysis and recommendations
        """
        # Merge data
        merged = self._merge_data(sales_data, inventory_data, product_info)
        
        # Calculate velocity metrics
        velocity = self._calculate_velocity(merged, analysis_period_days)
        
        # Calculate days of supply
        days_supply = self._calculate_days_of_supply(velocity)
        
        # Identify slow movers
        slow_movers = self._identify_slow_movers(days_supply)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(slow_movers)
        
        return {
            'velocity_analysis': days_supply,
            'slow_movers': slow_movers,
            'recommendations': recommendations,
            'summary': {
                'total_skus_analyzed': len(days_supply),
                'slow_movers_count': len(slow_movers),
                'total_slow_inventory_value': float(slow_movers['inventory_value'].sum()) if len(slow_movers) > 0 else 0,
                'threshold_days': self.days_threshold
            }
        }
    
    def _merge_data(self, sales_data: pd.DataFrame, inventory_data: pd.DataFrame,
                   product_info: pd.DataFrame) -> pd.DataFrame:
        """Merge sales, inventory, and product data"""
        # Calculate sales velocity (units per day)
        if 'date' in sales_data.columns:
            sales_data['date'] = pd.to_datetime(sales_data['date'])
            date_range = (sales_data['date'].max() - sales_data['date'].min()).days
            date_range = max(date_range, 1)  # Avoid division by zero
        else:
            date_range = 90  # Default assumption
        
        sales_summary = sales_data.groupby('sku').agg({
            'units': 'sum',
            'revenue': 'sum'
        }).reset_index()
        
        sales_summary['sales_period_days'] = date_range
        
        # Merge with inventory
        merged = sales_summary.merge(
            inventory_data[['sku', 'quantity_on_hand', 'cost_per_unit']],
            on='sku',
            how='outer'
        )
        
        # Merge with product info
        merged = merged.merge(
            product_info[['sku', 'product_name', 'category', 'price']],
            on='sku',
            how='left'
        )
        
        # Fill missing values
        merged['units'] = merged['units'].fillna(0)
        merged['quantity_on_hand'] = merged['quantity_on_hand'].fillna(0)
        merged['cost_per_unit'] = merged['cost_per_unit'].fillna(0)
        merged['sales_period_days'] = merged['sales_period_days'].fillna(date_range)
        
        return merged
    
    def _calculate_velocity(self, merged: pd.DataFrame, analysis_period_days: int) -> pd.DataFrame:
        """Calculate sales velocity metrics"""
        velocity = merged.copy()
        
        # Calculate units per day
        velocity['units_per_day'] = np.where(
            velocity['sales_period_days'] > 0,
            velocity['units'] / velocity['sales_period_days'],
            0
        )
        
        # Calculate revenue per day
        velocity['revenue_per_day'] = np.where(
            velocity['sales_period_days'] > 0,
            velocity['revenue'] / velocity['sales_period_days'],
            0
        )
        
        # Calculate inventory turnover rate
        velocity['inventory_turnover'] = np.where(
            velocity['quantity_on_hand'] > 0,
            velocity['units'] / velocity['quantity_on_hand'],
            0
        )
        
        return velocity
    
    def _calculate_days_of_supply(self, velocity: pd.DataFrame) -> pd.DataFrame:
        """Calculate days of supply on hand"""
        days_supply = velocity.copy()
        
        # Calculate days of supply
        days_supply['days_of_supply'] = np.where(
            days_supply['units_per_day'] > 0,
            days_supply['quantity_on_hand'] / days_supply['units_per_day'],
            np.inf  # Infinite if no sales
        )
        
        # Calculate inventory value
        days_supply['inventory_value'] = (
            days_supply['quantity_on_hand'] * days_supply['cost_per_unit']
        )
        
        # Categorize inventory age
        days_supply['inventory_age_category'] = days_supply['days_of_supply'].apply(
            self._categorize_age
        )
        
        return days_supply
    
    def _categorize_age(self, days: float) -> str:
        """Categorize inventory age"""
        if np.isinf(days) or days == 0:
            return 'no_sales'
        elif days >= self.days_threshold:
            return 'critical'
        elif days >= 90:
            return 'slow'
        elif days >= 30:
            return 'normal'
        else:
            return 'fast'
    
    def _identify_slow_movers(self, days_supply: pd.DataFrame) -> pd.DataFrame:
        """Identify slow-moving products"""
        slow_movers = days_supply[
            (days_supply['days_of_supply'] >= self.days_threshold) |
            (days_supply['days_of_supply'] == np.inf)
        ].copy()
        
        # Sort by days of supply (worst first)
        slow_movers = slow_movers.sort_values('days_of_supply', ascending=False)
        
        # Add urgency level
        slow_movers['urgency'] = slow_movers['days_of_supply'].apply(self._get_urgency)
        
        return slow_movers
    
    def _get_urgency(self, days: float) -> str:
        """Get urgency level"""
        if np.isinf(days):
            return 'critical'
        elif days >= 365:
            return 'critical'
        elif days >= self.days_threshold:
            return 'high'
        else:
            return 'medium'
    
    def _generate_recommendations(self, slow_movers: pd.DataFrame) -> List[Dict]:
        """Generate recommendations for slow movers"""
        recommendations = []
        
        if len(slow_movers) == 0:
            return recommendations
        
        # Critical inventory
        critical = slow_movers[slow_movers['urgency'] == 'critical']
        if len(critical) > 0:
            total_value = critical['inventory_value'].sum()
            recommendations.append({
                'type': 'markdown_urgent',
                'priority': 'critical',
                'action': f"Immediate markdown needed for {len(critical)} SKUs",
                'impact': f"${total_value:,.0f} in dead inventory",
                'details': 'These SKUs have no sales or >365 days of inventory'
            })
        
        # High priority slow movers
        high_priority = slow_movers[
            (slow_movers['urgency'] == 'high') &
            (slow_movers['days_of_supply'] >= self.days_threshold)
        ]
        
        if len(high_priority) > 0:
            total_value = high_priority['inventory_value'].sum()
            recommendations.append({
                'type': 'markdown',
                'priority': 'high',
                'action': f"Markdown {len(high_priority)} slow-moving SKUs",
                'impact': f"${total_value:,.0f} in slow inventory",
                'details': f"These SKUs have {self.days_threshold}+ days of inventory"
            })
        
        # Individual SKU recommendations
        top_slow = slow_movers.head(10)
        for idx, row in top_slow.iterrows():
            days = row['days_of_supply']
            if np.isinf(days):
                days_str = "No sales"
            else:
                days_str = f"{int(days)} days"
            
            recommendations.append({
                'type': 'sku_action',
                'priority': row['urgency'],
                'action': f"SKU {row['sku']}: {days_str} of inventory",
                'impact': f"${row['inventory_value']:,.0f} tied up",
                'details': f"Current velocity: {row['units_per_day']:.2f} units/day"
            })
        
        return recommendations

