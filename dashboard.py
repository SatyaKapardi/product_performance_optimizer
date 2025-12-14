"""Dashboard for Product Performance Optimizer using Dash"""
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime
from orchestrator import PerformanceOptimizer
import config

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Product Performance & Assortment Optimizer", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Label("Select Platform:"),
            dcc.Dropdown(
                id='platform-selector',
                options=[
                    {'label': 'Demo (Sample Data)', 'value': 'demo'},
                    {'label': 'Amazon', 'value': 'amazon'},
                    {'label': 'Shopify', 'value': 'shopify'},
                    {'label': 'WooCommerce', 'value': 'woocommerce'}
                ],
                value='demo',
                className="mb-3"
            )
        ], width=4),
        dbc.Col([
            html.Label("Analysis Period (days):"),
            dcc.Slider(
                id='days-slider',
                min=30,
                max=365,
                step=30,
                value=90,
                marks={i: str(i) for i in range(30, 366, 60)},
                className="mb-3"
            )
        ], width=4),
        dbc.Col([
            html.Br(),
            dbc.Button("Run Analysis", id="run-button", color="primary", className="w-100")
        ], width=4)
    ]),
    
    html.Hr(),
    
    # Traffic Light Status
    dbc.Row([
        dbc.Col([
            html.H3("Traffic Light Status", className="mb-3"),
            html.Div(id="traffic-light-status")
        ])
    ]),
    
    html.Hr(),
    
    # Summary Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Zombie Products", className="card-title"),
                    html.H2(id="zombie-count", children="0"),
                    html.P(id="zombie-capital", children="")
                ])
            ], color="danger", outline=True)
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Money Losers", className="card-title"),
                    html.H2(id="loser-count", children="0"),
                    html.P(id="loser-loss", children="")
                ])
            ], color="warning", outline=True)
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Slow Movers", className="card-title"),
                    html.H2(id="slow-mover-count", children="0"),
                    html.P(id="slow-mover-value", children="")
                ])
            ], color="warning", outline=True)
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Bundle Opportunities", className="card-title"),
                    html.H2(id="bundle-count", children="0"),
                    html.P(id="bundle-potential", children="")
                ])
            ], color="success", outline=True)
        ], width=3)
    ], className="mb-4"),
    
    # Tabs for different analyses
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="SKU Rationalization", tab_id="tab-1"),
                dbc.Tab(label="Contribution Margin", tab_id="tab-2"),
                dbc.Tab(label="Slow Movers", tab_id="tab-3"),
                dbc.Tab(label="Cannibalization", tab_id="tab-4"),
                dbc.Tab(label="New Products", tab_id="tab-5"),
                dbc.Tab(label="Bundle Opportunities", tab_id="tab-6"),
                dbc.Tab(label="Recommendations", tab_id="tab-7")
            ], id="tabs", active_tab="tab-1")
        ])
    ]),
    
    html.Div(id="tab-content", className="mt-4"),
    
    # Store for analysis results
    dcc.Store(id="analysis-results")
    
], fluid=True)

@app.callback(
    Output("analysis-results", "data"),
    Input("run-button", "n_clicks"),
    Input("platform-selector", "value"),
    Input("days-slider", "value"),
    prevent_initial_call=True
)
def run_analysis(n_clicks, platform, days_back):
    """Run full analysis"""
    try:
        optimizer = PerformanceOptimizer(platform=platform)
        results = optimizer.run_full_analysis(days_back=days_back)
        
        # Convert DataFrames to dict for JSON serialization
        results_serialized = serialize_results(results)
        
        return results_serialized
    except Exception as e:
        print(f"Error running analysis: {e}")
        return {}

def serialize_results(results):
    """Convert DataFrames in results to dict format"""
    serialized = {}
    for key, value in results.items():
        if isinstance(value, pd.DataFrame):
            serialized[key] = value.to_dict('records')
        elif isinstance(value, dict):
            serialized[key] = serialize_results(value)
        else:
            serialized[key] = value
    return serialized

