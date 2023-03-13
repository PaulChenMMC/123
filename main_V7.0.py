import io
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import convolve
from segment_analysis import Analysis
from global_analysis import tfa_morlet, coarse_grain, sample_entropy1, sample_entropy2

def gen_markers(analysis, point, colors):
    # point= 'Prepare for next stand' , 'Sit-to-stand' , 'Prepare to sit' , 'Stand to sit'
    markers_x_list = []
    markers_y_list = []
    # 將影格作為x軸座標
    for i in analysis.Sp_Item_dict.keys():
        if analysis.Sp_Item_dict[i].get(point):
            markers_x_list.append(analysis.Sp_Item_dict[i][point])
    # 將數值作為y軸座標
    for i in analysis.Sp_Value_dict.keys():
        if analysis.Sp_Value_dict[i].get(point):
            markers_y_list.append(analysis.Sp_Value_dict[i][point])
    return go.Scatter(x=markers_x_list, y=markers_y_list, marker={'color': colors, 'size': 7}, mode="markers",
                      name=point, )

def trans_select(data_selectXY,data_selectPiont):
    if data_selectPiont=="Nose":
        keypiont="1"
    elif data_selectPiont=="Left-eye":
        keypiont="2"
    elif data_selectPiont=="Right-eye":
        keypiont="3"    
    elif data_selectPiont=="Left-ear":
        keypiont="4"
    elif data_selectPiont=="Right-ear":
        keypiont="5"
    elif data_selectPiont=="Left-shouder":
        keypiont="6"
    elif data_selectPiont=="Right-shouder":
        keypiont="7"
    elif data_selectPiont=="Left-elbow":
        keypiont="8"
    elif data_selectPiont=="Right-elbow":
        keypiont="9"
    elif data_selectPiont=="Left-wrist":
        keypiont="10"
    elif data_selectPiont=="Right-wrist":
        keypiont="11"
    elif data_selectPiont=="Left-hip":
        keypiont="12"
    elif data_selectPiont=="Right-hip":
        keypiont="13"
    elif data_selectPiont=="Left-knee":
        keypiont="14"
    elif data_selectPiont=="Right-knee":
        keypiont="15"
    elif data_selectPiont=="Left-ankle":
        keypiont="16"
    elif data_selectPiont=="Right-ankle":
        keypiont="17"
    else:
        keypiont="7"

    if data_selectXY =="" :
        data_selectXY="y"

    select_item = data_selectXY + keypiont
    return select_item

# Set page title
st.header("STS keypiont data analysis system")
st.subheader("R'nR Elderly Care Series")
#未選擇上傳資料顯示
empty_element1 = st.empty()
empty_element1.write("Analyze keypoint data recognized by KeypointRCNN from sit-to-stand video. The data file looks like this.")
empty_element2 = st.empty()
image_path = "Example.png"
empty_element2.image(image_path, caption='Example')

