#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The haplogroup-tracker is adapted from Haplogroup Tracker.py

Description: This script is used to track the movement of haplogroups over time using streamlit and plotly libraries.
The script takes the data from the excel file and plots the haplogroups on the map based on the user input. 
The user can select the haplogroups to be plotted on the map and the map type. 
The user can also select the haplogroup to animate and the script will animate the haplogroup movement over time.

Website Link:https://nikhilesh-vasanthakumar-haplotracker-haplogroup-tracker-wqf8g7.streamlit.app/

User Defined Functions:
    common_code(mtgeo): This function is used to plot the haplogroups on the map based on the user input.
    The function takes the data as input and returns the map with the haplogroups plotted on it and the user can select the group to be animated.
    Onlyfemale_mtdna(): This function is used to filter the data to only include the females mtdna and then call the common_code function to plot the haplogroups on the map.
    Onlymale_mtdna(): This function is used to filter the data to only include the males mtdna and then call the common_code function to plot the haplogroups on the map.
    Combined_mtdna():This function is used to filter the data to only include  mtdna and then call the common_code function to plot the haplogroups on the map.
    Onlymale_ychrom():This function is used to filter the data to include only individuals with y-chromosome and then call the common_code function to plot the haplogroups on the map.
Procedure:
1.Import the required libraries
2.Read the data from the excel file which acts as the database.
3.Filter the data based on the user input.
4.Plot the haplogroups on the map based on the user input.
5.Create static traces based on the groups selected.
5.Create frames based on the longitude and latitude of the haplogroups selected.
6.Create the animation based on the frames created.
User Guide:
1.User selects mode of the haplogroup ie. the mtdna mode or y-chromosome mode.
2.User selects the Haplogroups that they want to visualize.
3.User selects the map type.
4.User selects the haplogroup to animate.
5.Press the play button to animate the haplogroup movement over time.

    """
#Create a streamlit app to track the movement of haplogroups over time
#Importing the required libraries
#import matplotlib.pyplot as plt
#import seaborn as sns
import tap
import pandas as pd
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
#from itables.streamlit import interactive_table
#from PIL import Image
import os
from pathlib import Path
#Adding a browser title
st.set_page_config(page_title="Ancient DNA and Schizophrenia with Haplo Tracker",page_icon=":dna:",layout="wide",initial_sidebar_state="collapsed")

st.markdown(f'<link rel="stylesheet" href="assests/style.css">', unsafe_allow_html=True)
#Hiding the main menu and footer {visibility: hidden;}
hide_streamlit_style = """
            <style>
            #MainMenu 
            footer 
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)



def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    _min,
                    _max,
                    (_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].str.contains(user_text_input)]

    return df



#Reading the data
data=pd.read_csv("Data/data.csv", sep="\t")

data=data.rename(columns={'Continente':'Region', 'Período Histórico': 'Historical Period', 'PRS_Normalizado': 'PRS_SCZ'})

# Selecting the required columns from the data
data=data[["Molecular Sex","Lat.","Long.","Region","mtDNA haplogroup if >2x or published",
           "Date mean in BP in years before 1950 CE [OxCal mu for a direct radiocarbon date, and average of range for a contextual date]",
           "Political Entity", "PRS_SCZ", "Historical Period"]]

mapa_paises_continentes = {
    'Nigeria': 'África', 'USA': 'América', 'Russia': 'Ásia', 'Puerto Rico': 'América', 'Spain': 'Europa',
    'United Kingdom': 'Europa', 'India': 'Ásia', 'Sri Lanka': 'Ásia', 'Turkmenistan': 'Ásia', 'Uzbekistan': 'Ásia',
    'Pakistan': 'Ásia', 'China': 'Ásia', 'Tajikistan': 'Ásia', 'Kazakhstan': 'Ásia', 'Kyrgyzstan': 'Ásia',
    'Peru': 'América', 'Mexico': 'América', 'Bahamas': 'América', 'Finland': 'Europa', 'Venezuela': 'América',
    'Canada': 'América', 'Iceland': 'Europa', 'Greenland': 'América', 'Nepal': 'Ásia', 'Norway': 'Europa',
    'Cuba': 'América', 'Haiti': 'América', 'Belize': 'América', 'Dominican Republic': 'América', 'Jordan': 'Ásia',
    'France': 'Europa', 'Chile': 'América', 'Ireland': 'Europa', 'Argentina': 'América', 'Morocco': 'África',
    'Hungary': 'Europa', 'Guadeloupe': 'América', 'Tonga': 'Oceania', 'French Polynesia': 'Oceania', 'Sudan': 'África'
}

