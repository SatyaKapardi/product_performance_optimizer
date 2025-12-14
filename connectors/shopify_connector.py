"""Shopify Admin API connector"""
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from connectors.base_connector import BaseConnector

class ShopifyConnector(BaseConnector):
    """Connector for Shopify Admin API"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.shop_name = config.get('SHOPIFY_SHOP_NAME')
        self.access_token = config.get('SHOPIFY_ACCESS_TOKEN')
        self.base_url = f"https://{self.shop_name}.myshopify.com/admin/api/2024-01"
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request to Shopify"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching from Shopify: {e}")
            return {}
    
    def fetch_sales_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch sales data from Shopify Orders API"""
        # Fetch orders within date range
        params = {
            'created_at_min': start_date.isoformat(),
            'created_at_max': end_date.isoformat(),
            'status': 'any',
            'limit': 250
        }
        
        orders_data = []
        page_info = None
        
        while True:
            if page_info:
                params['page_info'] = page_info
            
            response = self._make_request('orders.json', params)
            orders = response.get('orders', [])
            
            if not orders:
                break
            
            for order in orders:
                for line_item in order.get('line_items', []):
                    # Calculate fees (transaction fees ~2.9% + $0.30)
                    revenue = float(line_item.get('price', 0)) * int(line_item.get('quantity', 0))
                    fees = revenue * 0.029 + 0.30
                    shipping_cost = float(order.get('total_shipping_price_set', {}).get('shop_money', {}).get('amount', 0))
                    
                    orders_data.append({
                        'sku': line_item.get('sku', ''),
                        'date': order.get('created_at', ''),
                        'revenue': revenue,
                        'units': int(line_item.get('quantity', 0)),
                        'fees': fees,
                        'shipping_cost': shipping_cost / len(order.get('line_items', [1])),
                        'returns': 0  # Would need to check refunds API
                    })
            
            # Check for pagination
            link_header = response.headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break
            
            # Extract page_info from Link header
            # Simplified - in production, parse Link header properly
            page_info = None  # Extract from Link header
        
        df = pd.DataFrame(orders_data)
        return self.normalize_data(df, 'sales')
    
    def fetch_inventory_data(self) -> pd.DataFrame:
        """Fetch inventory data from Shopify Inventory API"""
        response = self._make_request('inventory_levels.json')
        inventory_levels = response.get('inventory_levels', [])
        
        inventory_data = []
        for level in inventory_levels:
            # Fetch product details for cost
            location_id = level.get('location_id')
            inventory_item_id = level.get('inventory_item_id')
            
            inventory_data.append({
                'sku': level.get('sku', ''),
                'quantity_on_hand': int(level.get('available', 0)),
                'cost_per_unit': 0,  # Would need to fetch from product variants
                'days_of_supply': None
            })
        
        df = pd.DataFrame(inventory_data)
        return self.normalize_data(df, 'inventory')
    
    def fetch_product_views(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch product view data from Shopify Analytics API"""
        # Shopify Analytics API requires different authentication
        # For now, use Google Analytics integration or Shopify Reports API
        
        # Placeholder - would use Analytics API or GA4 integration
        data = {
            'sku': [],
            'date': [],
            'views': [],
            'sessions': [],
            'unique_visitors': []
        }
        
        df = pd.DataFrame(data)
        return self.normalize_data(df, 'views')
    
    def fetch_customer_overlap(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch customer purchase patterns"""
        params = {
            'created_at_min': start_date.isoformat(),
            'created_at_max': end_date.isoformat(),
            'limit': 250
        }
        
        overlap_data = []
        response = self._make_request('orders.json', params)
        orders = response.get('orders', [])
        
        for order in orders:
            customer_id = order.get('customer', {}).get('id', f"guest_{order.get('id')}")
            for line_item in order.get('line_items', []):
                overlap_data.append({
                    'customer_id': str(customer_id),
                    'sku': line_item.get('sku', ''),
                    'purchase_date': order.get('created_at', '')
                })
        
        df = pd.DataFrame(overlap_data)
        return self.normalize_data(df, 'overlap')
    
    def fetch_product_info(self) -> pd.DataFrame:
        """Fetch product metadata"""
        products_data = []
        page_info = None
        
        while True:
            params = {'limit': 250}
            if page_info:
                params['page_info'] = page_info
            
            response = self._make_request('products.json', params)
            products = response.get('products', [])
            
            if not products:
                break
            
            for product in products:
                for variant in product.get('variants', []):
                    products_data.append({
                        'sku': variant.get('sku', ''),
                        'product_name': product.get('title', ''),
                        'category': ', '.join([tag for tag in product.get('tags', [])]),
                        'launch_date': product.get('created_at', ''),
                        'price': float(variant.get('price', 0))
                    })
            
            link_header = response.headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break
            
            page_info = None
        
        df = pd.DataFrame(products_data)
        return self.normalize_data(df, 'product_info')