# 上傳檔案
uploaded_file = st.sidebar.file_uploader("Select keypoint data file", type=["xlsx"])
if uploaded_file:
    if uploaded_file is not None:
        empty_element1.text("")
        empty_element2.empty()
    df = pd.read_excel(uploaded_file)
    data_selectXY = st.sidebar.radio('Direction:', ("x","y"), horizontal=True)
    
    options=["Nose","LEye","REye","LEar","REar","LShouder","RShouder","LElbow","RElbow","LWrist","RWrist","LHip","RHip","LKnee","RKnee","LAnkle","RAankle"]
    data_selectPiont = st.sidebar.radio('Keypiont',options, horizontal=True)
    
    st.sidebar.write("Keypoint:", trans_select(data_selectXY, data_selectPiont))

    Data_Arr = df[trans_select(data_selectXY,data_selectPiont)]
    analysis = Analysis(Data_Arr)
    try:
        analysis.analysis_data()
        # 產生全部數據線圖，x軸是影格的list，y軸是數值
        data1 = go.Scatter(x=[i for i in range(0, len(Data_Arr))], y=Data_Arr, mode="lines", name='總數據')
        # 產生點位
        data2 = gen_markers(analysis, 'Prep-to-std', 'green')
        data3 = gen_markers(analysis, 'Sit-to-std', 'grey')
        data4 = gen_markers(analysis, 'Prep-to-sit', 'orange')
        data5 = gen_markers(analysis, 'Std-to-sit', 'red')

        # 將各點整合到圖上
        data = [data1, data2, data3, data4, data5]
        layout = go.Layout(title=uploaded_file.name)
        fig = go.Figure(data=data, layout=layout)
        fig.update_layout(autosize=False, width=800, height=400, )
        st.plotly_chart(fig, use_container_width=False)

        # WAVELET
        time_series = np.array(Data_Arr.values)
        ts_length = time_series.shape[0]
        ts = time_series.reshape(ts_length,)
        pts_per_second = 60
        fmin = 0.1
        fmax = 1.5 #社區老人做坐到站每秒極限是2.5次
        fstep = 0.1
        taxis = np.linspace(1, ts_length, ts_length)
        taxis = taxis / pts_per_second  # 把單位改成 sec
        x_max = ts_length/pts_per_second  #畫小波圖的X軸的最大值(秒)

        time_series = Data_Arr
        spec = tfa_morlet(time_series, pts_per_second, fmin, fmax, fstep)
        spec_reverse = np.flip(spec, axis=0)
        plt.figure(figsize=(12, 6))
        plt.imshow(spec_reverse, extent=[0, x_max, fmin, fmax], cmap='jet', aspect='auto')
        plt.xlabel('Time', fontsize=14)
        plt.ylabel('Frequency', fontsize=14)
        plt.title('CWT', fontsize=14)
        plt.grid()
        plt.colorbar()
        st.pyplot(plt)

        # MSE
        msg_container = st.empty()# Create empty container
        time_series = np.array(Data_Arr.values)
        time_series_length = time_series.shape[0]
        ts = time_series.reshape(time_series_length,)
        lst1 = []
        lst2 = []
        lstnolds = []
        maxScale = 6
        r_ratio = 0.15
        with st.spinner('Calculating SE. It takes a while, please wait...'):
            for scale_factor in range (1, maxScale+1):
                msg = "SE1, scale= "+ str(scale_factor)
                msg_container.write(msg)    
                ts_i = coarse_grain(ts, scale_factor)
        
                se1 = sample_entropy1(ts_i, 3, r_ratio) 
                lst1.append(se1)
            
                tmp = [] #蒐集此 scale 下不同 m 之 SE 
                for m in range(1, 4): #m=1, 2, 3 
                    msg = "SE2, scale= "+ str(scale_factor) + ", m=" + str(m) 
                    msg_container.write(msg)    
                    se2 = sample_entropy2(ts_i, m, r_ratio)
                    tmp.append(se2)
                lst2.append(tmp)
                msg_container.empty()
        
        new_lst1 = []
        for idx in range(3): #0, 1, 2
            tmp = []
            for elt in lst1:
                tmp.append(elt[idx])
            new_lst1.append(tmp)
        
        #collect SE for m=1, 2, 3 from lst2
        new_lst2 = []
        for idx in range(3): #0, 1, 2
            tmp = []
            for elt in lst2:
                tmp.append(elt[idx])
            new_lst2.append(tmp)
        plt.figure(figsize=(12, 6))
        plt.plot(new_lst1[0], color='red',label="SE1 m=1")
        plt.plot(new_lst1[1], color='orange',label="SE1 m=2")
        plt.plot(new_lst1[2], color='pink',label="SE1 m=3")
        plt.plot(new_lst2[0], color='blue',label="SE2 m=1")
        plt.plot(new_lst2[1], color='purple',label="SE2 m=2")
        plt.plot(new_lst2[2], color='black',label="SE3 m=3")
        plt.legend(fontsize=14)
        plt.xticks(list(range(maxScale)), list(range(1,maxScale+1)), fontsize=14)
        plt.tick_params(axis='y', labelsize=14)
        plt.grid()
        st.pyplot(plt)

        pfnstand, sittostand, ptsit, stantosit = [], [], [], []
        for i in analysis.Sp_Item_dict.keys():
            try:
                if len(analysis.Sp_Cal_dict[i].keys()) == 4:
                    pfnstand.append(analysis.Sp_Cal_dict[i]['Prep-to-std'])
                    sittostand.append(analysis.Sp_Cal_dict[i]['Sit-to-std'])
                    ptsit.append(analysis.Sp_Cal_dict[i]['Prep-to-sit'])
                    stantosit.append(analysis.Sp_Cal_dict[i]['Std-to-sit'])
            except KeyError as e:
                print(e)