# Atualizar a coluna 'Continente' com base no mapeamento direto
for pais, continente in mapa_paises_continentes.items():
    data.loc[(data['Region'] == 'Indeterminado') & (data['Political Entity'] == pais), 'Region'] = continente

# Renaming the columns for ease of use
data=data.rename(columns={'Lat.':'Lat','Long.':'Long',
                          'Molecular Sex':'Sex',
                          'Political Entity':'Country',
                          'mtDNA haplogroup if >2x or published':'mtdna',
                          'Historical Period':'Period',
                          'Date mean in BP in years before 1950 CE [OxCal mu for a direct radiocarbon date, and average of range for a contextual date]':'Date'})

data=data.drop(data[data.Lat==".."].index) #dropping the rows with missing values
data["Lat"] = data["Lat"].replace('',np.nan).astype(float) # df.a.replace('',np.nan).astype(float)
data["Long"] = data["Long"].replace('',np.nan).astype(float)
#data["PRS_SCZ"] = data["PRS_SCZ"].str.replace(",", ".").astype(float) 
#data=data.drop(data[data.Region=="Indeterminado"].index) 
data["mtdna"] = data["mtdna"].str.replace('n/a (<2x)', "..")
    
#Creating a title for the app
title_text = "Ancient DNA and Schizophrenia"
subtitle = "Polygenic risk for schizophrenia: from the Paleolithic to the post-Neolithic"

st.title(title_text)

tab1, tab2, tab3 = st.tabs(["Home", "Exploratory Data Analysis", "HaploTracker"])
with tab1:
    st.subheader(subtitle)
    url = "https://github.com/Nikhilesh-Vasanthakumar/Haplotracker"
    st.markdown('''This study investigated the evolutionary dynamics of polygenic risk PRS_SCZs (PRS) for schizophrenia in ancient human populations, 
analyzing genomes spanning from the Early Upper Paleolithic to the Post-Neolithic period. The results revealed significant fluctuations in PRS over time, with a reduction observed during the Paleolithic and a notable increase from the Neolithic onward.
**Keywords:** schizophrenia, polygenic risk, ancient DNA, human evolution, Neanderthal introgression, selective pressures.
                ''')
  
# These variations appear to be related to changes in selective pressures and social transformations brought about by the advent of agriculture and the growth of sedentary societies. During the Paleolithic, negative selection may have reduced the frequency of schizophrenia risk alleles, reflecting the need for social cohesion and cognitive skills in small hunter-gatherer groups. In contrast, in the Neolithic, increasing social complexity and the development of caregiving practices may have favored the persistence of genetic variants associated with schizophrenia. Additionally, demographic factors such as population bottlenecks, founder effects, and genetic drift may have influenced the distribution of these alleles over time. The study also highlights the relevance of Neanderthal DNA introgression in modern genetic composition and its possible impact on psychiatric disorders. The integration of ancient genomic data with emerging technologies and advanced analytical methodologies offers new perspectives for understanding the evolution of complex conditions such as schizophrenia. The findings underPRS_SCZ the importance of including diverse populations in genetic studies and adopting interdisciplinary approaches to investigate the interplay between genetic, cultural, and environmental factors. This work contributes to understanding the evolutionary foundations of schizophrenia, emphasizing the complex relationship between genetic and social evolution.          
    st.markdown('''
#### Dataset source 
The ancient genotypes used in this study were obtained from the [Allen Ancient DNA Resource (AADR)](https://reich.hms.harvard.edu/allen-ancient-dna-resource-aadr-downloadable-genotypes-present-day-and-ancient-dna-data), 
a robust repository that provides curated and standardized data for analyses of population history and natural selection. 
                
#### How to cite:
_Polygenic risk for schizophrenia: from the Paleolithic to the post-Neolithic._
Thiago Felipe Fonseca Nunes de Oliveira¹, Priscilla Kelly², Patrick Terrematte¹, Raul Maia Falcão¹, Jorge Estefano Santana de Souza¹, Sandro de Souza¹ and Sidarta Ribeiro². 
_To be published._
- ¹ Bioinformatics Multidisciplinary Environment (BioME), Digital Metropolis Institute (IMD), Federal University of Rio Grande do Norte (UFRN), Brazil.
- ² Brain Institute, UFRN, Natal, RN, Brazil

#### Contact
If you have some question, feedback, or request, contact the corresponding author.

#### Data
 ''')
    st.dataframe(filter_dataframe(data))
    
    
