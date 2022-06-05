import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import altair as alt
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import json
import plotly.express as px

### HELPER FUNCTIONS
@st.cache(allow_output_mutation=True)
def load_data(file):
    df = pd.read_csv(file)
    df['Stars_Num'] = pd.to_numeric(
        df['Stars'].str.strip().str[0], errors='coerce')
    df = df.dropna()
    zipcodes = sorted(df["Zip"].unique().tolist())

    return df, zipcodes


def return_zipcodes(zipcode_filter, zipcodes_selected, df):
    if zipcodes_selected == []:
        properties = sorted(df["Property Name"].unique().tolist())
        return properties
    elif (zipcodes_selected != []) & (zipcode_filter == "Include"):
        filteredProperties = sorted(df.loc[df['Zip'].isin(
            zipcodes_selected), "Property Name"].unique().tolist())
        return filteredProperties
    else:
        filteredProperties = sorted(df.loc[~df['Zip'].isin(
            zipcodes_selected), "Property Name"].unique().tolist())
        return filteredProperties


def filter_dataset(zipcode_filter, zipcodes_selected, df, property_filter, properties_selected):
    if (zipcodes_selected == []) & (zipcodes_selected == []):
        return df
    elif (property_filter == 'Include') & (properties_selected != []):
        filteredDf = df.loc[df['Property Name'].isin(properties_selected), :]
        return filteredDf
    elif (property_filter == 'Exclude') & (properties_selected != []):
        if zipcode_filter == 'Include':
            filteredDf = df.loc[(df['Zip'].isin(zipcodes_selected)) & (
                ~df['Property Name'].isin(properties_selected)), :]
            return filteredDf
        else:
            filteredDf = df.loc[(~df['Zip'].isin(zipcodes_selected)) & (
                ~df['Property Name'].isin(properties_selected)), :]
            return filteredDf
    else:
        if zipcode_filter == 'Include':
            filteredDf = df.loc[df['Zip'].isin(zipcodes_selected), :]
            return filteredDf
        else:
            filteredDf = df.loc[~df['Zip'].isin(zipcodes_selected), :]
            return filteredDf
###

