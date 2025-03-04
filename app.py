import kathprfi_functions
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import os
import glob
import pickle
import os
import pdb
from dask import compute
import concurrent.futures
from tqdm.notebook import tqdm

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#%matplotlib inline

#'/net/stevie/data3/nadeem/KATHPRFI/OUT_ZARR/HH/UBAND/SKA_Baseline',
DATA_PATHS = ['/scratch/kvanqa/RFI_work/2024_UBAND_HH/AUG_HH_U',
              '/scratch/kvanqa/RFI_work/2024_UBAND_HH/SEPT_HH_U',
              '/scratch/kvanqa/RFI_work/2024_UBAND_HH/OCT_HH_U',
              '/scratch/kvanqa/RFI_work/2024_UBAND_HH/NOV_HH_U',
                '/scratch/kvanqa/RFI_work/2024_UBAND_HH/DEC_HH_U',
                '/scratch/kvanqa/RFI_work/2024_UBAND_HH/JUL_HH_U',
                '/scratch/kvanqa/RFI_work/JAN_HH_U/']

def GetZarrList(base_dirs, pattern):
    all_files = []
    for base_dir in base_dirs:
        files = glob.glob(os.path.join(base_dir, "**", pattern), recursive=True)
        all_files.append(files)
    return all_files

AllZarrList = GetZarrList(DATA_PATHS,"*.zarr")
# define the problematic fikle
# problematic_file = "/net/stevie/data3/nadeem/MeerKAT/KATHPRFI/OUT_ZARR/HH/UBAND/SKA_Baseline/UHF_HH_1672117272.zarr"
# AllZarrList = [f for f in AllZarrList0 if f != problematic_file]

print(AllZarrList)
#extraxt the actual files from the path
AllFileNames = [[Files.split('_')[-1] for Files in AllZarrList[i]] for i in range(len(AllZarrList))]


Freq, Time = [], []
origDims = []
baselines = []
elevation_data = []
# Define a helper function to open a Zarr file and extract frequency and time
def open_zarr_data(zarr_path, group="arr"):
    dataset = xr.open_zarr(zarr_path, group=group)
# `orr`, `freq`, and `time` will now be tuples containing the datasets, frequencies, and times respectively
    return list(dataset.coords), dataset["frequency"], dataset["time"], dataset["baseline"], dataset["elevation"]

for j in range(len(AllZarrList)):
    # Use list comprehension to call the helper function
    origDim, freq, time, baseline, elevation = zip(*(open_zarr_data(zarr_path) for zarr_path in AllZarrList[j]))
    Freq.append(freq)
    Time.append(time)
    baselines.append(baseline)
    elevation_data.append(elevation)
    origDims.append(origDim)
    

def open_zarr(file_list):
    """
    This function will load each file in file_list and concatenate them into a single xarray Dataset
    """
    return xr.open_zarr(file_list, group = 'arr')
#     combined_dataset = xr.concat(datasets, dim='column')  # Adjust 'concat_dim' based on your dataset dimensions

def ReturnProb(FileList, Dimension):
    '''
    
        This function will return the probability after calling the Openzarr function and process the zarr file
    
    '''

    data = open_zarr(FileList)
    data = kathprfi_functions.ProcessZarr(data, Dimension)
        
    return data

def MultiProb(FileList, DimenSions, MyDim):
    '''
    Takes the master, counter and dimension name one is
    interested in.
    Input:
        FileList - list holding names of zarr files
        DimenSions - list holding dims from zarr
        MyDim - dimension to work on
    Returns : Probability array for the chosen dimension.
    
    
    '''
    
    print(f'Going to return {MyDim} probability')
    print(f"Length MyDim {len(MyDim)},length {len(DimenSions)}")
    
    if len(MyDim) == 1:
        DimenSions.remove(MyDim[0])
    else:
        for indx in range(len(MyDim)):
            DimenSions.remove(MyDim[indx])
    
    print(DimenSions)
    
    ave_mon = []
    
    for i in tqdm(range(len(FileList))):

        try:
            p = ReturnProb(FileList[i],DimenSions) #.compute()
            ave_mon.append(p)
        except Exception as e:
            print(e)
            continue
            
    return(ave_mon)

pickle_file = True


def get_time_prob(args):
    all_filenames, index = args
    time_prob = compute(MultiProb(AllZarrList[i], origDims[0][i], ['time']))
    #time_prob = MultiProb(zarr_list, orig_dim, ['time'])
    return time_prob

