import io
import nolds
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
from generate_Result import Analysis
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import convolve


# 產生特別的點位座標'Prepare for next stand' , 'Sit-to-stand' , 'Prepare to sit' , 'Stand to sit'
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


def MorletWavelet(fc):
    F_RATIO = 7
    Zalpha2 = 3.3

    sigma_f = fc / F_RATIO
    sigma_t = 1 / (2 * np.pi * sigma_f)
    A = 1 / np.sqrt(sigma_t * np.sqrt(np.pi))
    max_t = np.ceil(Zalpha2 * sigma_t)

    t = np.arange(-max_t, max_t + 1)

    v1 = 1 / (-2 * sigma_t ** 2)
    v2 = 2j * np.pi * fc
    MW = A * np.exp(t * (t * v1 + v2))

    return MW


def tfa_morlet(td, fs, fmin, fmax, fstep):
    TFmap = np.array([])
    for fc in np.arange(fmin, fmax + fstep, fstep):
        MW = MorletWavelet(fc / fs)
        cr = convolve(td, MW, mode='same')

        TFmap = np.vstack([TFmap, abs(cr)]) if TFmap.size else abs(cr)

    return TFmap


def coarse_grain(tsLst, scale):
    while (len(tsLst) % scale != 0):
        tsLst = tsLst[:-1]  # remove the last one
    data = np.array(tsLst)
    return np.mean(data.reshape(-1, scale), axis=1)


