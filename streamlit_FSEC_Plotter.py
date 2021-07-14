#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
import plotly.express as px

st.title('FSEC Plotter')

#!/usr/bin/env python
# coding: utf-8

# ## ・FSEC plotterの実装

# In[ ]:


# ライブラリの読み込み
from glob import glob
import ntpath
import pandas as pd
import numpy as np
import plotly.offline as offline
import plotly.graph_objs as go
import os
import sys


# ### 0. 入力される引数 (デフォルト値)
# 
# #### 追加済みの引数
# 
# ・入力データがファイルであるかフォルダであるかの指定 (フォルダ)
# 
# ・一連のRunデータのフォルダ名 or ファイル名
# 
# ・データファイルのフィルタリング用文字列 (なし)
# 
# ・見たいDetector, Channel
# 
# ・画像を保存するか否か (しない)

# In[ ]:


#folderpath = "/Users/murakoshi/Dropbox/研究_SIDT2/FSEC/210628"
#Detector = "A"
#Channel = 1
#InputDataType = "folder"
#filtering = ""
#savefig = False


# #### 追加したい引数
# 
# ・matplotlibとplotlyの選択
# 
# ・(matplotlibを選んだ場合)範囲選択
# 
# ・カラーテーマの選択

# ### 1. 一連のRunに関する情報をまとめた辞書配列

# In[ ]:


# 入力された文字列から, _df["列名"][_df.index.get_loc("文字列")]により値を持ってくる関数get_element_from_indexを実装
@st.cache
def get_element_from_index(_df, column, index, TYPE=str):
    if TYPE == int:
        element = int(_df["{}".format(column)][_df.index.get_loc("{}".format(index))])
    elif TYPE == float:
        element = float(_df["{}".format(column)][_df.index.get_loc("{}".format(index))])
    else:
        element = _df["{}".format(column)][_df.index.get_loc("{}".format(index))]
    return element


# In[ ]:


# ファイルから全体に関する情報を取得
@st.cache
def entire_information(_df):
    BatchFile = ntpath.basename(get_element_from_index(_df, "C1", "Batch File", TYPE=str))[:-4]
    
    Num_of_Detectors = get_element_from_index(_df, "C1", "# of Detectors", TYPE=int)
    
    DetectorIDs = [] 
    for i in range(1,Num_of_Detectors+1):
        DetectorID = get_element_from_index(_df, "C{}".format(i), "Detector ID", TYPE=str)
        DetectorIDs.append(DetectorID)
        
    DetectorNames = [] 
    for i in range(1,Num_of_Detectors+1):
        DetectorName = get_element_from_index(_df, "C{}".format(i), "Detector Name", TYPE=str)
        DetectorNames.append(DetectorName)
        
    Nums_of_Channels = [] 
    for i in range(1,Num_of_Detectors+1):
        Num_of_Channels = get_element_from_index(_df, "C{}".format(i), "# of Channels", TYPE=int)
        Nums_of_Channels.append(Num_of_Channels)
    
    return BatchFile, Num_of_Detectors, DetectorIDs, DetectorNames, Nums_of_Channels


# In[ ]:


# Detector, Channelのリストを作る
@st.cache
def Det_Ch_list(entire_info):
    Det_Ch = []
    for i in range(entire_info[1]):
        for j in range(entire_info[4][i]):
            Det_Ch.append([entire_info[2][i],j+1])
    return Det_Ch


# In[ ]:


# Detector, Channelの入力と対応するDet_Ch_list上の要素のindexを取得
def DC_number(Detector, Channel, Det_Ch):
    DC = ["Detector " + Detector,Channel]
    if not DC in Det_Ch:
        st.warning('Detector '+Detector+'/Ch {}'.format(Channel)+' dose not exist.')
        st.stop()
    return Det_Ch.index(DC)


# In[ ]:


# 各ファイルをpd.DataFrameとして保存
def dfs(folderpath,filtering):
    filepaths = glob(folderpath+"/*{}*.txt".format(filtering))
    _dfs = []
    col_names = ['C{0:01d}'.format(i) for i in range(17)]
    for path in filepaths:
        _df = pd.read_csv(path, encoding='cp932', sep = '\t',index_col="C0", names=col_names)
        _dfs.append(_df)
    return(_dfs)


