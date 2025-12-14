"""Configuration settings for the Product Performance Optimizer"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Amazon Configuration
    AMAZON_SELLER_ID = os.getenv('AMAZON_SELLER_ID', '')
    AMAZON_ACCESS_KEY = os.getenv('AMAZON_ACCESS_KEY', '')
    AMAZON_SECRET_KEY = os.getenv('AMAZON_SECRET_KEY', '')
    AMAZON_MARKETPLACE_ID = os.getenv('AMAZON_MARKETPLACE_ID', '')
    
    # Shopify Configuration
    SHOPIFY_SHOP_NAME = os.getenv('SHOPIFY_SHOP_NAME', '')
    SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY', '')
    SHOPIFY_API_SECRET = os.getenv('SHOPIFY_API_SECRET', '')
    SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    
    # WooCommerce Configuration
    WOOCOMMERCE_URL = os.getenv('WOOCOMMERCE_URL', '')
    WOOCOMMERCE_CONSUMER_KEY = os.getenv('WOOCOMMERCE_CONSUMER_KEY', '')
    WOOCOMMERCE_CONSUMER_SECRET = os.getenv('WOOCOMMERCE_CONSUMER_SECRET', '')
    
    # Google Analytics 4 Configuration
    GA4_PROPERTY_ID = os.getenv('GA4_PROPERTY_ID', '')
    GA4_CREDENTIALS_PATH = os.getenv('GA4_CREDENTIALS_PATH', '')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///sku_analytics.db')
    
    # Analysis Parameters
    ZOMBIE_THRESHOLD_PERCENTILE = 20  # Bottom 20% for zombie products
    SLOW_MOVER_DAYS_THRESHOLD = 180  # Days of inventory threshold
    CANNIBALIZATION_OVERLAP_THRESHOLD = 0.85  # 85% customer overlap
    NEW_PRODUCT_DAYS = [30, 60, 90]  # Analysis windows for new products
    BUNDLE_CORRELATION_THRESHOLD = 0.70  # 70% view correlation for bundles

