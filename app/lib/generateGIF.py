# -*- coding: utf-8 -*-
"""
Created on Fri May 21 09:12:08 2021

@author: SHAOQM

pip install -U gif
pip install "gif[altair]"     
pip install "gif[matplotlib]"
pip install "gif[plotly]"
"""


#import plotly.graph_objects as go
from matplotlib import pyplot as plt
import pandas as pd
import time
from pathlib import Path    
import gif


def generateGIF(filename, start, locations, interval, name=None, skiprows=9, duration=100, minute=True):
    plt.ioff()
    # Gif function definition
    @gif.frame
    def plot(i):
        x = bedlen
    #    y = df.iloc[i][start:start+locations].tolist()
        y = [float(e) for e in df.iloc[i]]
        y = df.iloc[i][start:start+locations]
        plt.plot(x,y)
        plt.ylim(minT,maxT)
        plt.ylabel('Temperature [F]')
        plt.xlabel('Bed Length [%]')
        tt = name + '\n' if name else ''
        if minute:
            plt.title(f'{tt}t = {int(i/60)} minutes')
        else:
            plt.title(f'{tt}t = {i} seconds')
    
    #    fig = go.Figure()
    #    fig.add_trace(go.Scatter(
    #        x=bedlen,
    #        y=df.iloc[i][st:st+21]
    ##        mode="markers"
    #    ))
    #    fig.update_layout(width=500, height=300)
    #    return fig
    
    df = pd.read_csv(filename, skiprows=skiprows, header=[0,1],dtype='float').dropna(axis=1)
    # Construct list of frames
    cols = df.columns
    maxT = max(df[cols[start:start+locations]].max())
    maxT = (maxT//50 + 1) * 50
    minT = min(df[cols[start:start+locations]].min())
    minT = (minT//50) * 50
    
    xint = 100 / (locations-1)
    bedlen = [i*xint for i in range(locations)]
    frames = []
    for i in range(df.shape[0]):
        if i%interval==0 or i==df.shape[0]-1:
            print(f'generating frame at {i} seconds for {name}')
            frame = plot(i)
            frames.append(frame)
    
    
    # Save gif from frames with a specific duration for each frame in ms
    filepath = Path(filename)
    csvstem = filepath.stem
    gifname = f'{csvstem}{("-"+ name) if name else ""}-{int(time.time()*1000)}.gif'
    gif.save(frames, filepath.parent.parent.parent/'downloads'/gifname, duration=duration)

    return gifname


# df = pd.read_csv(filename, skiprows=9, header=[0,1],dtype='float').dropna(axis=1)

# for i in range(3):
#     generateGIF(df, f'Bed{i+1}', 1+i*21, 21, interval, filename)