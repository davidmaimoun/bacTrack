import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium, folium_static

st.set_page_config(page_title='DataExplorer', layout="wide")
pd.options.mode.chained_assignment = None  # default='warn'

st.write("""
<style>
    html, body, [class*="css"]  {
    }
    h3 {
        color: #4267B2;
        margin-bottom: 24px;
    }
    h5 {
        margin-bottom: 8px;
    }
    .date_selected {
        color: #4267B2;
    }
   
</style>
""", unsafe_allow_html=True)
####################
###  FUNCTIONS  ###
##################

serogroup_color_palette = {'B':'#4267B2', 
                        'Y':'#9FB4FF', 
                        'W':'#3E8E7E',
                        'W+Y': '#7CD1B8',
                        'C':'#E8E2E2',
                        'E': '#FF8B13',
                        'NG': '#FC4F4F'}

jerusalem_coords = [31.7833, 35.2167]

type_chosen = 'Serogroup'

def groupDataFrameBy(df, val1, val2):
    return (
        df.groupby(val1)[val2]
            .value_counts()
            .rename_axis()
            .reset_index(name='Counts')
    )

def createBarChart(df, x, y, color):
   
    bar = (
        px.bar(
            df,
            x= x,
            y= y,
            color = color,
            color_discrete_map=serogroup_color_palette,
            template= 'plotly_white')
    ) 
    bar.update_layout(
        title_text= f"""
            {color}s Distribution, {df[x].min()} - {df[x].max()}
        """,
        xaxis = dict(tickmode = 'linear')
    )
    return bar

def getSlider(title, value):
    return  st.slider(
        title,
        min_value= min(value),
        max_value= max(value),
        value=(min(value),max(value))
    )

def dateFilter(getSlider, df):
    return getSlider('Isolate Year :', df['Isolate Year'].unique().tolist())

def filterDataSliderSelection(df_column, value):
    return df[df_column].between(*value)

def createVaccinChart(df, vaccin, type_chosen):
    df_vacc = df.groupby(vaccin)[type_chosen].value_counts().rename_axis().reset_index(name='Counts').sort_values(by=['Counts'], ascending=False)         
    return px.bar(df_vacc,
                    x=type_chosen,
                    y='Counts',
                    color = vaccin,
                    barmode='group',
                    template= 'plotly_white')

 
def dateSelectedTitle(date):
    if min(date) != max(date):
        return f"""{min(date)} - {max(date)}
        """
    return min(date)

def fixHeightChart(x):
    if x >= 20:
        return 1000
    elif (x >= 10) & x < 20: 
        return 500
    else:
        return 300

def assignReactivity(val):
                    if val == 'insufficient data':
                        return  '🤷 Insufficient Data'
                    elif val == 'exact match':
                        return '✅ Exact Match!'
                    elif val == 'none':
                        return '❌ No'
                    elif val == 'cross-reactive':
                        return '✔️ Cross-Reactive!'

def createMap(df, coords, source, total, cases):
    m = folium.Map(location=coords, tiles="OpenStreetMap", zoom_start=7)

    for i in range(0,len(df)):
        folium.CircleMarker(
                location=[df.iloc[i]['Lat'], df.iloc[i]['Lon']],
                tooltip=folium.Tooltip(f"""
                    <b style='color:#4267B2;'>
                    {df.iloc[i][source]},
                    {df.iloc[i][total]} cases.
                    </b><br>
                    {df.iloc[i][cases]}
                """,
                ),
                radius=float(df.iloc[i][total]*1.2),
                color='#4267B2',
                fill=True,
                fill_color='#4267B2'
            ).add_to(m)
    return m

##############
###  RUN  ###
############

df = pd.DataFrame()
df = pd.read_csv('data/data.csv')
with st.sidebar:
    st.header('BacTrack')
    st.subheader('Neisseira Surveys - MOH')
    # uploaded_file = st.file_uploader("Choose a file")
    # if uploaded_file is not None:
    #     df = pd.read_csv(uploaded_file)