def process_data(i):
    #orig_dim = open_zarr(AllZarrList[i])
    #orig_dim = GetZarrItem(AllZarrList[i][0])[0]
    TPX_file = f'U_hh_TPX_{i}.pkl'
    if pickle_file and os.path.exists(TPX_file):
        with open(TPX_file, 'rb') as file:
            #return pickle.load(file)
            return pd.read_pickle(file)
    else:
        #pdb.set_trace()
        TPX = get_time_prob((AllFileNames[i], i))
        with open(TPX_file, 'wb') as file:
            pickle.dump(TPX, file)
        return TPX

TPX_list = []
for i in range(len(DATA_PATHS)):
    process_data(i)


# with concurrent.futures.ProcessPoolExecutor() as executor:
#     map(process_data, range(len(DATA_PATHS))

zarr_files_data = []
for zarr_size in range(len(AllFileNames)):
    print(AllFileNames[zarr_size])
    zarr_files_data.append(AllFileNames[zarr_size])

# now we will just read it with pickle as we have dumped it in the sy
DS = []
for ii in range(len(AllFileNames)+1):
    with open(f'U_hh_TPX_{ii}.pkl', 'rb') as file:
        datasets=  pd.read_pickle(file)
        DS.append(datasets)

# Identify row and column where the probability is zero
dataset_T, dataset1_T, dataset2_T, dataset3_T, dataset4_T, dataset5_T, dataset6_T, dataset7_T = DS[0], DS[1], DS[2],DS[3], DS[4], DS[5], DS[6], DS[7]


# now we will just read it with pickle as we have dumped it in the sy
DSF = []
for ii in range(len(AllFileNames)+1):
    with open(f'U_hhh_FPX_{ii}.pkl', 'rb') as file:
        datasetsF=  pd.read_pickle(file)
        DSF.append(datasetsF)
# Identify row and column where the probability is zero
dataset_F, dataset1_F, dataset2_F, dataset3_F, dataset4_F, dataset5_F, dataset6_F, dataset7_F = DSF[0], DSF[1], DSF[2],DSF[3], DSF[4], DSF[5], DSF[6], DSF[7]
dataset_F[0][0]


# prepare dataset for time
band="U"

# Sort out the data nad prepare it for visualization and analysis
# the pickle files produce tuples, convert those to correct dimensions of (row: observations, columns: hours of the day)

# Iterate over the rows and remove rows that contain zeros
filtered_dataset = []
filtered_dataset1 = []
filtered_dataset2 = []
filtered_dataset3 = []
filtered_dataset4 = []
filtered_dataset5 = []
filtered_dataset6 = []
filtered_dataset7 = []


for row in dataset_T[0]:
    if not np.any(row == 0):  # If there is no zero in the row
        filtered_dataset.append(row)

for row in dataset1_T[0]:
    if not np.any(row == 0):  # If there is no zero in the row
        filtered_dataset1.append(row)
        
for row in dataset2_T[0]:
    if not np.any(row == 0):  # If there is no zero in the row
        filtered_dataset2.append(row)
for row in dataset3_T[0]:
    if not np.any(row == 0):  # If there is no zero in the row
        filtered_dataset3.append(row)
for row in dataset4_T[0]:
    if not np.any(row == 0):  # If there is no zero in the row
        filtered_dataset4.append(row)
for row in dataset5_T[0]:
    if not np.any(row == 0):  # If there is no zero in the row
        filtered_dataset5.append(row)

for row in dataset6_T[0]:
    if not np.any(row == 0):  # If there is no zero in the row
        filtered_dataset6.append(row)

for row in dataset7_T[0]:
    if not np.any(row==0):
        filtered_dataset7.append(row)

# Convert back to NumPy array if needed
dataset_T = np.array(filtered_dataset)
dataset1_T = np.array(filtered_dataset1)
dataset2_T = np.asarray(filtered_dataset2)
dataset3_T = np.asarray(filtered_dataset3)
dataset4_T = np.asarray(filtered_dataset4)
dataset5_T = np.asarray(filtered_dataset5)
dataset6_T = np.asarray(filtered_dataset6)
dataset7_T = np.asarray(filtered_dataset7)

print("Filtered dataset:")
print(dataset_T.shape, dataset1_T.shape, dataset2_T.shape, dataset3_T.shape, dataset4_T.shape, dataset4_T.shape, dataset5_T.shape,dataset6_T.shape, dataset7_T.shape)