# ### 2. 任意のファイルの情報をまとめる
# 
# ファイル名を引数として, 
# 
# [ BatchFile名, Sample Name, # of Detectors, DetectorID, DetectorName, # of Channels, [ 分割番号 ] ]
# 
# を取得する。

# In[ ]:


# 上の関数により, ファイル全体に関する情報を取得していく
def file_information(_df):
    # Sample Nameを取得
    Sample_Name = get_element_from_index(_df, "C1", "Sample Name", TYPE=str)

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    # list(_df.filter(like="[LC",axis=0).index)を用いてファイルを分割するindexの文字列を取得
    splits = list(_df.filter(like="[LC",axis=0).index)

    # ファイルを分割する行番号の配列を取得
    Nums_of_split = []
    for split in splits:
        Num_of_split = _df.index.get_loc(split)
        Nums_of_split.append(Num_of_split)
    Nums_of_split.append(len(_df))
        
    return splits,Sample_Name,Nums_of_split


# ### 3. 2. で取得した情報より, 分割したDataFrameを配列として取得
# 
# [ [ A1 ], [ B1 ], [ B2 ], ...... ]

# In[ ]:


# ファイルと2.の配列から, DataFrameを分割
def split_df(_df):
    file_info = file_information(_df)
    entire_info = entire_information(_df)
    
    splited_dfs = []
    for i in range(sum(entire_info[4])):
        splited_df = _df[file_info[2][i]:file_info[2][i+1]]
        splited_dfs.append(splited_df)
    
    return splited_dfs


# In[ ]:


# 各分割済みDataFrameから, 情報を取得していく
def splited_df_information(splited_df):
    # # of Pointsを取得
    Number_of_Points = get_element_from_index(splited_df, "C1", "# of Points", TYPE=int)

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    # End Time(min)を取得
    End_Time_min = get_element_from_index(splited_df, "C1", "End Time(min)", TYPE=float)


    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    # Wavelength(nm)を取得 (ExとEm)
    Wavelengths = list(splited_df.filter(like="Wavelength",axis=0).index)

    # ファイルを分割する行番号の配列を取得
    Wavelengths_list = []
    for wavelength in Wavelengths:
        Wavelength = get_element_from_index(splited_df, "C1", "{}".format(wavelength), TYPE=int)
        Wavelengths_list.append(Wavelength)

    #ーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    # データ取得情報の行数を取得
    initial_cut = splited_df.index.get_loc("R.Time (min)")

    return Number_of_Points,End_Time_min,Wavelengths_list,initial_cut+1


# ### 4. 2. と3. で取得した情報より, グラフを作成・出力

# In[ ]:


# ファイル名と2.の配列と3.のDataFrameと各種情報から, グラフを作成・出力する
def plotly_trace(splited_df, file_info):
    splited_df_info = splited_df_information(splited_df)
    splited_df_volume_axis = splited_df[splited_df_info[3]:]["C1"].index.astype(float).values
    splited_df_volume_axis = splited_df_volume_axis*30/splited_df_info[1]
    splited_df_intensity_axis = splited_df[splited_df_info[3]:]["C1"]

    trace = go.Scatter(
    x = splited_df_volume_axis,
    y = splited_df_intensity_axis,
    mode = 'lines',
    name = file_info[1]
    ,line=dict(width=2.5)
    ,line_shape="spline"
    )
    
    return trace

def savefig(folderpath,fig):
    filename = folderpath+'/plot.html'
    fig.write_html(filename)
    st.sidebar.success(filename+" 保存済み")
    