with tab2:
    st.subheader("Exploratory Data Analysis")
    col1,col2=st.columns(2)
    with col1: 
        period_order = ['Paleolítico', 'Mesolítico', 'Neolítico', 'Pós-Neolítico', "Total"]
        df_cros = pd.crosstab(data['Region'], data['Period']) #, colnames=period_order)
        df_cros['Total'] = df_cros.sum(axis=1)
        df_cros.columns = period_order
        fig02 = px.imshow(df_cros, text_auto=True)
        st.plotly_chart(fig02)

    with col2:
        # Tab 02 - Figure 03 - Barplot
        periods=['Paleolítico', 'Mesolítico', 'Neolítico', 'Pós-Neolítico']
        fig03 = px.histogram(data, x="Period", color="Region", text_auto=False)
        fig03.update_xaxes(categoryorder='array', categoryarray=periods)
        #fig03.update_layout(xaxis={'categoryorder': order})
        st.plotly_chart(fig03)

    x = "Period"
    y = "PRS_SCZ"
    fig00 = tap.plot_stats(data, x, y, order=periods, type_correction="bonferroni", type_test="dunn") 
    st.plotly_chart(fig00)

    x = "Region"
    y = "PRS_SCZ"
    order = ['África','Ásia','Europa','América', 'Oceania']
    pairs=[("África", "Ásia"), ("África", "América"), ("África", "Europa"), ('América','Ásia'), 
           ('América','Europa'), ('América','Oceania')           ]
    fig01 = tap.plot_stats(data, x, y, type_correction="bonferroni", order=order) # , pairs=pairs
    st.plotly_chart(fig01)
    
      
    data_sorted = data.sort_values(by='Date')
    fig04 = px.line(data_sorted, x='Date', y='PRS_SCZ', markers=True, color='Region')

    colors = [px.colors.qualitative.Pastel[3], px.colors.qualitative.Pastel[4],  px.colors.qualitative.Pastel[5], 
              px.colors.qualitative.Pastel[7]]
    shapes = []
    bgs = [[0, 4000], 
           [4000, 8000], 
           [8000, 13000], 
           [13000, max(data_sorted.Date)+1000]]
    for i, b in enumerate(bgs):
        shapes.append(dict(type="rect",
                    xref="x",
                    yref="paper",
                    x0=b[0],
                    y0=0,
                    x1=b[1],
                    y1=1,
                    fillcolor=colors[i],
                    opacity=0.3,
                    layer="below",
                    line_width=0))
        fig04.add_annotation(text=periods[3-i], textangle=315, 
                  x=(b[0]+b[1])/2, y=min(data_sorted.PRS_SCZ), showarrow=False,)

    fig04.update_layout(#xaxis=dict(showgrid=False),
                    shapes=shapes)

    fig04.update_layout(xaxis = dict(autorange="reversed") )

    st.plotly_chart(fig04)

    


