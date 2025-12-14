"""Generate sample data for testing and demonstration"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

def generate_sample_sales_data(num_skus: int = 100, days: int = 90) -> pd.DataFrame:
    """Generate sample sales data"""
    np.random.seed(42)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    dates = pd.date_range(start_date, end_date, freq='D')
    skus = [f"SKU-{i:04d}" for i in range(1, num_skus + 1)]
    
    sales_data = []
    
    for date in dates:
        # Random number of sales per day
        num_sales = np.random.poisson(50)
        
        for _ in range(num_sales):
            sku = np.random.choice(skus)
            units = np.random.randint(1, 5)
            price = np.random.uniform(10, 200)
            revenue = price * units
            
            # Fees (2.9% + $0.30)
            fees = revenue * 0.029 + 0.30
            shipping_cost = np.random.uniform(3, 15)
            returns = 0 if np.random.random() > 0.05 else 1  # 5% return rate
            
            sales_data.append({
                'sku': sku,
                'date': date,
                'revenue': revenue,
                'units': units,
                'fees': fees,
                'shipping_cost': shipping_cost,
                'returns': returns
            })
    
    return pd.DataFrame(sales_data)

def generate_sample_inventory_data(num_skus: int = 100) -> pd.DataFrame:
    """Generate sample inventory data"""
    np.random.seed(42)
    
    skus = [f"SKU-{i:04d}" for i in range(1, num_skus + 1)]
    
    inventory_data = []
    
    for sku in skus:
        quantity = np.random.randint(0, 500)
        cost_per_unit = np.random.uniform(5, 100)
        
        # Calculate days of supply (rough estimate)
        days_of_supply = np.random.uniform(30, 200) if quantity > 0 else 0
        
        inventory_data.append({
            'sku': sku,
            'quantity_on_hand': quantity,
            'cost_per_unit': cost_per_unit,
            'days_of_supply': days_of_supply
        })
    
    return pd.DataFrame(inventory_data)

def generate_sample_product_info(num_skus: int = 100) -> pd.DataFrame:
    """Generate sample product information"""
    np.random.seed(42)
    
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys']
    
    skus = [f"SKU-{i:04d}" for i in range(1, num_skus + 1)]
    
    product_info = []
    
    for i, sku in enumerate(skus):
        # Some products are newer
        days_ago = np.random.exponential(180)  # Exponential distribution
        launch_date = datetime.now() - timedelta(days=days_ago)
        
        product_info.append({
            'sku': sku,
            'product_name': f"Product {i+1}",
            'category': np.random.choice(categories),
            'launch_date': launch_date,
            'price': np.random.uniform(10, 200)
        })
    
    return pd.DataFrame(product_info)

def generate_sample_product_views(num_skus: int = 100, days: int = 90) -> pd.DataFrame:
    """Generate sample product view data"""
    np.random.seed(42)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    dates = pd.date_range(start_date, end_date, freq='D')
    skus = [f"SKU-{i:04d}" for i in range(1, num_skus + 1)]
    
    views_data = []
    
    for date in dates:
        for sku in skus:
            # Some SKUs get more views
            base_views = np.random.poisson(10)
            views = max(0, base_views + np.random.randint(-5, 20))
            sessions = int(views * 0.7)  # ~70% session rate
            unique_visitors = int(sessions * 0.8)  # ~80% unique visitor rate
            
            if views > 0:
                views_data.append({
                    'sku': sku,
                    'date': date,
                    'views': views,
                    'sessions': sessions,
                    'unique_visitors': unique_visitors,
                    'session_id': f"{date.strftime('%Y%m%d')}_{np.random.randint(1000, 9999)}"
                })
    
    return pd.DataFrame(views_data)

def generate_sample_customer_overlap(num_skus: int = 100, days: int = 90) -> pd.DataFrame:
    """Generate sample customer overlap data"""
    np.random.seed(42)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    dates = pd.date_range(start_date, end_date, freq='D')
    skus = [f"SKU-{i:04d}" for i in range(1, num_skus + 1)]
    
    overlap_data = []
    customer_id_counter = 1
    
    for date in dates:
        # Random number of customers per day
        num_customers = np.random.poisson(30)
        
        for _ in range(num_customers):
            customer_id = f"CUST-{customer_id_counter:06d}"
            customer_id_counter += 1
            
            # Each customer buys 1-3 products
            num_purchases = np.random.randint(1, 4)
            purchased_skus = np.random.choice(skus, size=num_purchases, replace=False)
            
            for sku in purchased_skus:
                overlap_data.append({
                    'customer_id': customer_id,
                    'sku': sku,
                    'purchase_date': date
                })
    
    return pd.DataFrame(overlap_data)

def generate_all_sample_data(num_skus: int = 100, days: int = 90) -> Dict:
    """Generate all sample data for testing"""
    return {
        'sales_data': generate_sample_sales_data(num_skus, days),
        'inventory_data': generate_sample_inventory_data(num_skus),
        'product_info': generate_sample_product_info(num_skus),
        'product_views': generate_sample_product_views(num_skus, days),
        'customer_overlap': generate_sample_customer_overlap(num_skus, days)
    }

