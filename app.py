import numpy as np
from pyXSteam.XSteam import XSteam
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Initialize steam table
steam_table = XSteam(XSteam.UNIT_SYSTEM_MKS)

# Default parameter values
etax_default = 0.85
p_HD_default = 35
t_HD_default = 375

# Create a Dash application
app = dash.Dash(__name__)
server = app.server

# Define the layout of the app
app.layout = html.Div([
    html.H1("Dampfturbinen-Parameter Visualisierung", style={'textAlign': 'center'}),
    
    html.Div([
        html.Div([
            html.Label("HD-Druck [bar]"),
            dcc.Input(
                id='p-hd-input',
                type='number',
                min=1,
                max=100,
                step=0.5,
                value=p_HD_default,
                style={'width': '100%', 'height': '40px', 'fontSize': '16px', 'padding': '5px'}
            ),
            html.Div(id='p-hd-error', style={'color': 'red', 'fontSize': '12px', 'height': '20px'}),
        ], style={'padding': '20px', 'flex': '1'}),
        
        html.Div([
            html.Label("HD-Temperatur [°C]"),
            dcc.Input(
                id='t-hd-input',
                type='number',
                min=100,
                max=500,
                step=5,
                value=t_HD_default,
                style={'width': '100%', 'height': '40px', 'fontSize': '16px', 'padding': '5px'}
            ),
            html.Div(id='t-hd-error', style={'color': 'red', 'fontSize': '12px', 'height': '20px'}),
        ], style={'padding': '20px', 'flex': '1'}),
        
        html.Div([
            html.Label("Wirkungsgrad Eta [-]"),
            dcc.Input(
                id='etax-input',
                type='number',
                min=0.1,
                max=1.0,
                step=0.01,
                value=etax_default,
                style={'width': '100%', 'height': '40px', 'fontSize': '16px', 'padding': '5px'}
            ),
            html.Div(id='etax-error', style={'color': 'red', 'fontSize': '12px', 'height': '20px'}),
        ], style={'padding': '20px', 'flex': '1'}),
    ], style={'display': 'flex', 'flexDirection': 'row'}),
    
    html.Button('Berechnen', id='calculate-button', n_clicks=0, 
                style={'margin': '20px', 'padding': '10px 20px', 'fontSize': '16px'}),
    
    dcc.Graph(id='steam-graph', style={'height': '800px'}),
    
    html.Div(id='parameter-display', style={'textAlign': 'center', 'margin': '20px'}),
], style={'maxWidth': '1200px', 'margin': '0 auto'})