# 上傳檔案
uploaded_file = st.file_uploader("選擇30秒坐站Keypiont數據", type=["csv"])
if uploaded_file:
    st.write("檔案名稱: ", uploaded_file.name)
    df = pd.read_csv(uploaded_file)
    # 轉資料轉為list並進行切片，需求的資料從第2個之後開始，所以[2:]
    data_select = st.selectbox(
        '請選擇Keypiont',
        options=list(df.keys())[2:])

    st.write('使用的Keypiont是:', data_select)
    Data_Arr = df[data_select]
    analysis = Analysis(Data_Arr)
    try:
        analysis.analysis_data()
        # 產生excel檔案
        # buffer = io.BytesIO()
        # with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        #     df1 = pd.DataFrame(analysis.Sp_Value_dict)
        #     df2 = pd.DataFrame(analysis.Sp_Item_dict)
        #     df3 = pd.DataFrame(analysis.Sp_Cal_dict)
        #     df = pd.concat([df1, df2, df3])
        #     df.to_excel(writer, sheet_name='Result')
        #     writer.save()
        # 提供下載按鈕讓使用者下載 Excel 檔案
        # st.download_button(
        #     label="下載數據",
        #     data=buffer,
        #     file_name=f"Result_{data_select}_{uploaded_file.name}.xlsx",
        #     mime="application/vnd.ms-excel"
        # )
        # 產生全部數據線圖，x軸是影格的list，y軸是數值
        data1 = go.Scatter(x=[i for i in range(0, len(Data_Arr))], y=Data_Arr, mode="lines", name='總數據')
        # 產生點位
        data2 = gen_markers(analysis, 'Prepare-for-next-stand', 'green')
        data3 = gen_markers(analysis, 'Sit-to-stand', 'grey')
        data4 = gen_markers(analysis, 'Prepare-to-sit', 'orange')
        data5 = gen_markers(analysis, 'Stand-to-sit', 'red')
        # 將各點整合到圖上
        data = [data1, data2, data3, data4, data5]
        layout = go.Layout(title=uploaded_file.name)
        fig = go.Figure(data=data, layout=layout)
        # 設定圖片的大小
        fig.update_layout(autosize=False, width=800, height=600, )
        # 顯示到streamlit上
        st.plotly_chart(fig, use_container_width=False)
        # 顯示分析結果
        st.dataframe(data=analysis.Sp_Cal_dict, use_container_width=True)

        pfnstand, sittostand, ptsit, stantosit = [], [], [], []
        for i in analysis.Sp_Item_dict.keys():
            try:
                if len(analysis.Sp_Cal_dict[i].keys()) == 4:
                    pfnstand.append(analysis.Sp_Cal_dict[i]['Prepare-for-next-stand'])
                    sittostand.append(analysis.Sp_Cal_dict[i]['Sit-to-stand'])
                    ptsit.append(analysis.Sp_Cal_dict[i]['Prepare-to-sit'])
                    stantosit.append(analysis.Sp_Cal_dict[i]['Stand-to-sit'])
            except KeyError as e:
                print(e)
        # print(pfnstand, sittostand, ptsit, stantosit)
        # 長條圖
        x = [i for i in range(1,len(pfnstand)+1)]  # 水平資料點
        h = pfnstand  # 高度
        plt.subplot(411)
        plt.bar(x, h)
        plt.ylabel('Prepare-for-next-stand')
        plt.yticks([0,0.5,1,1.5])
        # plt.xlabel('Times')
        # plt.ylabel('Second')
        x = [i for i in range(1,len(sittostand)+1)]  # 水平資料點
        h = sittostand  # 高度
        plt.subplot(412)
        plt.bar(x, h)
        plt.ylabel('Sit-to-stand')
        plt.yticks([0, 0.5, 1, 1.5])
        # plt.xlabel('Times')
        # plt.ylabel('Second')
        x = [i for i in range(1,len(ptsit)+1)]  # 水平資料點
        h = ptsit  # 高度
        plt.subplot(413)
        plt.bar(x, h)
        plt.ylabel('Prepare-to-sit')
        plt.yticks([0, 0.5, 1, 1.5])
        # plt.xlabel('Times')
        # plt.ylabel('Second')
        x = [i for i in range(1,len(stantosit)+1)]  # 水平資料點
        h = stantosit  # 高度
        plt.subplot(414)
        plt.bar(x, h)
        plt.ylabel('Stand-to-sit')
        plt.yticks([0, 0.5, 1, 1.5])
        # plt.xlabel('Times')
        # plt.ylabel('Second')

        plt.tight_layout()
        st.pyplot(plt)

        # 盒鬚圖
        plt.subplot(141)
        plt.boxplot(pfnstand)
        plt.xticks([])
        plt.xlabel('Prepare-for-next-stand')
        plt.subplot(142)
        plt.boxplot(sittostand)
        plt.xticks([])
        plt.xlabel('Sit-to-stand')
        plt.subplot(143)
        plt.boxplot(ptsit)
        plt.xticks([])
        plt.xlabel('Prepare-to-sit')
        plt.subplot(144)
        plt.boxplot(stantosit)
        plt.xticks([])
        plt.xlabel('Stand-to-sit')
        plt.tight_layout()
        st.pyplot(plt)

        # MSE
        plt.subplot(111)

        # set the parameters for the multiscale entropy calculation
        m = 2  # embedding dimension
        r = 0.15  # tolerance
        ts = Data_Arr
        python_MSE_results = []
        for scale_factor in range(1, 11):
            ts_i = coarse_grain(ts, scale_factor)
            sample_entropy = nolds.sampen(ts_i, m, r)
            # print(round(sample_entropy, 4), end = ", ")
            python_MSE_results.append(sample_entropy)
        # plt.figure(figsize=(18, 9))
        plt.plot(python_MSE_results, color='red', label="Python MSE")
        plt.xticks(list(range(10)), list(range(1, 11)))
        plt.tight_layout()

        st.pyplot(plt)

        # WAVELET
        time_series = np.array(Data_Arr.values)
        time_series_length = time_series.shape[0]
        time_series = time_series.reshape(time_series_length, )
        # print(time_series.shape)
        pts_per_second = 15
        fmin = 0.5
        fmax = 3
        fstep = 0.01
        # line plot 的 x
        taxis = np.linspace(1, time_series_length, time_series_length)
        taxis = taxis / pts_per_second  # 把單位改成 sec

        time_series = Data_Arr
        spec = tfa_morlet(time_series, pts_per_second, fmin, fmax, fstep)
        # reverse the rows of the array
        # 因為 1st row 是 fmin, last row 是 fmax 結果
        # 而畫圖 fmin 要畫最下面
        spec_reverse = np.flip(spec, axis=0)

        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax1.plot(taxis, time_series)
        # ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.set_title('Signal')
        img = ax2.imshow(spec_reverse, extent=[1, taxis[-1], fmin, fmax], cmap='jet', aspect='auto')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('CWT')

        plt.colorbar(img, ax=ax2, orientation='horizontal', pad=0.3)
        plt.tight_layout()

        st.pyplot(plt)

    except Exception as e:
        st.write('選取的資料計算後超出範圍無法顯示')
        print(e)
