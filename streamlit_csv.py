import io
import pandas as pd
import streamlit as st
import plotly.graph_objs as go
from generate_Result import Analysis


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

# 上傳檔案
uploaded_file = st.file_uploader("上傳檔案", type=["csv"])

# 當有選擇資料時才會出現
if uploaded_file:
    # 讀入csv檔案
    df = pd.read_csv(uploaded_file)
    # 篩選sid欄位不重覆的值
    unique_values = df['sid'].drop_duplicates()
    unique_values_list = list(unique_values)
    # 產生sid選項
    sid_select = st.selectbox(
        '請選擇SID',
        options=unique_values_list)
    # 產生XC、YC
    XC = st.number_input('XC')
    YC = st.number_input('YC')
    # 分離csv
    df_filtered = df.loc[df['sid'] == sid_select]
    # 為了避免產生SettingWithCopyWarning，要將資料先進行copy再進行操作
    df_filter_copy = df_filtered.copy()
    # 把每一列的標題取出為list，再一一代入進行運算
    for i in list(df_filtered.keys())[2:]:
        # 進行資料XC，YC運算
        if 'x' in i:
            df_filter_copy[i] = df_filtered[i] - XC
        if 'y' in i:
            df_filter_copy[i] = df_filtered[i] * -1 + YC
    # 宣告buffer來存放資料
    buffer_csv = io.BytesIO()
    with pd.ExcelWriter(buffer_csv, engine='openpyxl') as writer:
        df_filter_copy.to_excel(writer, sheet_name='Result', index=False)
        writer.save()
        # 提供下載按鈕讓使用者下載 CSV 檔案
        st.download_button(
            label="下載篩選SID的數據",
            data=buffer_csv,
            file_name=f"Result_{sid_select}_{uploaded_file.name.replace('.csv','')}.xlsx",
            mime="application/vnd.ms-excel"
        )
    st.write('TOP5')
    st.dataframe(data=df_filter_copy.head(5), use_container_width=True)
    #當XC/YC不是0的時候才執行後面的程式
    if XC != 0 or YC != 0:
        # 轉資料轉為list並進行切片，需求的資料從第2個之後開始，所以[2:]
        data_select = st.selectbox(
            '請選擇要使用的資料',
            options=list(df_filter_copy.keys())[2:])
        st.write('使用的資料是:', data_select)
        Data_Arr = df_filter_copy[data_select]
        analysis = Analysis(Data_Arr)
        try:
            analysis.analysis_data()
            # 產生excel檔案
            buffer_xlsx = io.BytesIO()
            with pd.ExcelWriter(buffer_xlsx, engine='openpyxl') as writer:
                df1 = pd.DataFrame(analysis.Sp_Value_dict)
                df2 = pd.DataFrame(analysis.Sp_Item_dict)
                df3 = pd.DataFrame(analysis.Sp_Cal_dict)
                df = pd.concat([df1, df2, df3])
                df.to_excel(writer, sheet_name='Result')
                writer.save()
                # 提供下載按鈕讓使用者下載 Excel 檔案
                st.download_button(
                    label="下載計算後的數據",
                    data=buffer_xlsx,
                    file_name=f"Result_{data_select}_{uploaded_file.name}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            # 顯示分析結果
            st.dataframe(data=analysis.Sp_Cal_dict, use_container_width=True)
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

        except Exception as e:
            st.write('選取的資料計算後超出範圍無法顯示')
            # print(e)