### STREAMLIT APP SETUP
st.set_option('deprecation.showPyplotGlobalUse', False)
st.set_page_config(page_title="Apartment Analysis",page_icon=":office:",layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

selected = option_menu(menu_title=None, options=[
                       "Home", "Area Analysis", "Model Prediction"], icons=["house", "bar-chart-line", "bullseye"],
                       orientation="horizontal")


uploaded_file = st.sidebar.file_uploader(
    "Upload Apartment Reviews CSV File Below:", type=['csv'])


## HOME PAGE SETUP
if selected == "Home":

    st.title("Apartment Analysis App :office:")
    st.header(
        "Welcome to the Apartment Analysis App! :wave: ")
    st.markdown("""
    ### Overview:
    #### :house: Home
    - The start page of the web app and contains instructions
    - **Columns Required in Uploaded Dataset: Property Name, Zip, Rent, Unit Count, Stars, and Review**
    ---
    #### :bar_chart: Area Analysis
    - Provides statistics and visualizations of the apartment information based on user input
    - **Upload your Apartment Reviews CSV in side bar otherwise analysis can't be performed**
    - Once the file is uploaded and you are on the Area Analysis page, the sidebar will change to allow you to filter zip codes and properties from analysis
    - You can change filters to either include/exclude zip codes and properties from analysis by selecting buttons and drop down options
    - No selection will result in all records in the dataset to be considered
    - To generate the Area Analysis, select the _Generate Report_ button at the bottom of the sidebar
    - Output will consist of metrics, bar charts, and choropleth maps
    ---
    #### :dart: Model Prediction
    - Compares model predictions to actual averages and shows descriptive statistics for individual properties
    - **Upload your Apartment Reviews CSV in side bar otherwise analysis can't be performed**
    - You can select a zip code to analyze with the drop down on the page
    - After a zip code is selected, the page will display how the model's predicted average rent compares to the gathered data
    - Statistics and word clouds will be displayed for each property in the zip code
    """)


## AREA ANALYSIS PAGE SETUP
if selected == "Area Analysis":
    try:
        df, zipcodes = load_data(uploaded_file)

        st.sidebar.header("Filter Options")
        zipcode_filter = st.sidebar.radio(
            "Zip Code Filter Method", ["Include", "Exclude"], key="zipcode_bubble")
        zipcodes_selected = st.sidebar.multiselect(
            "Select Zip Codes", zipcodes)

        property_filter = st.sidebar.radio(
            "Property Filter Method", ["Include", "Exclude"], key="property_bubble")
        properties = return_zipcodes(zipcode_filter, zipcodes_selected, df)
        properties_selected = st.sidebar.multiselect(
            "Select Properties", properties)

        st.sidebar.header("Generate Report")
        button_pressed = st.sidebar.button("Generate Report")

        if button_pressed:
            df = filter_dataset(zipcode_filter, zipcodes_selected,
                                df, property_filter, properties_selected)
            st.write(df)

            st.markdown("""
            ---
            """)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="Count of Reviews",
                    value=f"{len(df['Stars_Num']):,} Reviews",
                )
                
            with col2:
                st.metric(
                    label="Average Review Rating",
                    value=f"{round(df['Stars_Num'].mean(),2)} Stars"
                )
                starRating = ":star:" * int(round(df['Stars_Num'].mean(),0))
                st.write(starRating)
                

            with col3:
                st.metric(
                    label="Total Properties",
                    value=f"{len(df['Property Name'].unique()):,} Properties",
                )

            with col4:
                st.metric(
                    label="Total Zip Codes",
                    value=f"{len(df['Zip'].unique()):,} Zip Codes",
                )

            st.markdown("""
            ---
            """)

            col2_1, col2_2 = st.columns(2)

            with col2_1:
                starGroup = df.groupby('Stars').agg(Count=pd.NamedAgg(
                    column='Stars_Num', aggfunc='count')).reset_index()

                barchart = alt.Chart(starGroup).mark_bar().encode(
                    x='Stars',
                    y=alt.Y('Count',title='Count of Reviews'),
                    opacity=alt.value(0.8),
                    color=alt.value('red')
                )

                st.subheader("Distribution of Star Reviews")
                st.altair_chart(barchart, use_container_width=True)
            
            with col2_2:
                rentAggDf = df.groupby("Property Name").agg(Rent=pd.NamedAgg(
                    column='Rent',aggfunc='mean')).reset_index()
                histogram = alt.Chart(rentAggDf).mark_bar().encode(
                    alt.X("Rent:Q", bin=alt.Bin(extent=[0,max(rentAggDf["Rent"])],step=500),title="Rent ($)"),
                    y=alt.Y('count()',title="Count of Properties"),
                    opacity=alt.value(0.8),
                    color=alt.value('red'))
                
                st.subheader("Distribution of Rent Prices")
                st.altair_chart(histogram, use_container_width=True)

            st.markdown("""
            ---
            """)

            ### SETUP FOR MAP DATA
            with open("il_illinois_zip_codes_geo.min.json", "r") as jsonfile:
                data = json.load(jsonfile)

            mapData = data
            df2 = df.groupby('Zip').agg(
                {'Rent': ['mean', 'count']}).reset_index()
            df3 = df.groupby('Zip')['Property Name'].nunique().reset_index()
            df3 = df3.rename(columns={'Property Name':'Count of Properties'})
            ###
        
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                fig1 = px.choropleth(pd.concat([df2['Zip'], df2['Rent']['mean']], axis=1),
                                    geojson=mapData,
                                    locations='Zip',
                                    color='mean',
                                    color_continuous_scale="Reds",
                                    range_color=(min(df2['Rent']['mean']), max(
                                        df2['Rent']['mean'])),
                                    featureidkey="properties.ZCTA5CE10",
                                    scope="usa",
                                    labels={'Rent': 'Rent_Category'})
                fig1.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},coloraxis_colorbar=dict(title="Average Rent ($)"))
                fig1.update_geos(fitbounds="locations")
                st.subheader("Average Rent by Zip Code")
                st.plotly_chart(fig1)

            with col3_2:
                fig2 = px.choropleth(pd.concat([df2['Zip'], df2['Rent']['count']], axis=1),
                                    geojson=mapData,
                                    locations='Zip',
                                    color='count',
                                    color_continuous_scale="Reds",
                                    range_color=(min(df2['Rent']['count']), max(
                                        df2['Rent']['count'])),
                                    featureidkey="properties.ZCTA5CE10",
                                    scope="usa",
                                    labels={'Rent': 'Rent_Category'})
                fig2.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0},coloraxis_colorbar=dict(title="Count of Reviews"))
                fig2.update_geos(fitbounds="locations")
                st.subheader("Count of Reviews by Zip Code")
                st.plotly_chart(fig2)

            col4_1, col4_2 = st.columns(2)
            with col4_1:
                fig3 = px.choropleth(df3,
                                    geojson=mapData,
                                    locations='Zip',
                                    color='Count of Properties',
                                    color_continuous_scale="Reds",
                                    range_color=(min(df3['Count of Properties']), max(
                                        df3['Count of Properties'])),
                                    featureidkey="properties.ZCTA5CE10",
                                    scope="usa",
                                    labels={'Rent': 'Rent_Category'})
                fig3.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
                fig3.update_geos(fitbounds="locations")
                st.header("Count of Properties by Zip Code")
                st.plotly_chart(fig3)

            with col4_2:
                pass

    except Exception:
        st.header("Please upload the real estate file in the Side Bar.")


