"""WooCommerce REST API connector"""
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from connectors.base_connector import BaseConnector
from woocommerce import API

class WooCommerceConnector(BaseConnector):
    """Connector for WooCommerce REST API"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.url = config.get('WOOCOMMERCE_URL')
        self.consumer_key = config.get('WOOCOMMERCE_CONSUMER_KEY')
        self.consumer_secret = config.get('WOOCOMMERCE_CONSUMER_SECRET')
        
        self.wcapi = API(
            url=self.url,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            version="wc/v3",
            timeout=30
        )
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """Make API request to WooCommerce"""
        try:
            response = self.wcapi.get(endpoint, params=params or {})
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching from WooCommerce: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error fetching from WooCommerce: {e}")
            return {}
    
    def fetch_sales_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch sales data from WooCommerce Orders API"""
        params = {
            'after': start_date.isoformat(),
            'before': end_date.isoformat(),
            'per_page': 100,
            'status': 'completed'
        }
        
        orders_data = []
        page = 1
        
        while True:
            params['page'] = page
            orders = self._make_request('orders', params)
            
            if not orders:
                break
            
            for order in orders:
                for line_item in order.get('line_items', []):
                    # Calculate fees (payment gateway fees ~2.9% + $0.30)
                    revenue = float(line_item.get('total', 0))
                    fees = revenue * 0.029 + 0.30
                    shipping_cost = float(order.get('shipping_total', 0))
                    
                    orders_data.append({
                        'sku': line_item.get('sku', ''),
                        'date': order.get('date_created', ''),
                        'revenue': revenue,
                        'units': int(line_item.get('quantity', 0)),
                        'fees': fees,
                        'shipping_cost': shipping_cost / len(order.get('line_items', [1])),
                        'returns': 0  # Would need to check refunds
                    })
            
            if len(orders) < params['per_page']:
                break
            
            page += 1
        
        df = pd.DataFrame(orders_data)
        return self.normalize_data(df, 'sales')
    
    def fetch_inventory_data(self) -> pd.DataFrame:
        """Fetch inventory data from WooCommerce Products API"""
        inventory_data = []
        page = 1
        
        while True:
            products = self._make_request('products', {'per_page': 100, 'page': page})
            
            if not products:
                break
            
            for product in products:
                for variation in product.get('variations', []):
                    # Fetch variation details
                    variation_data = self._make_request(f"products/{product['id']}/variations/{variation}")
                    if variation_data:
                        inventory_data.append({
                            'sku': variation_data.get('sku', ''),
                            'quantity_on_hand': int(variation_data.get('stock_quantity', 0)),
                            'cost_per_unit': float(variation_data.get('regular_price', 0)),
                            'days_of_supply': None
                        })
                else:
                    # Simple product without variations
                    inventory_data.append({
                        'sku': product.get('sku', ''),
                        'quantity_on_hand': int(product.get('stock_quantity', 0)),
                        'cost_per_unit': float(product.get('regular_price', 0)),
                        'days_of_supply': None
                    })
            
            if len(products) < 100:
                break
            
            page += 1
        
        df = pd.DataFrame(inventory_data)
        return self.normalize_data(df, 'inventory')
    
    def fetch_product_views(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch product view data"""
        # WooCommerce doesn't have built-in analytics API
        # Would need Google Analytics integration or custom tracking
        # Placeholder structure
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
            'after': start_date.isoformat(),
            'before': end_date.isoformat(),
            'per_page': 100
        }
        
        overlap_data = []
        page = 1
        
        while True:
            params['page'] = page
            orders = self._make_request('orders', params)
            
            if not orders:
                break
            
            for order in orders:
                customer_id = order.get('customer_id', f"guest_{order.get('id')}")
                for line_item in order.get('line_items', []):
                    overlap_data.append({
                        'customer_id': str(customer_id),
                        'sku': line_item.get('sku', ''),
                        'purchase_date': order.get('date_created', '')
                    })
            
            if len(orders) < params['per_page']:
                break
            
            page += 1
        
        df = pd.DataFrame(overlap_data)
        return self.normalize_data(df, 'overlap')
    
    def fetch_product_info(self) -> pd.DataFrame:
        """Fetch product metadata"""
        products_data = []
        page = 1
        
        while True:
            products = self._make_request('products', {'per_page': 100, 'page': page})
            
            if not products:
                break
            
            for product in products:
                for variation in product.get('variations', []):
                    variation_data = self._make_request(f"products/{product['id']}/variations/{variation}")
                    if variation_data:
                        products_data.append({
                            'sku': variation_data.get('sku', ''),
                            'product_name': product.get('name', ''),
                            'category': ', '.join([cat.get('name', '') for cat in product.get('categories', [])]),
                            'launch_date': product.get('date_created', ''),
                            'price': float(variation_data.get('regular_price', 0))
                        })
                else:
                    products_data.append({
                        'sku': product.get('sku', ''),
                        'product_name': product.get('name', ''),
                        'category': ', '.join([cat.get('name', '') for cat in product.get('categories', [])]),
                        'launch_date': product.get('date_created', ''),
                        'price': float(product.get('regular_price', 0))
                    })
            
            if len(products) < 100:
                break
            
            page += 1
        
        df = pd.DataFrame(products_data)
        return self.normalize_data(df, 'product_info')

