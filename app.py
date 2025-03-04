import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import os
import dash
from dash import dcc, html, Input, Output, dash_table
from statsmodels.distributions.empirical_distribution import ECDF
import plotly.express as px
import plotly.graph_objects as go


# Sample data (replace with your actual datasets)
band = "UHF"  # Example band
time_range = np.arange(24)
frequency2 = np.load('frequencies.npy')
month_labels = ['DEC 2022', 'AUG 2024', 'SEPT 2024', 'OCT 2024', 'NOV 2024', 'DEC 2024', 'JAN 2025']

# Load the summary table
summary_df = pd.read_csv("RFI_summary_statistics.csv")

# Define file paths
file_paths = {
    "December 2022": "assets/RFI_Datasets/fractional_RFI_December_2022.csv",
    "August 2024": "assets/RFI_Datasets/fractional_RFI_August_2024.csv",
    "September 2024": "assets/RFI_Datasets/fractional_RFI_September_2024.csv",
    "October 2024": "assets/RFI_Datasets/fractional_RFI_October_2024.csv",
    "November 2024": "assets/RFI_Datasets/fractional_RFI_November_2024.csv",
    "December 2024": "assets/RFI_Datasets/fractional_RFI_December_2024.csv",
    "January 2025": "assets/RFI_Datasets/fractional_RFI_January_2025.csv"
}

# Load datasets into a dictionary
loaded_datasets = {
    name: pd.read_csv(path).iloc[:, 1:].values  # Exclude the first column using iloc
    for name, path in file_paths.items()
}
# Compute nanmean for each dataset
datasets = {name: np.nanmean(data, axis=0) for name, data in loaded_datasets.items()}

# Prepare data for boxplot and bar plot
data_for_boxplot = [data.flatten() for data in loaded_datasets.values()]
average = [np.nanmean(d) for d in data_for_boxplot]
yerr = [np.nanstd(d) for d in data_for_boxplot]

# Compute ECDF data
ecdf_data = {name: ECDF(data.flatten()) for name, data in loaded_datasets.items()}
# Combine frequency datasets into a dictionary
frequency_datasets = {
    'DEC 2022': pd.DataFrame(dataset_F[0][0]).median(),
    'AUG 2024': pd.DataFrame(dataset1_F[0][0]).median(),
    'SEPT 2024': pd.DataFrame(dataset2_F[0][0]).median(),
    'OCT 2024': pd.DataFrame(dataset3_F[0][0]).median(),
    'NOV 2024': pd.DataFrame(dataset4_F[0][0]).median(),
    'DEC 2024': pd.DataFrame(dataset5_F[0][0]).median(),
    'JAN 2025': pd.DataFrame(dataset7_F[0][0]).median(),
}
# Create a 2D dataset of time and frequency for the heatmap
time_frequency_datasets = {
    "AUG 2024": np.outer(datasets["August 2024"], pd.DataFrame(dataset1_F[0][0]).median().to_numpy()),
    "SEPT 2024": np.outer(datasets["September 2024"], pd.DataFrame(dataset2_F[0][0]).median().to_numpy()),
    "OCT 2024": np.outer(datasets["October 2024"], pd.DataFrame(dataset3_F[0][0]).median().to_numpy()),
    "NOV 2024": np.outer(datasets["November 2024"], pd.DataFrame(dataset4_F[0][0]).median().to_numpy()),
    "DEC 2024": np.outer(datasets["December 2024"], pd.DataFrame(dataset5_F[0][0]).median().to_numpy()),
    "JAN 2025": np.outer(datasets["January 2025"], pd.DataFrame(dataset7_F[0][0]).median().to_numpy()),
}

# Initialize Dash app
app = dash.Dash(__name__)

