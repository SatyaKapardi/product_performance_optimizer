"""Demo connector that uses sample data for testing"""
from connectors.base_connector import BaseConnector
from utils.sample_data_generator import generate_all_sample_data
import pandas as pd

class DemoConnector(BaseConnector):
    """Demo connector using generated sample data"""
    
    def __init__(self, config: dict = None):
        super().__init__(config or {})
        self.sample_data = generate_all_sample_data(num_skus=100, days=90)
    
    def fetch_sales_data(self, start_date, end_date):
        """Return sample sales data"""
        df = self.sample_data['sales_data'].copy()
        df['date'] = pd.to_datetime(df['date'])
        # Filter by date range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        return self.normalize_data(df, 'sales')
    
    def fetch_inventory_data(self):
        """Return sample inventory data"""
        return self.normalize_data(self.sample_data['inventory_data'].copy(), 'inventory')
    
    def fetch_product_views(self, start_date, end_date):
        """Return sample product views"""
        df = self.sample_data['product_views'].copy()
        df['date'] = pd.to_datetime(df['date'])
        # Filter by date range
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        return self.normalize_data(df, 'views')
    
    def fetch_customer_overlap(self, start_date, end_date):
        """Return sample customer overlap data"""
        df = self.sample_data['customer_overlap'].copy()
        df['purchase_date'] = pd.to_datetime(df['purchase_date'])
        # Filter by date range
        df = df[(df['purchase_date'] >= start_date) & (df['purchase_date'] <= end_date)]
        return self.normalize_data(df, 'overlap')
    
    def fetch_product_info(self):
        """Return sample product info"""
        return self.normalize_data(self.sample_data['product_info'].copy(), 'product_info')

