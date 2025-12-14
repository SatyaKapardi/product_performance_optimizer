"""Cannibalization Analysis - Detects products stealing sales from each other"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from itertools import combinations

class CannibalizationAnalyzer:
    """Analyzes customer overlap to detect product cannibalization"""
    
    def __init__(self, overlap_threshold: float = 0.85):
        self.overlap_threshold = overlap_threshold
    
    def analyze(self, customer_overlap_data: pd.DataFrame, sales_data: pd.DataFrame,
                product_info: pd.DataFrame) -> Dict:
        """
        Analyze product cannibalization based on customer overlap
        
        Returns:
            Dict with cannibalization pairs and recommendations
        """
        # Calculate customer overlap matrix
        overlap_matrix = self._calculate_overlap_matrix(customer_overlap_data)
        
        # Identify cannibalization pairs
        cannibal_pairs = self._identify_cannibalization(overlap_matrix, sales_data)
        
        # Calculate impact
        impact_analysis = self._calculate_impact(cannibal_pairs, sales_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(cannibal_pairs, impact_analysis, product_info)
        
        return {
            'overlap_matrix': overlap_matrix,
            'cannibalization_pairs': cannibal_pairs,
            'impact_analysis': impact_analysis,
            'recommendations': recommendations,
            'summary': {
                'total_pairs_analyzed': len(overlap_matrix),
                'cannibalization_pairs_count': len(cannibal_pairs),
                'high_risk_pairs': len(cannibal_pairs[cannibal_pairs['overlap_pct'] >= self.overlap_threshold])
            }
        }
    
    def _calculate_overlap_matrix(self, customer_overlap_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate customer overlap between all product pairs"""
        if customer_overlap_data.empty:
            return pd.DataFrame()
        
        # Get unique SKUs
        skus = customer_overlap_data['sku'].unique()
        
        # Create customer-SKU matrix
        customer_skus = customer_overlap_data.groupby('customer_id')['sku'].apply(set).to_dict()
        
        # Calculate overlap for all pairs
        overlap_pairs = []
        
        for sku1, sku2 in combinations(skus, 2):
            # Get customers who bought each SKU
            customers_sku1 = set()
            customers_sku2 = set()
            
            for customer_id, sku_set in customer_skus.items():
                if sku1 in sku_set:
                    customers_sku1.add(customer_id)
                if sku2 in sku_set:
                    customers_sku2.add(customer_id)
            
            # Calculate overlap
            if len(customers_sku1) > 0 or len(customers_sku2) > 0:
                overlap = len(customers_sku1 & customers_sku2)
                total_unique = len(customers_sku1 | customers_sku2)
                
                if total_unique > 0:
                    overlap_pct = overlap / total_unique
                    
                    overlap_pairs.append({
                        'sku1': sku1,
                        'sku2': sku2,
                        'customers_sku1': len(customers_sku1),
                        'customers_sku2': len(customers_sku2),
                        'overlap_count': overlap,
                        'overlap_pct': overlap_pct
                    })
        
        overlap_matrix = pd.DataFrame(overlap_pairs)
        return overlap_matrix
    
    def _identify_cannibalization(self, overlap_matrix: pd.DataFrame, 
                                 sales_data: pd.DataFrame) -> pd.DataFrame:
        """Identify products with high customer overlap (potential cannibalization)"""
        if overlap_matrix.empty:
            return pd.DataFrame()
        
        # Filter high overlap pairs
        cannibal_pairs = overlap_matrix[
            overlap_matrix['overlap_pct'] >= self.overlap_threshold
        ].copy()
        
        # Add sales data for context
        sales_summary = sales_data.groupby('sku').agg({
            'revenue': 'sum',
            'units': 'sum'
        }).reset_index()
        
        # Merge sales data for both SKUs
        cannibal_pairs = cannibal_pairs.merge(
            sales_summary.rename(columns={'sku': 'sku1', 'revenue': 'revenue1', 'units': 'units1'}),
            on='sku1',
            how='left'
        )
        
        cannibal_pairs = cannibal_pairs.merge(
            sales_summary.rename(columns={'sku': 'sku2', 'revenue': 'revenue2', 'units': 'units2'}),
            on='sku2',
            how='left'
        )
        
        # Calculate which product is stronger
        cannibal_pairs['stronger_sku'] = cannibal_pairs.apply(
            lambda row: row['sku1'] if row['revenue1'] >= row['revenue2'] else row['sku2'],
            axis=1
        )
        
        cannibal_pairs['weaker_sku'] = cannibal_pairs.apply(
            lambda row: row['sku2'] if row['revenue1'] >= row['revenue2'] else row['sku1'],
            axis=1
        )
        
        # Sort by overlap percentage (highest first)
        cannibal_pairs = cannibal_pairs.sort_values('overlap_pct', ascending=False)
        
        return cannibal_pairs
    
    def _calculate_impact(self, cannibal_pairs: pd.DataFrame, 
                         sales_data: pd.DataFrame) -> Dict:
        """Calculate financial impact of cannibalization"""
        if len(cannibal_pairs) == 0:
            return {
                'total_revenue_at_risk': 0,
                'average_overlap': 0,
                'potential_consolidation_savings': 0
            }
        
        # Calculate revenue at risk (revenue from weaker SKU)
        cannibal_pairs['revenue_at_risk'] = cannibal_pairs.apply(
            lambda row: min(row['revenue1'], row['revenue2']),
            axis=1
        )
        
        total_revenue_at_risk = cannibal_pairs['revenue_at_risk'].sum()
        average_overlap = cannibal_pairs['overlap_pct'].mean()
        
        # Estimate potential savings from consolidation (assuming 20% cost reduction)
        potential_savings = total_revenue_at_risk * 0.20
        
        return {
            'total_revenue_at_risk': float(total_revenue_at_risk),
            'average_overlap': float(average_overlap),
            'potential_consolidation_savings': float(potential_savings)
        }
    
    def _generate_recommendations(self, cannibal_pairs: pd.DataFrame,
                                 impact_analysis: Dict, product_info: pd.DataFrame) -> List[Dict]:
        """Generate recommendations for cannibalization pairs"""
        recommendations = []
        
        if len(cannibal_pairs) == 0:
            return recommendations
        
        # General recommendation
        recommendations.append({
            'type': 'cannibalization_warning',
            'priority': 'high',
            'action': f"{len(cannibal_pairs)} product pairs with high customer overlap detected",
            'impact': f"${impact_analysis['total_revenue_at_risk']:,.0f} revenue potentially at risk",
            'details': f"Average overlap: {impact_analysis['average_overlap']:.1%}"
        })
        
        # Top 10 cannibalization pairs
        top_pairs = cannibal_pairs.head(10)
        
        # Merge with product names
        product_names = product_info.set_index('sku')['product_name'].to_dict()
        
        for idx, row in top_pairs.iterrows():
            sku1_name = product_names.get(row['sku1'], row['sku1'])
            sku2_name = product_names.get(row['sku2'], row['sku2'])
            stronger = product_names.get(row['stronger_sku'], row['stronger_sku'])
            weaker = product_names.get(row['weaker_sku'], row['weaker_sku'])
            
            recommendations.append({
                'type': 'cannibalization_pair',
                'priority': 'high' if row['overlap_pct'] >= 0.90 else 'medium',
                'action': f"SKUs {row['sku1']} and {row['sku2']}: {row['overlap_pct']:.1%} customer overlap",
                'impact': f"Consider discontinuing {weaker} or differentiating products",
                'details': f"{sku1_name} vs {sku2_name} - Stronger: {stronger}"
            })
        
        return recommendations