# Layout of the dashboard
app.layout = html.Div([
    html.H1("RFI Monitoring Dashboard"), 
    # Summary Section
    html.Div([
        html.H3("Summary"),
        html.P("""
            This dashboard provides an overview of Radio Frequency Interference (RFI) monitoring 
            using MeerKAT data. The visualizations show the intensity of RFI over time and frequency, 
            as well as the mean RFI levels for better analysis. Looking at the summarized version of the 
            January 2025 RFI occupancy. An unusual trend in RFI over frequency compared to previous months is observed.
             While the fractional RFI as a function of time remains consistent with past observations, 
             we see significantly higher RFI levels across a broad range of frequency intervals. 
             Notably, some of these affected frequencies were previously considered RFI-free for MeerKAT.
            This unexpected increase in RFI as a function of frequency could be attributed to several factors, 
            including new interference sources, changes in telescope hardware, or external environmental factors. 

        """)]),
    dcc.Graph(id='time-plot'),
    dcc.Graph(id='box-plot'),
    dcc.Graph(id='bar-plot'),
    dcc.Graph(id='ecdf-plot'),
    dcc.Graph(id='frequency-plot'),
    dcc.Graph(id='time_frequency-plot'),

    html.H3("Monthly Reports"),
    html.Ul([
        html.Li(html.A("August 2024 Report", href="/assets/RFI_Reports_21024_2025/RFI-Report-August-2024.pdf", target="_blank")),
        html.Li(html.A("September 2024 Report", href="/assets/RFI_Reports_21024_2025/RFI-Report-September-2024.pdf", target="_blank")),
        html.Li(html.A("October 2024 Report", href="/assets/RFI_Reports_21024_2025/RFI-Report-October-2024.pdf", target="_blank")),
        html.Li(html.A("November 2024 Report", href="/assets/RFI_Reports_21024_2025/RFI-Report-November-2024.pdf", target="_blank")),
        html.Li(html.A("December 2024 Report", href="/assets/RFI_Reports_21024_2025/RFI-Report-December-2024.pdf", target="_blank")),
        html.Li(html.A("January 2025 Report", href="/assets/RFI_Reports_21024_2025/RFI-Report-January-2025.pdf", target="_blank")),
        # Add links for all other months
    ]),
    html.H3("Monthly Fractional RFI Flagging Datasets"),
    html.Ul([
        html.Li(html.A("August 2024 Dataset", href="/assets/RFI_Datasets/fractional_RFI_August_2024.csv", target="_blank")),
        html.Li(html.A("September 2024 Dataset", href="/assets/RFI_Datasets/fractional_RFI_September_2024.csv", target="_blank")),
        html.Li(html.A("October 2024 Dataset", href="/assets/RFI_Datasets/fractional_RFI_October_2024.csv", target="_blank")),
        html.Li(html.A("November 2024 Dataset", href="/assets/RFI_Datasets/fractional_RFI_November_2024.csv", target="_blank")),
        html.Li(html.A("December 2024 Dataset", href="/assets/RFI_Datasets/fractional_RFI_December_2024.csv", target="_blank")),
        html.Li(html.A("January 2025 Dataset", href="/assets/RFI_Datasets/fractional_RFI_January_2025.csv", target="_blank")),
    ]),
    html.H3("Key RFI Statistics"),
    dash_table.DataTable(
        data=summary_df.to_dict("records"),
        columns=[{"name": col, "id": col} for col in summary_df.columns],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "center", "padding": "10px"},
        style_header={"backgroundColor": "lightgrey", "fontWeight": "bold"}
    )
])

