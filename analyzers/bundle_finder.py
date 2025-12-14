"""Bundle Opportunity Finder - Identifies products frequently viewed together"""
import pandas as pd
import numpy as np
from typing import Dict, List
from itertools import combinations
from scipy.stats import chi2_contingency

class BundleFinderAnalyzer:
    """Finds bundle opportunities based on product view correlation"""
    
    def __init__(self, correlation_threshold: float = 0.70):
        self.correlation_threshold = correlation_threshold
    
    def analyze(self, product_views_data: pd.DataFrame, sales_data: pd.DataFrame,
                product_info: pd.DataFrame) -> Dict:
        """
        Analyze product view patterns to find bundle opportunities
        
        Returns:
            Dict with bundle opportunities and recommendations
        """
        if product_views_data.empty:
            return {
                'view_correlations': pd.DataFrame(),
                'bundle_opportunities': pd.DataFrame(),
                'recommendations': [],
                'summary': {'opportunities_count': 0}
            }
        
        # Calculate view correlations
        correlations = self._calculate_view_correlations(product_views_data)
        
        # Identify bundle opportunities
        bundles = self._identify_bundle_opportunities(correlations, sales_data)
        
        # Calculate bundle potential
        bundle_potential = self._calculate_bundle_potential(bundles, sales_data, product_info)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bundles, bundle_potential, product_info)
        
        return {
            'view_correlations': correlations,
            'bundle_opportunities': bundles,
            'bundle_potential': bundle_potential,
            'recommendations': recommendations,
            'summary': {
                'opportunities_count': len(bundles),
                'high_potential_bundles': len(bundles[bundles['correlation'] >= self.correlation_threshold])
            }
        }
    
    def _calculate_view_correlations(self, product_views_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation between product views"""
        # Create session-level view matrix
        if 'session_id' not in product_views_data.columns:
            # If no session_id, create one based on date and visitor
            if 'unique_visitors' in product_views_data.columns:
                product_views_data['session_id'] = (
                    product_views_data['date'].astype(str) + '_' +
                    product_views_data['unique_visitors'].astype(str)
                )
            else:
                product_views_data['session_id'] = product_views_data['date'].astype(str)
        
        # Create binary matrix: session x SKU (1 if viewed)
        view_matrix = product_views_data.groupby(['session_id', 'sku']).size().unstack(fill_value=0)
        view_matrix = (view_matrix > 0).astype(int)
        
        # Calculate correlation between all SKU pairs
        skus = view_matrix.columns.tolist()
        correlations = []
        
        for sku1, sku2 in combinations(skus, 2):
            if sku1 in view_matrix.columns and sku2 in view_matrix.columns:
                # Calculate co-view rate
                views_sku1 = view_matrix[sku1].sum()
                views_sku2 = view_matrix[sku2].sum()
                co_views = ((view_matrix[sku1] * view_matrix[sku2]) > 0).sum()
                
                if views_sku1 > 0 and views_sku2 > 0:
                    # Correlation: percentage of SKU1 viewers who also viewed SKU2
                    correlation_1_to_2 = co_views / views_sku1 if views_sku1 > 0 else 0
                    correlation_2_to_1 = co_views / views_sku2 if views_sku2 > 0 else 0
                    
                    # Use average correlation
                    avg_correlation = (correlation_1_to_2 + correlation_2_to_1) / 2
                    
                    correlations.append({
                        'sku1': sku1,
                        'sku2': sku2,
                        'views_sku1': views_sku1,
                        'views_sku2': views_sku2,
                        'co_views': co_views,
                        'correlation': avg_correlation,
                        'correlation_1_to_2': correlation_1_to_2,
                        'correlation_2_to_1': correlation_2_to_1
                    })
        
        correlations_df = pd.DataFrame(correlations)
        return correlations_df
    
    def _identify_bundle_opportunities(self, correlations: pd.DataFrame,
                                       sales_data: pd.DataFrame) -> pd.DataFrame:
        """Identify high-correlation pairs as bundle opportunities"""
        if correlations.empty:
            return pd.DataFrame()
        
        # Filter high correlation pairs
        bundles = correlations[
            correlations['correlation'] >= self.correlation_threshold
        ].copy()
        
        # Add sales data for context
        sales_summary = sales_data.groupby('sku').agg({
            'revenue': ['sum', 'mean'],
            'units': 'sum'
        }).reset_index()
        sales_summary.columns = ['sku', 'revenue_sum', 'revenue_mean', 'units']
        
        # Merge sales for both SKUs
        bundles = bundles.merge(
            sales_summary.rename(columns={'sku': 'sku1', 'revenue_sum': 'revenue1', 'units': 'units1'}),
            on='sku1',
            how='left'
        )
        
        bundles = bundles.merge(
            sales_summary.rename(columns={'sku': 'sku2', 'revenue_sum': 'revenue2', 'units': 'units2'}),
            on='sku2',
            how='left'
        )
        
        # Calculate combined revenue potential
        bundles['combined_revenue'] = bundles['revenue1'] + bundles['revenue2']
        
        # Sort by correlation and revenue potential
        bundles = bundles.sort_values(['correlation', 'combined_revenue'], ascending=[False, False])
        
        return bundles
    
    def _calculate_bundle_potential(self, bundles: pd.DataFrame, sales_data: pd.DataFrame,
                                   product_info: pd.DataFrame) -> Dict:
        """Calculate potential revenue from bundles"""
        if len(bundles) == 0:
            return {
                'total_potential_revenue': 0,
                'estimated_bundle_conversion': 0,
                'average_bundle_discount': 0.1  # 10% discount assumption
            }
        
        # Estimate bundle conversion rate (assume 15% of co-viewers would buy bundle)
        total_co_views = bundles['co_views'].sum()
        estimated_conversions = total_co_views * 0.15
        
        # Calculate potential revenue (with 10% bundle discount)
        bundles['bundle_price'] = (bundles['revenue1'] + bundles['revenue2']) * 0.9
        bundles['potential_revenue'] = bundles['bundle_price'] * (bundles['co_views'] * 0.15)
        
        total_potential_revenue = bundles['potential_revenue'].sum()
        
        return {
            'total_potential_revenue': float(total_potential_revenue),
            'estimated_bundle_conversions': float(estimated_conversions),
            'average_bundle_discount': 0.1,
            'top_bundle_opportunities': bundles.head(10).to_dict('records')
        }
    
    def _generate_recommendations(self, bundles: pd.DataFrame, bundle_potential: Dict,
                                 product_info: pd.DataFrame) -> List[Dict]:
        """Generate bundle recommendations"""
        recommendations = []
        
        if len(bundles) == 0:
            return recommendations
        
        # General recommendation
        recommendations.append({
            'type': 'bundle_opportunity',
            'priority': 'medium',
            'action': f"Create {len(bundles)} product bundles",
            'impact': f"Potential revenue: ${bundle_potential['total_potential_revenue']:,.0f}",
            'details': f"{bundle_potential['estimated_bundle_conversions']:.0f} estimated bundle conversions"
        })
        
        # Top bundle opportunities
        top_bundles = bundles.head(10)
        product_names = product_info.set_index('sku')['product_name'].to_dict()
        
        for idx, row in top_bundles.iterrows():
            sku1_name = product_names.get(row['sku1'], row['sku1'])
            sku2_name = product_names.get(row['sku2'], row['sku2'])
            
            recommendations.append({
                'type': 'create_bundle',
                'priority': 'medium',
                'action': f"Bundle: {sku1_name} + {sku2_name}",
                'impact': f"{row['correlation']:.1%} view correlation - {row['co_views']} co-views",
                'details': f"SKUs {row['sku1']} and {row['sku2']} - Combined revenue: ${row['combined_revenue']:,.0f}"
            })
        
        return recommendations

