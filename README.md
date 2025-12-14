# Product Performance & Assortment Optimizer

A comprehensive analytics tool that analyzes SKUs across 6 dimensions to provide actionable recommendations for retailers selling on Amazon, Shopify, and WordPress/WooCommerce.

## What is This Project?

Retailers carry hundreds to thousands of SKUs but often don't know which ones actually drive profit versus which ones drain resources. This tool solves that problem by analyzing every SKU across 6 key dimensions and providing data-driven recommendations.

### Core Problem

Retailers make gut decisions on what to discontinue, promote, or reorder without understanding the true financial impact. This leads to:
- Carrying zombie products that tie up capital
- Losing money on "bestsellers" after fees and costs
- Missing bundle opportunities
- Cannibalizing sales between similar products

### Solution

This optimizer analyzes your entire product catalog and provides:
- Traffic light status for every SKU (Green/Yellow/Red)
- Actionable recommendations with financial impact
- Working capital calculations
- Profit optimization strategies

## Features

### 1. SKU Rationalization
Identifies "zombie products" (low revenue, low profit, slow-moving) and flags bottom 20% of SKUs to discontinue. Calculates working capital that can be freed up.

### 2. Contribution Margin Ranking
Sorts products by TRUE profit after Amazon fees, shipping costs, and returns. Shows where you're losing money on "bestsellers" that appear profitable but aren't.

### 3. Slow Mover Detection
Calculates inventory turnover (days of supply on hand) and alerts when products have excessive inventory. Example: "SKU X has 180 days of inventory at current velocity → markdown now"

### 4. Cannibalization Analysis
Detects products stealing sales from each other based on customer overlap patterns. Example: "Product A and B have 85% customer overlap → kill one or differentiate"

### 5. New Product Success Scoring
Compares new launches to historical winners (first 30/60/90 day velocity). Provides early warning: "This launch is underperforming - increase marketing or cut losses"

### 6. Bundle Opportunity Finder
Uses product view correlation to identify bundle opportunities. Example: "70% of customers who view Product A also view Product B → create bundle"

## Demo & Sample Results

### Dashboard Overview

The dashboard provides a comprehensive view of your product performance with actionable insights:

**Traffic Light Status:**
- **Red (Cut)**: 28 products recommended for discontinuation
- **Yellow (Watch)**: 17 products needing attention
- **Green (Winners)**: 55 products performing well

**Summary Metrics:**
- **Zombie Products**: 20 SKUs identified, freeing $243,223 in working capital
- **Money Losers**: 9 SKUs losing money, totaling $7,682 in losses
- **Slow Movers**: 48 SKUs with excessive inventory, totaling $810,864 in value
- **Bundle Opportunities**: Potential bundles identified with revenue opportunities

### Sample Data Analysis

The dashboard displays detailed product information including:
- SKU identifiers
- Product names and categories
- Launch dates and days since launch
- Revenue and units sold (30/60/90 day windows)
- Pricing information
- Performance scores

Example product data shown:
- **SKU-0001**: Product 1 (Books category)
  - Launch Date: September 2025
  - Days Since Launch: 84
  - 30-Day Revenue: $2,618.54
  - 30-Day Units: 33
  - Performance Score: 0.58

### Key Features Demonstrated

1. **Visual Traffic Light System**: Quick identification of product health
2. **Financial Impact Cards**: Immediate visibility into capital tied up and losses
3. **Detailed Analysis Tabs**: Deep dive into each analysis dimension
4. **Actionable Recommendations**: Prioritized list of actions with financial impact
5. **Interactive Tables**: Sortable, filterable product data with highlighting

### Key Outputs

**Dashboard Features:**
- Traffic-light system (green=winners, yellow=watch, red=cut)
- Summary cards with key financial metrics
- Detailed tables for each analysis module
- Consolidated recommendations list sorted by priority

**Recommendations Include:**
- "Discontinue 23 SKUs → free $87K capital"
- "Focus on top 30 SKUs → +$142K annual profit"
- "SKU X has 180 days of inventory → markdown now"
- "Create bundle: Product A + Product B (70% view correlation)"

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure platform credentials (optional for demo mode):**

Create a `.env` file in the project root (you can copy from `.env.example` if it exists):
```bash
# Amazon API Credentials
AMAZON_SELLER_ID=your_seller_id
AMAZON_ACCESS_KEY=your_access_key
AMAZON_SECRET_KEY=your_secret_key
AMAZON_MARKETPLACE_ID=your_marketplace_id

# Shopify API Credentials
SHOPIFY_SHOP_NAME=your_shop_name
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_ACCESS_TOKEN=your_access_token

# WooCommerce API Credentials
WOOCOMMERCE_URL=https://your-site.com
WOOCOMMERCE_CONSUMER_KEY=your_consumer_key
WOOCOMMERCE_CONSUMER_SECRET=your_consumer_secret
```

### Running the Application

#### Option 1: Demo Mode (No API Credentials Required)

1. **Start the application:**
```bash
python app.py
```

2. **Open your browser** to the URL shown in the terminal (typically `http://localhost:8050` or `http://localhost:8051`)

