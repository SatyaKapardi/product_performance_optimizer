"""Base connector class for all platform connectors"""
from abc import ABC, abstractmethod
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class BaseConnector(ABC):
    """Base class for all e-commerce platform connectors"""
    
    def __init__(self, config: dict):
        self.config = config
        self.platform_name = self.__class__.__name__.replace('Connector', '').lower()
    
    @abstractmethod
    def fetch_sales_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch sales data for all SKUs
        
        Returns DataFrame with columns:
        - sku: Product SKU
        - date: Sale date
        - revenue: Revenue from sale
        - units: Units sold
        - fees: Platform fees
        - shipping_cost: Shipping cost
        - returns: Return count/value
        """
        pass
    
    @abstractmethod
    def fetch_inventory_data(self) -> pd.DataFrame:
        """
        Fetch current inventory levels
        
        Returns DataFrame with columns:
        - sku: Product SKU
        - quantity_on_hand: Current inventory
        - cost_per_unit: Cost per unit
        - days_of_supply: Days of supply (if available)
        """
        pass
    
    @abstractmethod
    def fetch_product_views(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch product view/session data
        
        Returns DataFrame with columns:
        - sku: Product SKU
        - date: View date
        - views: Number of views
        - sessions: Number of sessions
        - unique_visitors: Unique visitors
        """
        pass
    
    @abstractmethod
    def fetch_customer_overlap(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch customer purchase patterns for cannibalization analysis
        
        Returns DataFrame with columns:
        - customer_id: Customer identifier
        - sku: Product SKU
        - purchase_date: Purchase date
        """
        pass
    
    @abstractmethod
    def fetch_product_info(self) -> pd.DataFrame:
        """
        Fetch product metadata
        
        Returns DataFrame with columns:
        - sku: Product SKU
        - product_name: Product name
        - category: Product category
        - launch_date: Product launch date
        - price: Current price
        """
        pass
    
    def normalize_data(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Normalize data format across platforms"""
        if df.empty:
            return df
        
        # Ensure date columns are datetime
        date_columns = ['date', 'purchase_date', 'launch_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Ensure numeric columns are numeric
        numeric_columns = ['revenue', 'units', 'fees', 'shipping_cost', 'returns', 
                          'quantity_on_hand', 'cost_per_unit', 'views', 'sessions', 
                          'unique_visitors', 'price']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df