# Shaded frequency bands (example values, adjust to match your figure)
shaded_regions = [
    (560, 580, 'DTV1'),
    (700, 720, 'DTV2'),
    (750, 780, 'Vodacom downlink'),
    (800, 830, 'MTN downlink'),
    (850, 875, 'Telkom downlink'),
    (880, 915, 'GSM UP'),
    (925, 960, 'GSM DOWN'),
    (967, 1164, 'Aircraft transponders')
]
# Sample data (replace with your actual datasets)
band = "UHF"  # Example band
time_range = np.arange(24)
frequency2 =  Freq[0][0].to_numpy() // 1e6
month_labels = ['DEC 2022', 'JUL 2024', 'AUG 2024', 'SEPT 2024', 'OCT 2024', 'NOV 2024', 'DEC 2024', 'JAN 2025']

# Load the summary table
summary_df = pd.read_csv("RFI_summary_statistics.csv")

# Combine datasets into a dictionary for easy access
datasets = {
    'DEC 2022': np.nanmean(dataset_T, axis=0),
    'AUG 2024': np.nanmean(dataset1_T, axis=0),
    'SEPT 2024': np.nanmean(dataset2_T, axis=0),
    'OCT 2024': np.nanmean(dataset3_T, axis=0),
    'NOV 2024': np.nanmean(dataset4_T, axis=0),
    'DEC 2024': np.nanmean(dataset5_T, axis=0),
    'JUL 2024': np.nanmean(dataset6_T, axis=0),
    'JAN 2025': np.nanmean(dataset7_T, axis=0),
}

# Create a DataFrame for boxplot and bar plot
data_for_boxplot = [dataset_T[0].flatten(), dataset1_T[0].flatten(), dataset2_T[0].flatten(),
                    dataset3_T[0].flatten(), dataset4_T[0].flatten(), dataset5_T[0].flatten(),
                    dataset6_T[0].flatten(), dataset7_T[0].flatten()]
average = [np.nanmean(d) for d in data_for_boxplot]
yerr = [np.nanstd(d) for d in data_for_boxplot]

# ECDF data (replace with your actual ECDF data)
from statsmodels.distributions.empirical_distribution import ECDF

ecdf_data = {
    'DEC 2022': ECDF(dataset_T.flatten()),
    'JUL 2024': ECDF(dataset1_T.flatten()),
    'AUG 2024': ECDF(dataset2_T.flatten()),
    'SEPT 2024': ECDF(dataset3_T.flatten()),
    'OCT 2024': ECDF(dataset4_T.flatten()),
    'NOV 2024': ECDF(dataset5_T.flatten()),
    'JUL 2024': ECDF(dataset6_T.flatten()),
    'JAN 2025': ECDF(dataset7_T.flatten()),
}

# Combine frequency datasets into a dictionary
frequency_datasets = {
    'DEC 2022': pd.DataFrame(dataset_F[0][0]).median(),
    'AUG 2024': pd.DataFrame(dataset1_F[0][0]).median(),
    'SEPT 2024': pd.DataFrame(dataset2_F[0][0]).median(),
    'OCT 2024': pd.DataFrame(dataset3_F[0][0]).median(),
    'NOV 2024': pd.DataFrame(dataset4_F[0][0]).median(),
    'DEC 2024': pd.DataFrame(dataset5_F[0][0]).median(),
    'JUL 2024': pd.DataFrame(dataset6_F[0][0]).median(),
    'JAN 2025': pd.DataFrame(dataset7_F[0][0]).median(),
}
# Create a 2 dimensional dataset of time and frequency for the heatmap
time_frequency_datasets = {"AUG 2024": np.outer(np.nanmean(dataset1_T, axis=0),pd.DataFrame(dataset1_F[0][0], columns=frequency2).median().to_numpy()) ,
                           "SEPT 2024": np.outer(np.nanmean(dataset2_T, axis=0),pd.DataFrame(dataset2_F[0][0], columns=frequency2).median().to_numpy()),
                           "OCT 2024": np.outer(np.nanmean(dataset3_T, axis=0),pd.DataFrame(dataset3_F[0][0], columns=frequency2).median().to_numpy()),
                           "NOV 2024": np.outer(np.nanmean(dataset4_T, axis=0),pd.DataFrame(dataset4_F[0][0], columns=frequency2).median().to_numpy()),
                           "DEC 2024": np.outer(np.nanmean(dataset5_T, axis=0),pd.DataFrame(dataset5_F[0][0], columns=frequency2).median().to_numpy()),
                           "JAN 2025" : np.outer(np.nanmean(dataset7_T, axis=0),pd.DataFrame(dataset7_F[0][0], columns=frequency2).median().to_numpy())}


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
