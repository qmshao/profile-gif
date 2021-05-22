#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 11:38:43 2020

@author: QuanMin
"""
import base64
import os
import io
from typing import Container
from urllib.parse import quote as urlquote
from pathlib import Path    

from flask import Flask, send_from_directory
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_uploader as du
from dash.exceptions import PreventUpdate
import uuid
import time

import logging
import os

import dash_bootstrap_components as dbc
from lib.generateGIF import generateGIF
from lib.util import delete_folder


DOWNLOAD_DIRECTORY = "../downloads"
UPLOAD_DIRECTORY = "../uploads"
LOG_DIRECTORY = "../log"

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)

if not os.path.exists(LOG_DIRECTORY):
    os.makedirs(LOG_DIRECTORY)
    with open(LOG_DIRECTORY+'/app.log', 'w') as fp:
        pass

logging.basicConfig(filename=LOG_DIRECTORY+'/app.log', format='%(asctime)s  %(levelname)s:  %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)

# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
du.configure_upload(app, UPLOAD_DIRECTORY, use_upload_id=True)


@server.route("/downloads/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(DOWNLOAD_DIRECTORY, path, as_attachment=True)

@server.route("/list")
def list():
    filelist = uploaded_files()
    return '<br>'.join(filelist)

@server.route("/deleteall")
def deleteall():
    delete_folder(DOWNLOAD_DIRECTORY)
    delete_folder('../data')
    return 'OK'


@server.route("/log")
def readlog():
    with open(LOG_DIRECTORY + '/app.log', 'r') as f:
        return f.read().replace('\n','<br>')

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("Name"),
                dbc.Input(
                    id="figure-name",
                    type="text",
                    value='Bed 1',
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Time Interval (seconds)"),
                dbc.Input(
                    id="time-interval",
                    type="number", 
                    value=60,
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Start Column"),
                dbc.Input(
                    id="start-col",
                    type="number", 
                    value=1,
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Number of Columns"),
                dbc.Input(
                    id="number-of-col",
                    type="number", 
                    value=21,
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("CSV Skip Rows"),
                dbc.Input(id="skip-rows", type="number", value=9),
            ]
        ),
        dbc.Button("Generate", id="generate", color="info", className="mr-1"),
    ],
    body=True,
)

# defaultInputs = {
#     'figure-name': '',
#     'time-interval': 60,
#     'start-col': 1,
#     'number-of-col': 21,
#     'skip-rows': 9
# }

stores = []
inputVals = []
for forminput in controls.children:
    if not ('Input' in type(forminput.children[1]).__name__):
        continue
    k = forminput.children[1].id
    inputVals.append(State(k, 'value'))
    stores.append(dcc.Store(id=k+'-local', storage_type='local'))

app.layout = html.Div(
    [
        *stores,
        dbc.NavbarSimple(    
            brand="Clound Computation",
            brand_href="#",
            color="dark",
            dark=True,
        ),
        dbc.Container([
            html.H1("Profile GIF Generator"),
            du.Upload(
                id="dash-uploader",
                max_file_size=1800,  # 1800 Mb
                filetypes=['csv'],
                max_files=1,
                upload_id=uuid.uuid1(),  # Unique session id
            ),
            html.Div(
                id="uploaded-files",
                children=[
                    html.A(f"", id="uuid",),
                ]
            ),
        ]),
        html.Br(),
        dbc.Container([    
            dbc.Row([
                dbc.Col(controls, md=4),
                dbc.Col(dbc.Spinner(dcc.Graph(id="init-graph"), id="gif-graph"), className="text-center", md=8),
            ])
        ])

    ],
    style = {"width": "100%"}
)


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(DOWNLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(DOWNLOAD_DIRECTORY):
        path = os.path.join(DOWNLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/downloads/{}".format(urlquote(filename))
    return html.A(filename, href=location)

@du.callback(
    Output("uploaded-files", "children"),
    id='dash-uploader',
)
def process_csv(filenames):
    """Save uploaded files and regenerate the file list."""
    filename = filenames[0]
    logging.info('file uploaded to ' + filename)
    uploaded = Path(filename).parts
    return [html.A(f"{uploaded[-2]}", id="uuid",), html.Br(), html.A(f"{uploaded[-1]}")]


'''
Draw gif
'''
@app.callback(
    Output('gif-graph', 'children'),
    [Input('generate', 'n_clicks')],
    [*inputVals, State('uploaded-files', 'children')])
def prepareGIF(n_clicks, name, tInt, st, ncol, skiprows, uuidDiv):
    
    if n_clicks is None:
        # prevent the None callbacks is important with the store component.
        # you don't want to update the store for nothing.
        raise PreventUpdate
    if uuidDiv is None:
        return dbc.Alert('Please upload csv file first', color="danger")

    uuid = uuidDiv[0]['props']['children']
    filename = uuidDiv[2]['props']['children']
    
    gifname = generateGIF(f'{UPLOAD_DIRECTORY}/{uuid}/{filename}', st, ncol, tInt, skiprows=skiprows, name=name)
    return html.Img(src=f'/downloads/{gifname}')


'''
Control Storage
'''
for forminput in controls.children:
    
    if not ('Input' in type(forminput.children[1]).__name__):
        continue
    inp = forminput.children[1].id
    @app.callback(
        Output(inp+'-local', 'data'),
        Input(inp, "value"),
        # State(inp+'-local', 'data')
    )
    def save_to_store(val):
        time.sleep(1)
        return val
    
    @app.callback(
        Output(inp, 'value'),
        Input(inp+'-local', 'modified_timestamp'),
        State(inp+'-local', 'data')
    )
    def read_from_store(ts, data):
        if ts is None:
            raise PreventUpdate
        if not (data is None):
            return data
        else:
            raise PreventUpdate


# Running the server
if __name__ == "__main__":
    app.run_server(debug=False, host='0.0.0.0', port=3800)