@app.callback(
    [Output('steam-graph', 'figure'),
     Output('parameter-display', 'children')],
    [Input('calculate-button', 'n_clicks')],
    [State('p-hd-input', 'value'),
     State('t-hd-input', 'value'),
     State('etax-input', 'value')]
)
def update_graph(n_clicks, p_HD, t_HD, etax):
    # Calculate steam properties
    try:
        hHD = steam_table.h_pt(p_HD, t_HD)
        sHD = steam_table.s_pt(p_HD, t_HD)
        ps = np.arange(0.04, p_HD, 0.01)
        t_sats = [steam_table.tsat_p(p) for p in ps]
        s_sat = [steam_table.s_pt(p, t+0.1) for p, t in zip(ps, t_sats)]
        h_MD_ideal = [steam_table.h_ps(p, sHD) for p in ps]
        
        h_MD_etax = [hHD - etax*(hHD-hi) for hi in h_MD_ideal]
        s_MD_etax = [steam_table.s_ph(p, h) for p, h in zip(ps, h_MD_etax)]
        t_MDetax = [steam_table.t_ph(p, h) for p, h in zip(ps, h_MD_etax)]
        t_ideal = [steam_table.t_ph(p, h) for p, h in zip(ps, h_MD_ideal)]
        x_ideal = [1-steam_table.x_ps(p, sHD) for p in ps]
        x_etax = [1-steam_table.x_ps(p, s) for p, s in zip(ps, s_MD_etax)]
        
        # Create subplots with 2 rows x 1 column
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.75, 0.25],
            specs=[[{"secondary_y": True}], 
                   [{"secondary_y": True}]]
        )
        
        # Add traces for first subplot (temperatures)
        fig.add_trace(
            go.Scatter(x=ps, y=t_sats, name="Kondensationstemperatur", line=dict(color="green", dash="dot")),
            row=1, col=1, secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=ps, y=t_MDetax, name=f"Entnahmetemperatur bei eta={etax}", line=dict(color="green")),
            row=1, col=1, secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=ps, y=t_ideal, name="Entnahmetemperatur bei eta=1", line=dict(color="green", dash="dash")),
            row=1, col=1, secondary_y=False
        )
        
        # Add traces for entropy on secondary y-axis
        fig.add_trace(
            go.Scatter(x=ps, y=s_sat, name="Entropie Sattdampf", line=dict(color="red", dash="dot")),
            row=1, col=1, secondary_y=True
        )
        fig.add_trace(
            go.Scatter(x=ps, y=[sHD]*len(ps), name="Entropie bei eta= 1", line=dict(color="red", dash="dash")),
            row=1, col=1, secondary_y=True
        )
        fig.add_trace(
            go.Scatter(x=ps, y=s_MD_etax, name=f"Entropie bei eta = {etax}", line=dict(color="red")),
            row=1, col=1, secondary_y=True
        )
        
        # Add traces for second subplot (enthalpy)
        fig.add_trace(
            go.Scatter(x=ps, y=[hHD]*len(ps), name="HD-Enthalpie", line=dict(color="purple")),
            row=2, col=1, secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=ps, y=h_MD_ideal, name="Enthalpie bei eta=1", line=dict(color="purple", dash="dash")),
            row=2, col=1, secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=ps, y=h_MD_etax, name=f"Enthalpie bei eta={etax}", line=dict(color="purple")),
            row=2, col=1, secondary_y=False
        )
        
        # Add water content on secondary y-axis of second subplot
        fig.add_trace(
            go.Scatter(x=ps, y=x_ideal, name="Wasseranteil bei eta=1", line=dict(color="orange", dash="dash")),
            row=2, col=1, secondary_y=True
        )
        fig.add_trace(
            go.Scatter(x=ps, y=x_etax, name=f"Wasseranteil bei eta={etax}", line=dict(color="orange",)),
            row=2, col=1, secondary_y=True
        )
        
        # Update axis properties
        fig.update_yaxes(title_text="Temperatur [°C]", row=1, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Entropie", row=1, col=1, secondary_y=True)
        fig.update_yaxes(title_text="Enthalpie", row=2, col=1, secondary_y=False)
        fig.update_yaxes(title_text="Wasseranteil", range=[-0.02, 0.3], row=2, col=1, secondary_y=True)
        fig.update_xaxes(title_text="Entnahme Druck [bar]", row=2, col=1)
        
        # Update layout
        fig.update_layout(
            title=f"Dampfturbinen-Parameter (HD: {p_HD} bar, {t_HD}°C, η: {etax})",
            height=800,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=50, r=50, t=100, b=50)
        )
        # Update layout with legend on the right side
        fig.update_layout(
            title=f"Dampfturbinen-Parameter (HD: {p_HD} bar, {t_HD}°C, η: {etax})",
            height=800,
            # New legend positioning on the right side
            legend=dict(
                orientation="v",  # vertical orientation
                yanchor="top",    # anchor point
                y=1,              # top position
                xanchor="left",   # anchor from the left
                x=1.02,           # position just outside the plot area
                bordercolor="Black",
                borderwidth=1
            ),
            # Adjust margins to make room for the legend
            margin=dict(l=50, r=150, t=100, b=50)  # increased right margin for legend
        )
        
        parameter_display = html.Div([
            html.H3("Berechnete Parameter:"),
            html.P(f"HD-Enthalpie: {hHD:.2f} kJ/kg"),
            html.P(f"HD-Entropie: {sHD:.4f} kJ/kg·K")
        ])
        
        return fig, parameter_display
        
    except Exception as e:
        # Error handling for invalid parameter combinations
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"Fehler bei der Berechnung: {str(e)}<br>Bitte andere Parameter wählen.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(height=800)
        
        error_display = html.Div([
            html.H3("Fehler bei der Parametrisierung", style={'color': 'red'}),
            html.P(str(e))
        ])
        
        return error_fig, error_display

# Add a main block to run the app
if __name__ == "__main__":
    app.run_server(debug=True)