if not df.empty:
    st.markdown(""" 
        <h1>Bact Tracking !</h1>  
        <br>""",unsafe_allow_html=True)
    
    st.markdown("""
        <h3>Data &#128196;</h3>
    """, unsafe_allow_html=True)

    cols = st.sidebar.multiselect("Columns",options = list(df.columns))
    type_chosen = st.sidebar.radio("Choose your type",
        ('Serogroup', 'ST', 'Serogroup + ST'))
    df['Serogroup'] = df['Serogroup'].fillna('NG')
    if not cols:
        st.dataframe(df, use_container_width=True)
    else:
        st.dataframe(df[cols], use_container_width=True)

    ################################################################
    # Separator

    st.markdown("""
        <hr style="height:1px;border:none;color:#CCC;background-color:#CCC;" />
        <h3>Charts 📊</h3>
        """, unsafe_allow_html=True)

    st.markdown("""
        <h5>Distribution of <i>N.meningitidis</i> in Israel</h5>
        """, unsafe_allow_html=True)
   
    ###############################################################
    # First Chart - Serogroups Distribution in total

   
    if type_chosen == 'ST' :
        df['ST'] = df['ST'].astype('str')
   

    if (type_chosen == 'Serogroup') | (type_chosen == 'ST'):
        df_total = groupDataFrameBy(df, 'Isolate Year', type_chosen)

        bar_total = createBarChart(
            df_total, 'Isolate Year', 'Counts', type_chosen)
       
        st.plotly_chart(bar_total)

        st.markdown("""
        <hr style="height:1px;border:none;color:#CCC;background-color:#CCC;" />
        """, unsafe_allow_html=True)
       
        ###############################################################
        # Slider selection
        date_selection = dateFilter(getSlider, df)

        ###############################################################
        # Filtered Charts
        mask = filterDataSliderSelection('Isolate Year', date_selection)
        number_of_result = df[mask].shape[0]

   
        st.markdown(f':red[*Matchs: {number_of_result}*]')

        # Group df after selection
        df_filtered = df[mask]
        dff = (
            df_filtered.groupby(type_chosen)
                .count().reset_index(type_chosen)
                .sort_values(by=['Sample'], ascending=False)
        )

        # Charts
        col1, col2 = st.columns([2,1])
        with col1:
            bar_chart = px.bar(dff,
                    x=type_chosen,
                    y='Sample',
                    text='Sample',
                    title = f"""In Selected Year(s) {dateSelectedTitle(date_selection)}
                    """,
                    color = type_chosen,
                    color_discrete_map=serogroup_color_palette,
                    template= 'plotly_white')

   
            st.plotly_chart(bar_chart, use_container_width=True)
        with col2:
            pie_chart = px.pie(dff,
                    values='Sample',
                    color = type_chosen,
                    color_discrete_map=serogroup_color_palette,
                    names=type_chosen)
            st.plotly_chart(pie_chart, use_container_width=True)
       
    else :
        col1, col2, col3= st.columns([1,.2, 1])
        with col1:
            serogroup = st.selectbox('Serogroup', pd.unique(df['Serogroup']))   
        with col3:   
            date_selection = dateFilter(getSlider, df)
            mask = filterDataSliderSelection('Isolate Year', date_selection)
            number_of_result = df[mask].shape[0]
            st.markdown(f':red[*Matchs: {number_of_result}*]')

        df_filtered = df.query(f'Serogroup == "{serogroup}"')
        df_filtered = df_filtered[mask]
        df_filtered['ST'] = df_filtered['ST'].astype('str')
        df_filtered['Isolate Year'] = df_filtered['Isolate Year'].astype('str')

        dff = (
            df_filtered.groupby(['Isolate Year'])['ST']
                .value_counts()
                .rename_axis()
                .reset_index(name='Counts')
        )

        height_chart = fixHeightChart(len(pd.unique(df_filtered['ST'])))

        bar_chart = px.bar(dff,
                    x='Counts',
                    y='ST',
                    text='Isolate Year',
                    title = f"""STs for Serogroup {serogroup} - {dateSelectedTitle(date_selection)}
                    """,
                    color = 'Isolate Year',
                    orientation='h',
                    height= height_chart,
                    template= 'plotly_white')
        bar_chart.update_layout(yaxis={'categoryorder': 'total ascending'})
   
        st.plotly_chart(bar_chart, use_container_width=True)


    ###############################################################
    # Bexero / Trumenba Cross Reactivity ###############################3
    st.markdown("""
    <h5>Bexero / Trumenba Cross Reactivity</h5>
    """, unsafe_allow_html=True)

    BEXERO = "Bexero cross reactivity"
    TRUMENBA = "Trumenba cross reactivity"

    tab1, tab2 = st.tabs(["Bexero", "Trumenba"])

    if type_chosen == 'Serogroup':
        with tab1:
            vaccin_chart = createVaccinChart(df[mask], BEXERO, type_chosen)
            st.plotly_chart(vaccin_chart, use_container_width=True)
        with tab2:
            vaccin_chart = createVaccinChart(df, TRUMENBA, type_chosen)
            st.plotly_chart(vaccin_chart, use_container_width=True)

    elif type_chosen == 'ST':
        df_new = df[['Sample', 'ST']]
        with tab1:               
            df_new['Cross reactivity']= df[BEXERO].apply(assignReactivity)
            st.dataframe(df_new, use_container_width=True)
        with tab2:
            df_new['Cross reactivity'] = df[TRUMENBA].apply(assignReactivity)
            st.dataframe(df_new, use_container_width=True)

    elif type_chosen == 'Serogroup + ST':
        df_new = df[['Sample', 'ST', 'Serogroup']]
        with tab1:               
            df_new['Cross reactivity']= df[BEXERO].apply(assignReactivity)
            st.dataframe(df_new, use_container_width=True)
        with tab2:
            df_new['Cross reactivity'] = df[TRUMENBA].apply(assignReactivity)
            st.dataframe(df_new, use_container_width=True)
    ########################################################
    # Epidemyology

   
    st.markdown("""
        <hr style="height:1px;border:none;color:#CCC;background-color:#CCC;" />
        <h3>Epidemiology 🗺️</h3>
        """, unsafe_allow_html=True)


    df_cities = pd.read_csv('data/cities.csv')
    dates = df['Isolate Year'].unique().tolist()

    map_col1, map_col2 = st.columns([3,1])

    with map_col2:
        if type_chosen == 'Serogroup + ST':
            type_filter = st.selectbox(
                type_chosen,options = pd.unique(df['Serogroup'].fillna('NG')))
            df = df.query(f'Serogroup == "{type_filter}"')
        else:
            type_filter = st.multiselect(
                type_chosen,options = pd.unique(df[type_chosen].fillna('NG')))
        region = st.multiselect("Region",options = pd.unique(df['Source Region'].fillna('Unknown')))
        date_filtered= getSlider('Isolate Years', dates)

   

    with map_col1:

        st.markdown(f"""
        <h5>Distribution of <i>N.meningitidis</i> {dateSelectedTitle(date_filtered)}
        </h5>
        """, unsafe_allow_html=True)

        # Map Filters
        if type_chosen != 'Serogroup + ST':
            if len(type_filter) > 0:
                df = df[df[type_chosen].isin(type_filter)]
        if len(region) > 0:
            df = df[df['Source Region'].isin(region)]
        if len(date_filtered) > 0:
            mask = filterDataSliderSelection('Isolate Year', date_filtered)
            df = df[mask]

       
        df1 = df['Source Region'].value_counts().rename_axis('Source').to_frame('TotalCases')
        df2 = pd.DataFrame().assign(
            Source = df_cities['city'],
            Lat = df_cities['lat'],
            Lon = df_cities['lng']
        )


        if type_chosen == 'Serogroup + ST':
            type_chosen = 'ST'

        # Regroup the num of cases by serogroup for popup on the map
        df_cases = (
            df.groupby('Source Region')[type_chosen]
            .apply(list)
            .reset_index(name=type_chosen)
        )
        l1 = []
        l2 = []
        for index, row in df_cases.iterrows():
            cases = ""
            l1.append(row[0])
            val = pd.unique(row[1])
            for i in val:
                cases += str(i) + ": " + str(row[1].count(i)) + "<br>"
            l2.append(cases) 
           

        df3 = pd.DataFrame(list(zip(l1, l2)),
                    columns =['Source', 'Cases'])
        df_map = pd.merge(
            pd.merge(df1, df2,on='Source'), df3, on='Source')


        map_created = createMap(
            df_map, jerusalem_coords, 'Source', 'TotalCases', 'Cases')

        folium_static(map_created, width=500, height=450)


    number_of_result = len(df)
    st.markdown(f':red[*Matchs: {number_of_result}*]')