@app.callback(
    [Output("zombie-count", "children"),
     Output("zombie-capital", "children"),
     Output("loser-count", "children"),
     Output("loser-loss", "children"),
     Output("slow-mover-count", "children"),
     Output("slow-mover-value", "children"),
     Output("bundle-count", "children"),
     Output("bundle-potential", "children"),
     Output("traffic-light-status", "children"),
     Output("tab-content", "children")],
    [Input("analysis-results", "data"),
     Input("tabs", "active_tab")]
)
def update_dashboard(results_data, active_tab):
    """Update dashboard with analysis results"""
    try:
        if not results_data or results_data == {}:
            return ["0"] * 8 + [html.P("Click 'Run Analysis' to start"), html.Div()]
        
        # Deserialize results
        results = deserialize_results(results_data)
        
        # Update summary cards with safe defaults
        sku_rational = results.get('sku_rationalization', {})
        zombie_count = sku_rational.get('summary', {}).get('total_zombies', 0) if sku_rational else 0
        zombie_capital_val = sku_rational.get('financial_impact', {}).get('working_capital_freed', 0) if sku_rational else 0
        zombie_capital = f"${zombie_capital_val:,.0f} capital"
        
        margin = results.get('contribution_margin', {})
        loser_count = margin.get('summary', {}).get('losing_skus', 0) if margin else 0
        loser_loss_val = abs(margin.get('summary', {}).get('total_losses', 0)) if margin else 0
        loser_loss = f"${loser_loss_val:,.0f} losses"
        
        slow_mover = results.get('slow_mover_detection', {})
        slow_count = slow_mover.get('summary', {}).get('slow_movers_count', 0) if slow_mover else 0
        slow_value_val = slow_mover.get('summary', {}).get('total_slow_inventory_value', 0) if slow_mover else 0
        slow_value = f"${slow_value_val:,.0f} value"
        
        bundles = results.get('bundle_opportunities', {})
        bundle_count = bundles.get('summary', {}).get('opportunities_count', 0) if bundles else 0
        bundle_potential_val = bundles.get('bundle_potential', {}).get('total_potential_revenue', 0) if bundles else 0
        bundle_potential = f"${bundle_potential_val:,.0f} potential"
        
        # Traffic light status
        traffic_light = generate_traffic_light_display(results)
        
        # Tab content
        tab_content = generate_tab_content(results, active_tab)
        
        return [
            str(zombie_count), zombie_capital,
            str(loser_count), loser_loss,
            str(slow_count), slow_value,
            str(bundle_count), bundle_potential,
            traffic_light, tab_content
        ]
    except Exception as e:
        print(f"Error updating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return ["Error"] * 8 + [html.P(f"Error: {str(e)}"), html.Div()]

def deserialize_results(results_data):
    """Convert dict back to DataFrames"""
    if not results_data or not isinstance(results_data, dict):
        return {}
    
    results = {}
    for key, value in results_data.items():
        try:
            if isinstance(value, list):
                if len(value) > 0 and isinstance(value[0], dict):
                    results[key] = pd.DataFrame(value)
                else:
                    results[key] = value
            elif isinstance(value, dict):
                results[key] = deserialize_results(value)
            else:
                results[key] = value
        except Exception as e:
            print(f"Error deserializing {key}: {e}")
            results[key] = value
    return results

def generate_traffic_light_display(results):
    """Generate traffic light status display"""
    try:
        status_map = results.get('traffic_light_status', {})
        
        if not status_map or not isinstance(status_map, dict):
            return html.P("No status data available")
        
        # Count by status
        red_count = 0
        yellow_count = 0
        green_count = 0
        
        for v in status_map.values():
            if isinstance(v, dict):
                status = v.get('status', 'green')
                if status == 'red':
                    red_count += 1
                elif status == 'yellow':
                    yellow_count += 1
                else:
                    green_count += 1
        
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(str(red_count), className="text-danger"),
                        html.P("Red (Cut)", className="mb-0")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(str(yellow_count), className="text-warning"),
                        html.P("Yellow (Watch)", className="mb-0")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3(str(green_count), className="text-success"),
                        html.P("Green (Winners)", className="mb-0")
                    ])
                ])
            ], width=4)
        ])
    except Exception as e:
        print(f"Error generating traffic light: {e}")
        return html.P(f"Error: {str(e)}")