## MODEL PREDICTION PAGE SETUP
if selected == "Model Prediction":
    predictions = pd.read_csv("model_predictions.csv")
    try:
        df, zipcodes = load_data(uploaded_file)

        zipcode = st.selectbox("Please Select a Zip Code", ['<Select>']+sorted(df['Zip'].unique()),0)
        if zipcode != '<Select>':
            try:
                col1, col2, col3 = st.columns(3)
                with col1:
                    filtered_zip = df[df['Zip']==zipcode]
                    unique_properties = filtered_zip.drop_duplicates(subset=["Property Name"])
                    st.metric(
                        label=f"Average Rent in {zipcode} Zip Code",
                        value=f"${round(unique_properties['Rent'].mean(),0):,.0f}"
                    )
                with col2:
                    st.metric(
                        label="Model Prediction",
                        value=f"${round(list(predictions[predictions['Zip']==zipcode]['Prediction'])[0],0):,.0f}"
                    )
                with col3:
                    predictionError = round(list(predictions[predictions['Zip']==zipcode]['Prediction'])[0],0)-round(unique_properties[unique_properties['Zip']==zipcode]['Rent'].mean(),0)
                    
                    if predictionError > 0:
                        errorLabel = 'Overestimated'
                    elif predictionError < 0:
                        errorLabel = 'Underestimated'
                    else:
                        errorLabel = 'Correct'
                    
                    deltaLabel = '-' if predictionError < 0 else ''
                    st.metric(
                        label="Prediction Error",
                        value=errorLabel,
                        delta=f"{deltaLabel}${abs(predictionError):,.0f}"
                    )
            
            except Exception:
                st.header("Sorry, there wasn't a prediction for this zipcode.")

            for prop in df[df['Zip']==zipcode]["Property Name"].unique():
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.subheader(f"{prop}")
                with col2:
                    st.metric(label='Property Rent',value=f"${round(list(df[df['Property Name']==prop]['Rent'])[0],0):,.0f}")
                with col3:
                    st.metric(label='Unit Count',value=f"{round(list(df[df['Property Name']==prop]['Unit Count'])[0],0):,.0f}")
                with col4:
                    st.metric(label="Average Review Rating", value=f"{round(df[df['Property Name']==prop]['Stars_Num'].mean(),2)} Stars")
                    starRating = ":star:" * int(round(df[df['Property Name']==prop]['Stars_Num'].mean(),0))
                    st.write(starRating)
                    st.write(f"Count of Reviews: {len(df[df['Property Name']==prop]['Stars_Num'])}")
                with col5:
                    wordcloud = WordCloud().generate(
                        ' '.join(df[df["Property Name"] == prop]['Review']))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis("off")
                    st.pyplot()
                st.markdown("""
                ---
                """)

    except Exception:
        st.header("Please upload the real estate file in the Side Bar.")
###