with tab3:
    st.subheader("HaploTracker Analysis")
    st.write("This application is adapted from the tool [Haplotracker](%s) (MIT license)." % url) 
    #Creating a dataframe with the required columns and renaming the columns
    col1,col2=st.columns(2)
    with col1:
        #image=Image.open('assests/LU.png')
        #st.image(image, width=150)
        #Creating the main function for the app    
        def common_code(mtgeo):     
            try:
                # 
                fig00 = go.Figure()
                periods = ['Paleolítico', 'Mesolítico', 'Neolítico', 'Pós-Neolítico']
                for p in periods:
                    fig00.add_trace(go.Violin(x=mtgeo['Period'][mtgeo['Period'] == p],
                                    y=mtgeo['PRS_SCZ'][mtgeo['Period'] == p],
                                    name=p,
                                    box_visible=True,
                                    meanline_visible=True))
                st.plotly_chart(fig00)


                # Get the top 10 most frequent mtdna values
                top_10_mtdna = mtgeo['mtdna'].value_counts().nlargest(20).index
                # Filter the DataFrame to include only the top 10 mtdna values
                filtered_subset = mtgeo[mtgeo['mtdna'].isin(top_10_mtdna)]
                fig01 = px.histogram(filtered_subset, x="mtdna", color="Region", text_auto=False)
                fig01.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig01)
                fig01 = px.histogram(filtered_subset, x="mtdna", color="Period", text_auto=False)
                fig01.update_layout(xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig01)
                #creating a sidebar to select the haplogroups
                option=st.multiselect(label="Select the haplogroup",options=mtgeo["mtdna"].unique())
                if not option:#if no haplogroup is selected
                    st.error("Please select atleast one haplogroup")
                else:  #    if haplogroup is selected
                    mtgeo["Date"]=mtgeo["Date"]+70 #adding 70 years to the date column to find age from 2020
                    mtgeo['Lat'].astype(float) #converting the latitude column to float
                    mtgeo['Long'].astype(float) #converting the longitude column to float
                    select=mtgeo[mtgeo["mtdna"].isin(option)]      #selecting the haplogroups selected in the sidebar
                    select["hover"] = select["Country"].str.cat('\t' + select["Date"].astype(str) + ' years ago') #creating a hover column
                    map_type=st.selectbox("Select map type",options=["USGS","Natural Earth"]) #selecting the map type
                    if map_type=="Natural Earth":   #if natural earth is selected
                            fig1 = px.scatter_geo(select, lat = 'Lat', lon = 'Long',color='mtdna',hover_name="hover",projection='natural earth',
                                                color_discrete_sequence=px.colors.qualitative.Set1)
                            fig1.update_geos(showland=True,landcolor="LightGreen",showocean=True, oceancolor="LightBlue",
                                            showrivers=True, rivercolor="Blue",
                                            projection_type="natural earth",fitbounds="locations")
                            st.plotly_chart(fig1)
                            select=select.sort_values(by="Date",ascending=False)  #sorting the data based on the date in descending order
                            animate_select=st.selectbox("Select haplogroup to animate",options=option)  #Using the user input to select the haplogroup to animate
                            animate_data = select[select["mtdna"].isin([animate_select])]
                            fig3 = go.Figure(
                                data=[
                                    go.Scattermapbox(
                                        lat=animate_data["Lat"],
                                        lon=animate_data["Long"],
                                        mode="lines",
                                        line=dict(width=2, color="blue"),
                                        name="Haplogroup Movement",
                                        hovertext=animate_data["hover"]
                                    ),
                                    go.Scattermapbox(
                                        lat=animate_data["Lat"],
                                        lon=animate_data["Long"],
                                        mode="lines",
                                        line=dict(width=2, color="blue")
                                    ),
                                    go.Scattermapbox(
                                        lat=animate_data["Lat"],
                                        lon=animate_data["Long"],
                                        mode="markers",
                                        marker=dict(
                                            size=6,
                                            color="red"
                                        ),
                                        name="Haplogroup locations",
                                        hovertext=animate_data["hover"]
                                    )
                                ],
                                layout=go.Layout(
                                    title_text="Movement of selected Haplogroup over history",
                                    mapbox_style="carto-positron", # Change the mapbox_style to "carto-positron"
                                    mapbox=dict(
                                        accesstoken="pk.eyJ1IjoibmlraGlsZXNoMjMiLCJhIjoiY2xmMmJucGx6MDFxaTN5bnRpYW12cWxxeCJ9.KeccdtSz6Hc9F_vPrYoiNg",
                                        bearing=0,
                                        center=dict(
                                            lat=select["Lat"].mean(),
                                            lon=select["Long"].mean()),
                                        pitch=0,
                                        zoom=1
                                    ),
                                    updatemenus=[
                                        dict(
                                            type="buttons",
                                            buttons=[dict(label="Play", method="animate",args=[None])]
                                        )
                                    ]
                                ),
                                frames=[
                                    go.Frame(
                                        data=[
                                            go.Scattermapbox(
                                                lat=[list(animate_data["Lat"])[k]],
                                                lon=[list(animate_data["Long"])[k]],
                                                mode="markers",
                                                marker=dict(color="red", size=10),
                                                text=list(animate_data["mtdna"])[k]
                                            ),

                                            go.Scattermapbox(
                                                lat=list(animate_data["Lat"])[:k+1],
                                                lon=list(animate_data["Long"])[:k+1],
                                                mode="lines",
                                                line=dict(width=2, color="orange"),
                                                name="Movement"
                                            )
                                        ]
                                    )
                                    for k in range(1, len(animate_data["mtdna"]))
                                ]
                            )

                            # Change the map style using update_layout
                            fig3.update_layout(
                                mapbox=dict(
                                    style="carto-positron",
                                    center=dict(
                                        lat=select["Lat"].mean(),
                                        lon=select["Long"].mean()
                                    ),
                                    zoom=1
                                )
                            )

                            st.plotly_chart(fig3)

                    else:       #if USGS is selected
                            fig1 = px.scatter_mapbox(select, lat = 'Lat', lon = 'Long',color='mtdna',hover_name="hover",
                                                color_discrete_sequence=px.colors.qualitative.Set1)   #creating a scatter plot on the map based on the haplogroups selected
                            fig1.update_traces(marker=dict(size=10, symbol="circle"))#updating the size of the markers and the shape of the markers
                            fig1.update_geos(showland=True,landcolor="LightGreen",showocean=True, oceancolor="LightBlue",   #updating the map features
                                            showrivers=True, rivercolor="Blue")
                            select=select.sort_values(by="Date",ascending=False)       #sorting the data based on the date in descending order
                            fig1.update_layout( #updating the layout of the map
                            mapbox_style="white-bg",            
                            mapbox_layers=[
                                {
                                    "below": 'traces',
                                    "sourcetype": "raster",
                                    "sourceattribution": "United States Geological Survey",
                                    "source": [
                                        "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                                        ]
                                    }
                                ])
                            st.plotly_chart(fig1)   #plotting the map
                            select=select.sort_values(by="Date",ascending=False)  #sorting the data based on the date in descending order
                            animate_select=st.selectbox("Select haplogroup to animate",options=option)  #Using the user input to select the haplogroup to animate
                            animate_data = select[select["mtdna"].isin([animate_select])]       #selecting the haplogroup to animate from the data
                            
                            fig3 = go.Figure( #Initializing the figure
                                data=[  #adding the data to the figure
                                    go.Scattermapbox( #adding the scattermapbox to the figure
                                        lat=animate_data["Lat"], #adding the latitude column to the scattermapbox
                                        lon=animate_data["Long"],      #adding the longitude column to the scattermapbox
                                        mode="lines",#adding the mode to the scattermapbox
                                        line=dict(width=2, color="blue"),#adding the line properties to the scattermapbox
                                        name="Haplogroup Movement",#adding the name to the scattermapbox
                                        hovertext=animate_data["hover"]#adding the hover text to the scattermapbox
                                    ),
                                    go.Scattermapbox(#adding a second scattermapbox to the figure
                                        lat=animate_data["Lat"],    #adding the latitude column to the scattermapbox
                                        lon=animate_data["Long"],   #adding the longitude column to the scattermapbox
                                        mode="lines",   #adding the mode to the scattermapbox
                                        line=dict(width=2, color="blue")        #adding the line properties to the scattermapbox
                                    ),
                                    go.Scattermapbox(   #adding a third scattermapbox to the figure
                                        lat=animate_data["Lat"],        #adding the latitude column to the scattermapbox
                                        lon=animate_data["Long"],       #adding the longitude column to the scattermapbox
                                        mode="markers",     #adding the mode to the scattermapbox
                                        marker=dict(            #adding the marker properties to the scattermapbox
                                            size=6, #adding the size of the marker
                                            color="red"     #adding the color of the marker
                                        ),
                                        name="Haplogroup locations",   #adding the name to the scattermapbox
                                        hovertext=animate_data["hover"]    #adding the hover text to the scattermapbox
                                    )
                                ],
                                layout=go.Layout(  #adding the layout to the figure
                                    title_text="Movement of mtHaplogroups over history", #adding the title to the figure
                                    mapbox_style="white-bg",   #adding the mapbox style to the figure
                                    mapbox_layers=[ #adding the mapbox layers to the figure
                                        {
                                            "below": 'traces',
                                            "sourcetype": "raster",
                                            "sourceattribution": "United States Geological Survey",
                                            "source": [
                                                "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                                            ]
                                        }
                                    ],
                                    mapbox=dict( 
                                        accesstoken="pk.eyJ1IjoibmlraGlsZXNoMjMiLCJhIjoiY2xmMmJucGx6MDFxaTN5bnRpYW12cWxxeCJ9.KeccdtSz6Hc9F_vPrYoiNg",
                                        bearing=0,
                                        center=dict(
                                            lat=select["Lat"].mean(),
                                            lon=select["Long"].mean()),
                                        pitch=0,
                                        zoom=1
                                    ),
                                    updatemenus=[ #adding the updatemenus to the figure which will be used to animate the figure
                                        dict(
                                            type="buttons",
                                            buttons=[dict(label="Play",method="animate",args=[None])] 
                                        )
                                    ]
                                ),
                                frames=[ #The frames are used to animate the figure initializing the frames.
                                    go.Frame(
                                        data=[
                                            go.Scattermapbox( #adding the scattermapbox "markers" to the frame to animate
                                                lat=[list(animate_data["Lat"])[k]],
                                                lon=[list(animate_data["Long"])[k]],
                                                mode="markers",
                                                marker=dict(color="red", size=10),
                                                text=list(animate_data["mtdna"])[k]
                                            ),
                                            
                                            go.Scattermapbox( #adding the scattermapbox "lines" to the frame to animate
                                                lat=list(animate_data["Lat"])[:k+1], #adding the latitude column to the scattermapbox
                                                lon=list(animate_data["Long"])[:k+1], #adding the longitude column to the scattermapbox
                                                mode="lines",
                                                line=dict(width=2, color="orange"),
                                                name="Movement"
                                            )
                                        ]
                                    )
                                    for k in range(1, len(animate_data["mtdna"]))   #for loop to iterate through the data
                                ]
                            )
                            st.plotly_chart(fig3)   #plotting the figure
                    fig4 = px.line(select, x='Date', y='PRS_SCZ', markers=True, color='Region')
                    #fig1.update_traces(line=dict(color = 'rgba(50,50,50,0.2)'))
                    fig4.update_layout(
                        xaxis = dict(autorange="reversed")
                        )
                    
                    st.plotly_chart(fig4)
                    st.success("The maps have been plotted successfully",icon="✅") #printing the success message
            except Exception as e:  #exception handling
                    st.error("An error occurred: {}".format(e)) #printing the error message



        def Onlyfemale_mtdna():        #Creating various functions to plot the data based on the user mode of selection
            mtgeo=data.loc[data["Sex"]=="F"]
            common_code(mtgeo)#calling the common code function to plot the data

        def Onlymale_mtdna():
            mtgeo=data.loc[data["Sex"]=="M"]
            common_code(mtgeo)
            
        def Combined_mtdna():
            mtgeo=data
            common_code(mtgeo)
            
        def Onlymale_ychrom():
            mtgeo=data.loc[data["Sex"]=="M"]
            common_code(mtgeo)
    with col2:
        haplogroup_select=st.selectbox("Select a mode",options=["MtDNA","MtDNA-Male","MtDNA-Female","Y-Chromosome"]) #selecting the mode of selection
    if not haplogroup_select:       #exception handling
        st.error("Please select one category")  #printing the error message
    elif haplogroup_select=="MtDNA":    #if the user selects the mtdna mode
        Combined_mtdna()    #calling the Combined_mtdna function
    elif haplogroup_select=="MtDNA-Male":   #if the user selects the mtdna-male mode
        Onlymale_mtdna() #calling the Onlymale_mtdna function
    elif haplogroup_select=="MtDNA-Female": #If the user selects the mtdna-female mode
        Onlyfemale_mtdna() #calling the Onlyfemale_mtdna function
    elif haplogroup_select=="Y-Chromosome": #If the user selects the y-chrom mode
        Onlymale_ychrom()   #calling the Onlymale_ychrom function