def generate_tab_content(results, active_tab):
    """Generate content for active tab"""
    try:
        if active_tab == "tab-1":  # SKU Rationalization
            sku_rational = results.get('sku_rationalization', {})
            # Get all metrics, not just zombies
            metrics = sku_rational.get('metrics', pd.DataFrame()) if sku_rational else pd.DataFrame()
            zombies = sku_rational.get('zombie_skus', pd.DataFrame()) if sku_rational else pd.DataFrame()
            
            # Convert to DataFrame if needed
            if isinstance(metrics, dict):
                metrics = pd.DataFrame(metrics)
            if isinstance(zombies, dict):
                zombies = pd.DataFrame(zombies)
            
            # Use metrics if available, otherwise use zombies
            if isinstance(metrics, pd.DataFrame) and len(metrics) > 0:
                display_df = metrics.copy()
                # Mark which are zombies - use numeric flag for more reliable filtering
                zombie_skus = set(zombies['sku'].unique()) if len(zombies) > 0 and 'sku' in zombies.columns else set()
                display_df['_is_zombie'] = display_df['sku'].isin(zombie_skus).astype(int)
                display_df['Status'] = display_df['sku'].apply(
                    lambda x: 'Zombie' if x in zombie_skus else 'Active'
                )
            elif isinstance(zombies, pd.DataFrame) and len(zombies) > 0:
                display_df = zombies.copy()
                display_df['_is_zombie'] = 1
                display_df['Status'] = 'Zombie'
            else:
                return html.P("No data available")
            
            # Sort by composite score (worst first)
            if 'composite_score' in display_df.columns:
                display_df = display_df.sort_values('composite_score')
            
            # Convert to records first
            data_records = display_df.head(100).to_dict('records')
            
            # Prepare columns (exclude the numeric flag from display)
            display_columns = [col for col in display_df.columns if col != '_is_zombie']
            columns = [{"name": i.replace('_', ' ').title(), "id": i} for i in display_columns]
            
            # Clean data (remove numeric flag)
            clean_data = [{k: v for k, v in rec.items() if k != '_is_zombie'} for rec in data_records]
            
            return dash_table.DataTable(
                data=clean_data,
                columns=columns,
                page_size=20,
                style_cell={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Status} = Zombie'},
                        'backgroundColor': '#ffcccc',
                        'color': 'black'
                    }
                ],
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                }
            )
        
        elif active_tab == "tab-2":  # Contribution Margin
            margin = results.get('contribution_margin', {})
            ranked = margin.get('ranked_products', pd.DataFrame()) if margin else pd.DataFrame()
            if isinstance(ranked, dict):
                ranked = pd.DataFrame(ranked)
            if not isinstance(ranked, pd.DataFrame) or len(ranked) == 0:
                return html.P("No data available")
            
            # Create chart
            top_30 = ranked.head(30)
            fig = px.bar(
                top_30,
                x='sku',
                y='contribution_margin',
                title="Top 30 SKUs by Contribution Margin",
                labels={'contribution_margin': 'Profit ($)', 'sku': 'SKU'}
            )
            fig.update_xaxes(tickangle=45)
            
            return dcc.Graph(figure=fig)
        
        elif active_tab == "tab-3":  # Slow Movers
            slow_mover = results.get('slow_mover_detection', {})
            slow_movers = slow_mover.get('slow_movers', pd.DataFrame()) if slow_mover else pd.DataFrame()
            if isinstance(slow_movers, dict):
                slow_movers = pd.DataFrame(slow_movers)
            if not isinstance(slow_movers, pd.DataFrame) or len(slow_movers) == 0:
                return html.P("No slow movers identified")
            
            return dash_table.DataTable(
                data=slow_movers.head(50).to_dict('records'),
                columns=[{"name": i, "id": i} for i in slow_movers.columns],
                page_size=20
            )
        
        elif active_tab == "tab-4":  # Cannibalization
            cannibal = results.get('cannibalization', {})
            pairs = cannibal.get('cannibalization_pairs', pd.DataFrame()) if cannibal else pd.DataFrame()
            if isinstance(pairs, dict):
                pairs = pd.DataFrame(pairs)
            if not isinstance(pairs, pd.DataFrame) or len(pairs) == 0:
                return html.P("No cannibalization detected")
            
            return dash_table.DataTable(
                data=pairs.head(50).to_dict('records'),
                columns=[{"name": i, "id": i} for i in pairs.columns],
                page_size=20
            )
        
        elif active_tab == "tab-5":  # New Products
            new_product = results.get('new_product_scoring', {})
            scores = new_product.get('scores', pd.DataFrame()) if new_product else pd.DataFrame()
            if isinstance(scores, dict):
                scores = pd.DataFrame(scores)
            if not isinstance(scores, pd.DataFrame) or len(scores) == 0:
                return html.P("No new products to analyze")
            
            return dash_table.DataTable(
                data=scores.to_dict('records'),
                columns=[{"name": i, "id": i} for i in scores.columns],
                page_size=20
            )
        
        elif active_tab == "tab-6":  # Bundle Opportunities
            bundles_data = results.get('bundle_opportunities', {})
            bundles = bundles_data.get('bundle_opportunities', pd.DataFrame()) if bundles_data else pd.DataFrame()
            if isinstance(bundles, dict):
                bundles = pd.DataFrame(bundles)
            if not isinstance(bundles, pd.DataFrame) or len(bundles) == 0:
                return html.P("No bundle opportunities found")
            
            return dash_table.DataTable(
                data=bundles.head(50).to_dict('records'),
                columns=[{"name": i, "id": i} for i in bundles.columns],
                page_size=20
            )
        
        elif active_tab == "tab-7":  # Recommendations
            recommendations = results.get('consolidated_recommendations', [])
            if not recommendations:
                return html.P("No recommendations available")
            
            rec_cards = []
            for rec in recommendations[:20]:
                color_map = {
                    'critical': 'danger',
                    'high': 'warning',
                    'medium': 'info',
                    'low': 'secondary'
                }
                color = color_map.get(rec.get('priority', 'low'), 'secondary')
                
                rec_cards.append(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(rec.get('action', ''), className="card-title"),
                            html.P(rec.get('details', ''), className="card-text"),
                            html.P(rec.get('impact', ''), className="text-muted")
                        ])
                    ], color=color, outline=True, className="mb-2")
                )
            
            return html.Div(rec_cards)
        
        return html.Div()
    except Exception as e:
        print(f"Error generating tab content: {e}")
        import traceback
        traceback.print_exc()
        return html.P(f"Error loading tab content: {str(e)}")

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