def plotly_plot(data,Det_Ch,folderpath,xlim):
    
    fig = go.Figure(data = data)

    fig.update_layout(
        title=Det_Ch[0]+"/Ch {}".format(Det_Ch[1]),
        title_font=dict(size=14),
        xaxis=dict(title='Volume(ml)',dtick=2,range=[xlim[0],xlim[1]]),
        yaxis=dict(title='FL intensity(AU)'),
        showlegend=True,
        legend=dict(orientation="v", xanchor="right", x=1.2),
        legend_font=dict(size=10),
        width=800,
        height=400,
        legend_title_side="top",
        margin_l=0,
        margin_t=22
        ,plot_bgcolor='rgba(150,0,230,0.02)'
        #,template="plotly_dark"
    )

    #fig.show()
    st.plotly_chart(fig)
    
    savefig_button = st.sidebar.button('save figure',help="クリックすると, データと同じフォルダに folder/plot.html の名前でプロットが(上書き)保存されます。")
    if savefig_button:
        savefig(folderpath,fig)


# ### 5. 1. から4. の関数を用いて, フォルダ内の各ファイルからグラフを作成・出力する

# In[ ]:


def FSEC_plotter_filename(folderpath,Detector,Channel,InputDataType="folder",filtering="",xlim=[0,30]):    
    filepaths = glob(folderpath+"/*{}*.txt".format(filtering))
    _dfs = dfs(folderpath,filtering)
    entire_info = entire_information(_dfs[0])
    data = []
    Det_Ch = Det_Ch_list(entire_info)
    num = DC_number(Detector, Channel, Det_Ch)
    for i in range(len(filepaths)):
        _df = _dfs[i]
        file_info = file_information(_df)
        splited_df = split_df(_df)[num]
        trace = plotly_trace(splited_df, file_info)
        data.append(trace)
    plotly_plot(data,Det_Ch[0],folderpath,xlim)
    
def FSEC_plotter_file(_dfs,Detector,Channel,folderpath,InputDataType="folder",filtering=""):
    entire_info = entire_information(_dfs[0])
    data = []
    Det_Ch = Det_Ch_list(entire_info)
    num = DC_number(Detector, Channel, Det_Ch)
    for i in range(len(filepaths)):
        _df = _dfs[i]
        file_info = file_information(_df)
        splited_df = split_df(_df)[num]
        trace = plotly_trace(splited_df, file_info)
        data.append(trace)
    plotly_plot(data,Det_Ch[0],folderpath)
    
def wavelength_display(folderpath,filtering):
    samples = []
    _dfs = dfs(folderpath,filtering)
    for df in _dfs:
        samples.append(get_element_from_index(df,"C1","Sample Name",TYPE=str))
    sample = st.sidebar.selectbox('sample',samples)
    ind = samples.index(sample)
    data = _dfs[ind]
    wavelength = splited_df_information(split_df(data)[DC_number(Detector, Channel, Det_Ch_list(entire_info))])[2]
    if len(wavelength) == 1:
        st.sidebar.write("Wavelength (nm): ", wavelength[0])
    else:
        st.sidebar.write("Ex. Wavelength (nm): ", wavelength[0])
        st.sidebar.write("Em. Wavelength (nm): ", wavelength[1])
        
folderpath = ''

Detector = st.sidebar.selectbox('Detector', ["A","B"])

Channel = st.sidebar.selectbox('Channel', [1,2])
folderpath = st.text_input(label='Input Folder Path')

if len(folderpath) < 1:
    st.warning("Please input folder path")
    st.stop()
    
filtering = st.sidebar.text_input(label='filter', value="",key='c')

_df = dfs(folderpath,filtering)[0]
entire_info = entire_information(_df)

InputDataType = "folder"

wavelength_display(folderpath,filtering)

container = st.beta_container()
with container:
    columns = container.beta_columns([0.2, 1, 2])
    with columns[1]:
        st.write('')
        st.info('検出器'+Detector+' / Ch {}'.format(Channel))
    with columns[2]:
        xlim = [0,30]
        _xlim = st.slider(label='Volume limit',min_value=0,max_value=30,value=(0,30))
        xlim = [_xlim[0],_xlim[1]]
"""
---
"""
        
FSEC_plotter_filename(folderpath,Detector,Channel,InputDataType="folder",filtering=filtering,xlim=xlim)
