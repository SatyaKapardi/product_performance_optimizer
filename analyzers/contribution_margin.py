"""Contribution Margin Ranking - Sorts products by TRUE profit"""
import pandas as pd
import numpy as np
from typing import Dict, List

class ContributionMarginAnalyzer:
    """Analyzes true profit contribution after all costs"""
    
    def analyze(self, sales_data: pd.DataFrame, inventory_data: pd.DataFrame,
                product_info: pd.DataFrame) -> Dict:
        """
        Analyze contribution margin for each SKU
        
        Returns:
            Dict with ranked products and profit analysis
        """
        # Merge and calculate metrics
        merged = self._merge_data(sales_data, inventory_data, product_info)
        
        # Calculate contribution margins
        margins = self._calculate_contribution_margins(merged)
        
        # Rank products
        ranked = self._rank_products(margins)
        
        # Identify money losers
        losers = self._identify_money_losers(ranked)
        
        # Generate insights
        insights = self._generate_insights(ranked, losers)
        
        return {
            'ranked_products': ranked,
            'money_losers': losers,
            'insights': insights,
            'summary': {
                'total_skus': len(ranked),
                'profitable_skus': len(ranked[ranked['contribution_margin'] > 0]),
                'losing_skus': len(losers),
                'total_profit': float(ranked['total_profit'].sum()),
                'total_losses': float(losers['total_profit'].sum()) if len(losers) > 0 else 0
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
            'shipping_cost': 'sum',
            'returns': 'sum'
        }).reset_index()
        
        # Merge with inventory for cost data
        merged = sales_summary.merge(
            inventory_data[['sku', 'cost_per_unit']],
            on='sku',
            how='left'
        )
        
        # Merge with product info
        merged = merged.merge(
            product_info[['sku', 'product_name', 'category', 'price']],
            on='sku',
            how='left'
        )
        
        # Fill missing values
        merged['cost_per_unit'] = merged['cost_per_unit'].fillna(0)
        merged['returns'] = merged['returns'].fillna(0)
        
        return merged
    
    def _calculate_contribution_margins(self, merged: pd.DataFrame) -> pd.DataFrame:
        """Calculate true contribution margin after all costs"""
        margins = merged.copy()
        
        # Calculate cost of goods sold
        margins['cogs'] = margins['units'] * margins['cost_per_unit']
        
        # Calculate return costs (assume 50% of return value is lost)
        margins['return_cost'] = margins['returns'] * 0.5
        
        # Calculate total costs
        margins['total_costs'] = (
            margins['fees'] +
            margins['shipping_cost'] +
            margins['cogs'] +
            margins['return_cost']
        )
        
        # Calculate contribution margin (profit)
        margins['contribution_margin'] = margins['revenue'] - margins['total_costs']
        
        # Calculate contribution margin percentage
        margins['contribution_margin_pct'] = np.where(
            margins['revenue'] > 0,
            margins['contribution_margin'] / margins['revenue'],
            0
        )
        
        # Calculate profit per unit
        margins['profit_per_unit'] = np.where(
            margins['units'] > 0,
            margins['contribution_margin'] / margins['units'],
            0
        )
        
        # Rename for clarity
        margins['total_profit'] = margins['contribution_margin']
        
        return margins
    
    def _rank_products(self, margins: pd.DataFrame) -> pd.DataFrame:
        """Rank products by contribution margin"""
        ranked = margins.copy()
        
        # Sort by total profit (descending)
        ranked = ranked.sort_values('contribution_margin', ascending=False)
        
        # Add rank
        ranked['rank'] = range(1, len(ranked) + 1)
        
        # Add percentile
        ranked['profit_percentile'] = ranked['contribution_margin'].rank(pct=True)
        
        # Categorize
        ranked['category'] = ranked.apply(self._categorize_product, axis=1)
        
        return ranked
    
    def _categorize_product(self, row: pd.Series) -> str:
        """Categorize product performance"""
        if row['contribution_margin'] < 0:
            return 'money_loser'
        elif row['profit_percentile'] >= 0.8:
            return 'top_performer'
        elif row['profit_percentile'] >= 0.5:
            return 'solid_performer'
        elif row['profit_percentile'] >= 0.2:
            return 'marginal'
        else:
            return 'poor_performer'
    
    def _identify_money_losers(self, ranked: pd.DataFrame) -> pd.DataFrame:
        """Identify products losing money"""
        losers = ranked[ranked['contribution_margin'] < 0].copy()
        losers = losers.sort_values('contribution_margin')  # Worst first
        
        return losers
    
    def _generate_insights(self, ranked: pd.DataFrame, losers: pd.DataFrame) -> List[Dict]:
        """Generate insights and recommendations"""
        insights = []
        
        # Top performers insight
        top_30 = ranked.head(30)
        top_30_profit = top_30['contribution_margin'].sum()
        total_profit = ranked['contribution_margin'].sum()
        
        if len(ranked) > 30:
            top_30_pct = (top_30_profit / total_profit) * 100 if total_profit > 0 else 0
            insights.append({
                'type': 'focus_opportunity',
                'title': 'Focus on Top 30 SKUs',
                'description': f"Top 30 SKUs generate {top_30_pct:.1f}% of total profit",
                'impact': f"Potential to increase profit by focusing marketing on these SKUs",
                'action': 'Prioritize marketing and inventory for top 30 SKUs'
            })
        
        # Money losers insight
        if len(losers) > 0:
            total_loss = losers['contribution_margin'].sum()
            insights.append({
                'type': 'warning',
                'title': f'{len(losers)} SKUs Losing Money',
                'description': f"These SKUs have negative contribution margins",
                'impact': f"Total losses: ${abs(total_loss):,.0f}",
                'action': 'Review pricing, costs, or discontinue these SKUs'
            })
        
        # High revenue, low profit insight
        high_revenue_low_profit = ranked[
            (ranked['revenue'] > ranked['revenue'].quantile(0.7)) &
            (ranked['contribution_margin_pct'] < 0.1)
        ]
        
        if len(high_revenue_low_profit) > 0:
            insights.append({
                'type': 'warning',
                'title': 'High Revenue, Low Profit SKUs',
                'description': f"{len(high_revenue_low_profit)} SKUs have high revenue but low margins",
                'impact': 'These "bestsellers" may not be as profitable as they appear',
                'action': 'Review pricing strategy or reduce costs for these SKUs'
            })
        
        return insights