# 長條圖
        fig2, ax2 = plt.subplots(figsize=(12,14))
        ax2.set_yticks([])
        ax2.set_xticks([])
        ax2.set_frame_on(False)
        x = [i for i in range(1,len(pfnstand)+1)]  # 水平資料點
        h = pfnstand  # 高度
        ax2 = fig2.add_subplot(411)
        ax2.bar(x, h)
        ax2.set_ylabel('Prep-to-std')
        ax2.set_yticks([0,0.5,1,1.5])

        x = [i for i in range(1,len(sittostand)+1)]  # 水平資料點
        h = sittostand  # 高度
        ax2 = fig2.add_subplot(412)
        ax2.bar(x, h)
        ax2.set_ylabel('Sit-to-std')
        ax2.set_yticks([0, 0.5, 1, 1.5])

        x = [i for i in range(1,len(ptsit)+1)]  # 水平資料點
        h = ptsit  # 高度
        ax2 = fig2.add_subplot(413)
        ax2.bar(x, h)
        ax2.set_ylabel('Prep-to-sit')
        ax2.set_yticks([0, 0.5, 1, 1.5])

        x = [i for i in range(1,len(stantosit)+1)]  # 水平資料點
        h = stantosit  # 高度
        ax2 = fig2.add_subplot(414)
        ax2.bar(x, h)
        ax2.set_ylabel('Std-to-sit')
        ax2.set_yticks([0, 0.5, 1, 1.5])

        # 盒鬚圖
        fig3, ax3 = plt.subplots(figsize=(12,12))
        ax3.set_yticks([])
        ax3.set_xticks([])
        ax3.set_frame_on(False)
        ax3 = fig3.add_subplot(141)
        ax3.boxplot(pfnstand)
        ax3.set_xticks([])
        ax3.set_xlabel('Prep-to-stand')

        ax3 = fig3.add_subplot(142)
        ax3.boxplot(sittostand)
        ax3.set_xticks([])
        ax3.set_xlabel('Sit-to-stand')

        ax3 = fig3.add_subplot(143)
        ax3.boxplot(ptsit)
        ax3.set_xticks([])
        ax3.set_xlabel('Prepare-to-sit')

        ax3 = fig3.add_subplot(144)
        ax3.boxplot(stantosit)
        ax3.set_xticks([])
        ax3.set_xlabel('Stand-to-sit')

        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(fig2)
        with col2:
            st.pyplot(fig3)

        #產生excel檔案
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df1 = pd.DataFrame(analysis.Sp_Value_dict)
            df2 = pd.DataFrame(analysis.Sp_Item_dict)
            df3 = pd.DataFrame(analysis.Sp_Cal_dict)
            df = pd.concat([df1, df2, df3])
            df.to_excel(writer, sheet_name='Result')
            df3 = pd.DataFrame(new_lst1)
            df4 = pd.DataFrame(new_lst2)
            df5 = pd.concat([df3, df4, ])
            df5.to_excel(writer, sheet_name='MSE')
            writer.save()
            # 提供下載按鈕讓使用者下載 Excel 檔案
            st.download_button(
                label="Download data",
                data=buffer,
                file_name=f"Result_{trans_select(data_selectXY, data_selectPiont)}_{uploaded_file.name}.xlsx",
                mime="application/vnd.ms-excel"
            )

    except Exception as e:
        st.write('Error!')
        print(e)