3. **In the dashboard:**
   - Select "Demo (Sample Data)" from the platform dropdown
   - Adjust the analysis period slider (default: 90 days)
   - Click "Run Analysis"
   - Wait a few seconds for the analysis to complete
   - Explore the results in different tabs

#### Option 2: With Real Platform Data

1. **Configure your `.env` file** with your platform API credentials (see above)

2. **Start the application:**
```bash
python app.py
```

3. **In the dashboard:**
   - Select your platform (Amazon, Shopify, or WooCommerce)
   - Adjust the analysis period
   - Click "Run Analysis"

### Platform-Specific Setup

#### Amazon
- Requires Seller Central account
- SP-API credentials and Marketplace ID
- Note: Current implementation is a skeleton - requires proper AWS signature generation for production use

#### Shopify
- Requires Shopify store
- Admin API access token
- Create an app in Shopify admin with read permissions for:
  - Orders
  - Products
  - Inventory

#### WooCommerce
- Requires WordPress site with WooCommerce installed
- REST API consumer key and secret
- Generate credentials in: WooCommerce → Settings → Advanced → REST API

## Using the Dashboard

### Navigation
- **Platform Selector**: Choose your data source (Demo, Amazon, Shopify, WooCommerce)
- **Analysis Period Slider**: Set the number of days to analyze (30-365 days)
- **Run Analysis Button**: Execute the full analysis

### Analysis Tabs
1. **SKU Rationalization**: View all products with zombies highlighted in red
2. **Contribution Margin**: See products ranked by true profit
3. **Slow Movers**: Identify products with excessive inventory
4. **Cannibalization**: Find products with high customer overlap
5. **New Products**: Compare new launches to historical benchmarks
6. **Bundle Opportunities**: Discover products frequently viewed together
7. **Recommendations**: Consolidated list of all actionable insights

### Understanding Results

**Traffic Light System:**
- **Green (Winners)**: Profitable, fast-moving products - prioritize these
- **Yellow (Watch)**: Products needing attention - review pricing, marketing, or costs
- **Red (Cut)**: Zombie products, money losers, critical slow movers - consider discontinuing

**Financial Impact:**
- Working capital calculations show how much money is tied up in slow inventory
- Profit/loss figures show true contribution margin after all costs
- Bundle potential estimates additional revenue opportunities

## Troubleshooting

### Port Already in Use
If you see "Port 8050 is in use", the application will automatically try the next available port. Check the terminal output for the actual port number.

### No Data Showing
- Verify API credentials are correct (for real platform data)
- Check API permissions for your platform
- Try demo mode first to verify the application works
- Check the browser console for errors

### Analysis Takes Too Long
- Reduce the analysis period using the slider
- Check your internet connection
- For large catalogs (1000+ SKUs), consider analyzing in batches

### Connection Refused
- Make sure the application is running (check terminal)
- Use the correct port number shown in terminal output
- Try refreshing your browser

## Project Structure

```
prod performance optimizer/
├── app.py                      # Main application entry point
├── dashboard.py                # Dash web dashboard
├── orchestrator.py             # Main analysis orchestrator
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── connectors/                 # Platform connectors
│   ├── base_connector.py      # Base connector class
│   ├── amazon_connector.py    # Amazon SP-API connector
│   ├── shopify_connector.py   # Shopify Admin API connector
│   ├── woocommerce_connector.py # WooCommerce REST API connector
│   └── demo_connector.py      # Demo connector with sample data
│
├── analyzers/                  # Analysis modules
│   ├── sku_rationalization.py      # Module 1: Zombie product detection
│   ├── contribution_margin.py      # Module 2: True profit ranking
│   ├── slow_mover_detection.py     # Module 3: Inventory turnover analysis
│   ├── cannibalization.py           # Module 4: Customer overlap analysis
│   ├── new_product_scoring.py       # Module 5: New product benchmarking
│   └── bundle_finder.py             # Module 6: Bundle opportunity detection
│
└── utils/                      # Utility functions
    └── sample_data_generator.py    # Generate sample data for testing
```

## Data Requirements

The tool analyzes the following data points:

**Sales Data:**
- Revenue by SKU
- Units sold
- Platform fees
- Shipping costs
- Returns

**Inventory Data:**
- Quantity on hand
- Cost per unit
- Days of supply

**Product Information:**
- Product names
- Categories
- Launch dates
- Current prices

**Customer Data (for cannibalization analysis):**
- Customer purchase patterns
- Product view correlations

## Next Steps

1. **Run Demo Analysis**: Start with demo mode to understand the tool
2. **Configure Your Platform**: Set up API credentials for your e-commerce platform
3. **Run Analysis**: Execute analysis on your real product data
4. **Review Recommendations**: Focus on high-priority recommendations first
5. **Take Action**: Discontinue zombies, optimize pricing, create bundles
6. **Track Progress**: Run regular analyses to track improvements

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review the terminal output for error messages
- Verify your API credentials and permissions

## License

This project is provided as-is for analysis and optimization purposes.