# Callback to update plots based on selected month
@app.callback(
    [Output('time-plot', 'figure'),
     Output('box-plot', 'figure'),
     Output('bar-plot', 'figure'),
     Output('ecdf-plot', 'figure'),
     Output('frequency-plot', 'figure'),
     Output('time_frequency-plot', 'figure')],
    [Input('time-plot', 'clickData')]
)
def update_plots(clickData):
    selected_month = None
    if clickData:
        selected_month = month_labels[clickData['points'][0]['curveNumber']]

    # Time plot
    time_fig = go.Figure()
    for month, data in datasets.items():
        time_fig.add_trace(go.Scatter(
            x=time_range, y=data, mode='lines', name=month,
            line=dict(width=10 if month == selected_month else 3, shape='hv'),
            opacity=1 if month == selected_month else 0.5
        ))
    time_fig.update_layout(
        title=f'RFI as a function of time for {band}-band HH',
        xaxis_title='Time of the day [UTC]',
        yaxis_title='Fractional RFI flagged',
    )

    # Box plot
    box_fig = go.Figure()
    for i, month in enumerate(month_labels):
        box_fig.add_trace(go.Box(
            y=data_for_boxplot[i], name=month,
            marker_color='blue' if month == selected_month else 'gray'
        ))
    box_fig.update_layout(
        title='Box Plot of Relative RFI Differences',
        xaxis_title='Months',
        yaxis_title='Relative RFI Difference',
    )

    # Bar plot
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=month_labels, y=average, name='Average RFI Level',
        error_y=dict(type='data', array=yerr, visible=True),
        marker_color=['blue' if month == selected_month else 'gray' for month in month_labels]
    ))
    bar_fig.update_layout(
        title='Average RFI Levels with Variance',
        xaxis_title='Month',
        yaxis_title='RFI Level',
    )

    # ECDF plot
    ecdf_fig = go.Figure()
    for month, ecdf_vals in ecdf_data.items():
        ecdf_fig.add_trace(go.Scatter(
            x=ecdf_vals.x, y=ecdf_vals.y, mode='lines', name=month,
            line=dict(width=10 if month == selected_month else 3),
            opacity=1 if month == selected_month else 0.5
        ))
    ecdf_fig.update_layout(
        yaxis_type="log",
        title='ECDF of RFI Levels (severity of received RFI)',
        xaxis_title='RFI Level',
        yaxis_title='Cumulative Probability',
    )

    # Frequency plot
    freq_fig = go.Figure()
    for month, data in frequency_datasets.items():
        freq_fig.add_trace(go.Scatter(
            x=frequency2, y=data, mode='lines', name=month,
            line=dict(width=10 if month == selected_month else 3),
            opacity=1 if month == selected_month else 0.5
        ))

    # Add shaded bands and labels on the same axis as the frequency data
    for xmin, xmax, label in shaded_regions:
    # Shaded region
        freq_fig.add_shape(
        type="rect",
        x0=xmin, x1=xmax, y0=0, y1=1,  # Extend to data range
        fillcolor="gray",
        opacity=0.3,
        layer="below",
        line_width=0
    )

    # Add label in the same x-axis
    freq_fig.add_annotation(
        x=(xmin + xmax) / 2, y=1 * 0.9,  # Positioning label slightly below max Y
        text=label,
        showarrow=False,
        font=dict(size=10),
        textangle=90,
        xanchor='center', yanchor='top'
    )
    freq_fig.update_layout(
        title=f'RFI as a function of frequency for {band}-band HH',
        xaxis_title='Frequency [MHz]',
        yaxis_title='Fractional RFI flagged',
    )

    # Create a time_vs_frequency figure
    time_freq_fig = go.Figure()

    # Add heatmaps for each month (initially hidden except AUG 2024)
    months = list(time_frequency_datasets.keys())
    traces = []

    for month in months:
        heatmap = go.Heatmap(
            x=time_range,
            y=frequency2,
            z=time_frequency_datasets[month].T,
            colorscale="Viridis",
            colorbar=dict(title="Intensity"),
            visible=(month == "AUG 2024"),  # Only show the first month initially
            name=month,
        )
        traces.append(heatmap)

    time_freq_fig.add_traces(traces)

    # Create dropdown menu
    dropdown_buttons = [
        {
            "label": month,
            "method": "update",
            "args": [
                {"visible": [m == month for m in months]},  # Show only the selected month
                {"title.text": f"Time vs Frequency Heatmap for {month}"},  # Update title properly
            ],
        }
        for month in months
    ]

    # Update layout with dropdown
    time_freq_fig.update_layout(
        title=dict(text="Time vs Frequency Heatmap"),  # Set title correctly
        xaxis_title="Time",
        yaxis_title="Frequency",
        updatemenus=[
            {
                "buttons": dropdown_buttons,
                "direction": "down",
                "showactive": True,
                "x": 0.1,
                "y": 1.15,
            }
        ],
    )


    return time_fig, box_fig, bar_fig, ecdf_fig, freq_fig, time_freq_fig

# Run the app
import webbrowser
if __name__ == '__main__':
    webbrowser.open("http://0.0.0.0:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)

# if __name__ == '__main__': 
#     app.run_server(jupyter_mode="external", debug=True)