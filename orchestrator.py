"""Main orchestrator that runs all analyses and generates reports"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config

from connectors.amazon_connector import AmazonConnector
from connectors.shopify_connector import ShopifyConnector
from connectors.woocommerce_connector import WooCommerceConnector
from connectors.demo_connector import DemoConnector

from analyzers.sku_rationalization import SKURationalizationAnalyzer
from analyzers.contribution_margin import ContributionMarginAnalyzer
from analyzers.slow_mover_detection import SlowMoverAnalyzer
from analyzers.cannibalization import CannibalizationAnalyzer
from analyzers.new_product_scoring import NewProductScoringAnalyzer
from analyzers.bundle_finder import BundleFinderAnalyzer

class PerformanceOptimizer:
    """Main orchestrator for product performance analysis"""
    
    def __init__(self, platform: str = 'amazon'):
        """
        Initialize optimizer for a specific platform
        
        Args:
            platform: 'amazon', 'shopify', or 'woocommerce'
        """
        self.platform = platform.lower()
        self.connector = self._get_connector()
        
        # Initialize analyzers
        self.sku_rationalizer = SKURationalizationAnalyzer(
            threshold_percentile=config.Config.ZOMBIE_THRESHOLD_PERCENTILE
        )
        self.margin_analyzer = ContributionMarginAnalyzer()
        self.slow_mover_analyzer = SlowMoverAnalyzer(
            days_threshold=config.Config.SLOW_MOVER_DAYS_THRESHOLD
        )
        self.cannibalization_analyzer = CannibalizationAnalyzer(
            overlap_threshold=config.Config.CANNIBALIZATION_OVERLAP_THRESHOLD
        )
        self.new_product_analyzer = NewProductScoringAnalyzer(
            analysis_windows=config.Config.NEW_PRODUCT_DAYS
        )
        self.bundle_finder = BundleFinderAnalyzer(
            correlation_threshold=config.Config.BUNDLE_CORRELATION_THRESHOLD
        )
    
    def _get_connector(self):
        """Get connector for the specified platform"""
        config_dict = {
            'AMAZON_SELLER_ID': config.Config.AMAZON_SELLER_ID,
            'AMAZON_ACCESS_KEY': config.Config.AMAZON_ACCESS_KEY,
            'AMAZON_SECRET_KEY': config.Config.AMAZON_SECRET_KEY,
            'AMAZON_MARKETPLACE_ID': config.Config.AMAZON_MARKETPLACE_ID,
            'SHOPIFY_SHOP_NAME': config.Config.SHOPIFY_SHOP_NAME,
            'SHOPIFY_ACCESS_TOKEN': config.Config.SHOPIFY_ACCESS_TOKEN,
            'WOOCOMMERCE_URL': config.Config.WOOCOMMERCE_URL,
            'WOOCOMMERCE_CONSUMER_KEY': config.Config.WOOCOMMERCE_CONSUMER_KEY,
            'WOOCOMMERCE_CONSUMER_SECRET': config.Config.WOOCOMMERCE_CONSUMER_SECRET
        }
        
        if self.platform == 'amazon':
            return AmazonConnector(config_dict)
        elif self.platform == 'shopify':
            return ShopifyConnector(config_dict)
        elif self.platform == 'woocommerce':
            return WooCommerceConnector(config_dict)
        elif self.platform == 'demo':
            return DemoConnector(config_dict)
        else:
            raise ValueError(f"Unsupported platform: {self.platform}")
    
    def run_full_analysis(self, days_back: int = 90) -> Dict:
        """
        Run complete analysis across all 6 dimensions
        
        Args:
            days_back: Number of days to analyze
        
        Returns:
            Dict with all analysis results
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        print(f"Fetching data from {self.platform}...")
        
        # Fetch all data
        sales_data = self.connector.fetch_sales_data(start_date, end_date)
        inventory_data = self.connector.fetch_inventory_data()
        product_info = self.connector.fetch_product_info()
        product_views = self.connector.fetch_product_views(start_date, end_date)
        customer_overlap = self.connector.fetch_customer_overlap(start_date, end_date)
        
        print("Running analyses...")
        
        # Run all analyses
        results = {
            'platform': self.platform,
            'analysis_date': datetime.now().isoformat(),
            'analysis_period_days': days_back,
            'sku_rationalization': self.sku_rationalizer.analyze(
                sales_data, inventory_data, product_info
            ),
            'contribution_margin': self.margin_analyzer.analyze(
                sales_data, inventory_data, product_info
            ),
            'slow_mover_detection': self.slow_mover_analyzer.analyze(
                sales_data, inventory_data, product_info, days_back
            ),
            'cannibalization': self.cannibalization_analyzer.analyze(
                customer_overlap, sales_data, product_info
            ),
            'new_product_scoring': self.new_product_analyzer.analyze(
                sales_data, product_info
            ),
            'bundle_opportunities': self.bundle_finder.analyze(
                product_views, sales_data, product_info
            )
        }
        
        # Generate consolidated recommendations
        results['consolidated_recommendations'] = self._consolidate_recommendations(results)
        
        # Generate traffic light status
        results['traffic_light_status'] = self._generate_traffic_light_status(results)
        
        return results
    
    def _consolidate_recommendations(self, results: Dict) -> List[Dict]:
        """Consolidate recommendations from all analyses"""
        all_recommendations = []
        
        # Collect recommendations from each analysis
        for analysis_name, analysis_result in results.items():
            if isinstance(analysis_result, dict) and 'recommendations' in analysis_result:
                for rec in analysis_result['recommendations']:
                    rec['source_analysis'] = analysis_name
                    all_recommendations.append(rec)
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        all_recommendations.sort(
            key=lambda x: priority_order.get(x.get('priority', 'low'), 3)
        )
        
        return all_recommendations
    
    def _generate_traffic_light_status(self, results: Dict) -> Dict:
        """Generate traffic light status for all SKUs"""
        # Get all unique SKUs
        all_skus = set()
        
        for analysis_name, analysis_result in results.items():
            if isinstance(analysis_result, dict):
                for key, value in analysis_result.items():
                    if isinstance(value, pd.DataFrame) and 'sku' in value.columns:
                        all_skus.update(value['sku'].unique())
        
        # Initialize status for each SKU
        status_map = {}
        
        for sku in all_skus:
            status_map[sku] = {
                'sku': sku,
                'status': 'green',  # Default to green
                'issues': [],
                'recommendations': []
            }
        
        # Apply status from each analysis
        # Red: Zombie products, money losers, critical slow movers
        if 'sku_rationalization' in results:
            zombies = results['sku_rationalization'].get('zombie_skus', pd.DataFrame())
            for _, row in zombies.iterrows():
                if row['sku'] in status_map:
                    status_map[row['sku']]['status'] = 'red'
                    status_map[row['sku']]['issues'].append('Zombie product')
        
        if 'contribution_margin' in results:
            losers = results['contribution_margin'].get('money_losers', pd.DataFrame())
            for _, row in losers.iterrows():
                if row['sku'] in status_map:
                    if status_map[row['sku']]['status'] != 'red':
                        status_map[row['sku']]['status'] = 'yellow'
                    status_map[row['sku']]['issues'].append('Losing money')
        
        if 'slow_mover_detection' in results:
            slow_movers = results['slow_mover_detection'].get('slow_movers', pd.DataFrame())
            critical = slow_movers[slow_movers.get('urgency', '') == 'critical']
            for _, row in critical.iterrows():
                if row['sku'] in status_map:
                    status_map[row['sku']]['status'] = 'red'
                    status_map[row['sku']]['issues'].append('Critical slow mover')
        
        # Yellow: Underperforming new products, medium priority issues
        if 'new_product_scoring' in results:
            underperformers = results['new_product_scoring'].get('underperformers', pd.DataFrame())
            for _, row in underperformers.iterrows():
                if row['sku'] in status_map and status_map[row['sku']]['status'] == 'green':
                    status_map[row['sku']]['status'] = 'yellow'
                    status_map[row['sku']]['issues'].append('Underperforming new product')
        
        # Add recommendations
        for rec in results.get('consolidated_recommendations', []):
            if 'sku' in rec.get('action', '').lower():
                # Try to extract SKU from recommendation
                action = rec.get('action', '')
                # Simple extraction - in production, use better parsing
                for sku in all_skus:
                    if sku in action:
                        status_map[sku]['recommendations'].append(rec)
        
        return status_map
    
    def generate_summary_report(self, results: Dict) -> Dict:
        """Generate executive summary report"""
        summary = {
            'analysis_date': results.get('analysis_date'),
            'platform': results.get('platform'),
            'key_metrics': {},
            'top_recommendations': results.get('consolidated_recommendations', [])[:10],
            'financial_impact': {}
        }
        
        # Key metrics
        sku_rational = results.get('sku_rationalization', {})
        summary['key_metrics']['zombie_products'] = sku_rational.get('summary', {}).get('total_zombies', 0)
        summary['key_metrics']['capital_freed'] = sku_rational.get('financial_impact', {}).get('working_capital_freed', 0)
        
        margin = results.get('contribution_margin', {})
        summary['key_metrics']['profitable_skus'] = margin.get('summary', {}).get('profitable_skus', 0)
        summary['key_metrics']['losing_skus'] = margin.get('summary', {}).get('losing_skus', 0)
        
        slow_mover = results.get('slow_mover_detection', {})
        summary['key_metrics']['slow_movers'] = slow_mover.get('summary', {}).get('slow_movers_count', 0)
        
        cannibal = results.get('cannibalization', {})
        summary['key_metrics']['cannibalization_pairs'] = cannibal.get('summary', {}).get('cannibalization_pairs_count', 0)
        
        new_product = results.get('new_product_scoring', {})
        summary['key_metrics']['new_products'] = new_product.get('summary', {}).get('new_products_count', 0)
        summary['key_metrics']['underperforming_new'] = new_product.get('summary', {}).get('underperformers_count', 0)
        
        bundles = results.get('bundle_opportunities', {})
        summary['key_metrics']['bundle_opportunities'] = bundles.get('summary', {}).get('opportunities_count', 0)
        
        # Financial impact
        summary['financial_impact'] = {
            'working_capital_freed': sku_rational.get('financial_impact', {}).get('working_capital_freed', 0),
            'potential_bundle_revenue': bundles.get('bundle_potential', {}).get('total_potential_revenue', 0),
            'total_profit': margin.get('summary', {}).get('total_profit', 0)
        }
        
        return summary

