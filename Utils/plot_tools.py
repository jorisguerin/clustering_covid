import numpy as np

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

DEFAULT_PLOTLY_COLORS=['rgb(31, 119, 180)', 'rgb(255, 127, 14)',
                       'rgb(44, 160, 44)', 'rgb(214, 39, 40)',
                       'rgb(148, 103, 189)', 'rgb(140, 86, 75)',
                       'rgb(227, 119, 194)', 'rgb(127, 127, 127)',
                       'rgb(188, 189, 34)', 'rgb(23, 190, 207)']

def plot_histogram(data, country, feature_name):
    d = data[data.index.get_level_values('Country') == country].sort_values(feature_name, ascending=False)
    colors = ['darkcyan' if s=='<all>' else 'lightgrey' for s in d.index.get_level_values('State')]
    go.Figure([go.Bar(
        x=d.Region, y=d[feature_name],
        text=round(d[feature_name], 2),
        marker_color=colors,
        textposition='auto',
    )]).update_layout(margin={'t': 0},
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        width=1000, height=500,
        font=dict(family="Courier New, monospace", size=22)
    ).show(displayModeBar=False)

def plot_clustering_results(data, embedding, labels):
    clustered = (labels >= 0)
    go.Figure() \
        .add_trace(go.Scatter(
            x=embedding[:,0], y=embedding[:,1],
            mode='markers', text=[r for r in data.index],
            marker={'color':[px.colors.qualitative.Set2[c] for c in labels[clustered]]},
            textposition="top center")) \
        .update_layout(margin={'t': 0},
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Courier New, monospace", size=15),
            width=500, height=300, xaxis_title='', yaxis_title='') \
        .update_xaxes(showline=False, linewidth=2, gridcolor=None, showticklabels=False) \
        .update_yaxes(showline=False, linewidth=2, gridcolor=None, showticklabels=False) \
        .show(displayModeBar=False)

def make_violin_plots(d, labels, rows=1):
    fig = make_subplots(rows=rows, cols=3, subplot_titles=d.columns)
    for i, name in enumerate(d.columns):
        for label in np.unique(labels):
            ind = (labels == label)
            fig.add_trace(
                go.Violin(
                    y=d.loc[ind, name], box_visible=True, line_color=px.colors.qualitative.Set2[label],
                    name="Class " + str(label)
                ), row=int(i/3) + 1, col=(i % 3) + 1
            )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Courier New, monospace", size=15),
        width=1000, height=600, showlegend=False) \
    .update_yaxes(showline=False, linewidth=0) \
    .show()
