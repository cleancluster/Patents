import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu


import time
import pandas as pd
import plotly.express as px
import geopandas as gpd
import altair as alt
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None  # default='warn'

#For Lottie animations
from streamlit_lottie import st_lottie
from streamlit_lottie import st_lottie_spinner
import requests

#For login part (necsesary for streamlit_authenticator)
import yaml
from yaml import load, dump
from yaml.loader import SafeLoader

#To add logo
from PIL import Image

# To send emails (For password recovery)
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#To delete Admin page, when user is not admin
from pathlib import Path
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5, 
    get_pages,
    _on_pages_changed
)

#Import data from Google sheets
#from google.oauth2 import service_account
#from shillelagh.backends.apsw.db import connect

# Sets up Favicon, webpage title and layout
favicon = Image.open(r"./assets/favicon.ico")

st.set_page_config(
    page_title = "CLEAN Insights",
    page_icon = favicon,
    layout="wide"
)

# Top sidebar CLEAN logo + removal of "Made with Streamlit" & Streamlit menu + no padding top and bottom
def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://cleancluster.dk/wp-content/uploads/2022/09/CLEAN-logo-white.png);
                background-repeat: no-repeat;
                background-position: 20px 20px;
                background-size: 265px;
                width: 325px;
                height: 215px;
            }

            footer {visibility: hidden;}
            #MainMenu {visibility: hidden;}

            div.block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                }

        </style>
        """,
        unsafe_allow_html=True,
    )
add_logo()

# Login menu in sidebar
#with open('./assets/config.yaml') as file:
#    config = yaml.load(file, Loader=SafeLoader)
#
#with open(r"./assets/connected_dots_viz.html") as f: 
#    html_data = f.read()
#
#authenticator = stauth.Authenticate(
#    config['credentials'],
#    config['cookie']['name'],
#    config['cookie']['key'],
#    config['cookie']['expiry_days'],
#    config['preauthorized']
#)

#name, authentication_status, username = authenticator.login('Login', 'sidebar')

##### Helper functions #####
# Get Lottie animation
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Delete (hide) a page
def delete_page(main_script_path_str, page_name):

    current_pages = get_pages(main_script_path_str)

    for key, value in current_pages.items():
        if value['page_name'] == page_name:
            del current_pages[key]
            break
        else:
            pass
    _on_pages_changed.send()

# Add (make visible) a page 
def add_page(main_script_path_str, page_name):
    
    pages = get_pages(main_script_path_str)
    main_script_path = Path(main_script_path_str)
    pages_dir = main_script_path.parent / "pages"

    script_path = [f for f in list(pages_dir.glob("*.py"))+list(main_script_path.parent.glob("*.py")) if f.name.find(page_name) != -1][0]
    script_path_str = str(script_path.resolve())
    pi, pn = page_icon_and_name(script_path)
    psh = calc_md5(script_path_str)
    pages[psh] = {
        "page_script_hash": psh,
        "page_name": pn,
        "icon": pi,
        "script_path": script_path_str,
    }
    _on_pages_changed.send()
    ##### Helper functions #####
def convert_excel(path, sheet_name = 'Ark1', pri = False):
    df = pd.read_excel(path, sheet_name)
    if pri:
        print('The first 5 rows of the loaded data:')
        # display_html(df.head())
    return df

def choose_headers(df, headers_list, pri):
    temp_df = pd.DataFrame()
    for i in range(len(headers_list)):
        if pri:
            print('Choosing the column "', headers_list[i], '"')
        temp_df = pd.concat([temp_df, df[headers_list[i]]], axis = 1)
    return temp_df

def remove_nan(df):
    df = df.dropna().reset_index(drop=True)
    return df

def choose_subsets(df, column_str_list, subset_str_list, pri):
    temp_df = pd.DataFrame()
    for i in range(len(column_str_list)):
        if pri:
            print('Choosing the rows with "', subset_str_list[i], '" in the "', column_str_list[i], '" column.')
        temp_df = pd.concat([temp_df, df[df[column_str_list[i]] == subset_str_list[i]]])
    return temp_df

    
delete_page("🌐 Ecosystem Insights", "Admin")

#delete_page("🌐 Ecosystem Insights", "Page")
#add_page("🌐 Ecosystem Insights", "Page")



#If user is not logged in and has not tried loggin in
#if st.session_state["authentication_status"] == None:
#    st.sidebar.warning('Please enter your username and password. \n \n For login credentials, please contact esh@cleancluster.dk 📧')
#    st.components.v1.html(html_data, width=None, height=775, scrolling=False)


#If user has tried loggin in, but has not entered correct credentials
"""
elif st.session_state["authentication_status"] == False:
    st.sidebar.error("Username/password is incorrect. Do you want to reset your password?")
    
    st.components.v1.html(html_data, width=None, height=775, scrolling=False)
    
    #Forgot Password function
    try:
        username_forgot_pw, email_forgot_password, random_password = authenticator.forgot_password('Reset password', 'sidebar')
        
       
        #Send email to user with new password
        if username_forgot_pw:
            try:
                subject = "Your new password for CLEAN Insights"
                sender_email = "noreply@cleancluster.dk"
                receiver_email = email_forgot_password
                password = st.secrets["server_password"]
                port = 587
                smtp_server = "smtp.office365.com"

                # Create a multipart message and set headers
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = receiver_email
                message["Subject"] = subject

                # Add body to email
                html = ""\
                <html>
                <body>
                    <p>Hi,<br><br>
                    <span>Here are your new login credentials for CLEAN Insights:</span><br><br>
                    <span><b>Username:</b> $(username)</span><br>
                    <span><b>New Password:</b> $(password)</span><br><br>
                    <span>Best regards</span><br>
                    <span>CLEAN</span>
                    </p>
                </body>
                </html>
                ""
                html = html.replace("$(username)", username_forgot_pw)
                html = html.replace("$(password)", random_password)

                part1 = MIMEText(html, "html")
                message.attach(part1)

                # Log in to server using secure context and send email
                context = ssl.create_default_context()
                with smtplib.SMTP(smtp_server, port) as server:
                    server.starttls(context=context)
                    server.login(sender_email, password)
                    server.ehlo()
                    server.sendmail(sender_email, receiver_email, message.as_string())
                    server.ehlo()
                    
                st.sidebar.success('New password was sent to your email ✅')

                #Update credetials in file
                with open('./assets/config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)

            #Catch email sending error
            except Exception as e:
                st.write(e)
                st.sidebar.warning(e)
        elif username_forgot_pw == False:
            st.sidebar.error('No such username exist. For login credentials, please contact esh@cleancluster.dk 📧')
    except Exception as e:
        st.error(e)
"""
#If user has logged in. 

# st.header("**CLEAN INSIGHTS**")
st.write(f'Welcome *{st.session_state["name"]}* 👋')

st.sidebar.info('This application is developed so that you can gain insights in the danish ecosystem of companies working with environmental technology.', icon="ℹ️")
#authenticator.logout('Logout', 'sidebar')

# Create a connection object.
#credentials = service_account.Credentials.from_service_account_info(
#    st.secrets["gcp_service_account"], 
#    scopes=["https://www.googleapis.com/auth/spreadsheets",],)

#connection = connect(":memory:", adapter_kwargs={
#    "gsheetsapi" : { 
#    "service_account_info" : {
#        "type" : st.secrets["gcp_service_account"]["type"],
#        "project_id" : st.secrets["gcp_service_account"]["project_id"],
#        "private_key_id" : st.secrets["gcp_service_account"]["private_key_id"],
#        "private_key" : st.secrets["gcp_service_account"]["private_key"],
#        "client_email" : st.secrets["gcp_service_account"]["client_email"],
#        "client_id" : st.secrets["gcp_service_account"]["client_id"],
#        "auth_uri" : st.secrets["gcp_service_account"]["auth_uri"],
#        "token_uri" : st.secrets["gcp_service_account"]["token_uri"],
#        "auth_provider_x509_cert_url" : st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
#        "client_x509_cert_url" : st.secrets["gcp_service_account"]["client_x509_cert_url"],
#        }
#    },
#})

#cursor = connection.cursor()
#sheet_url = st.secrets["private_gsheets_url"]

#query = f'SELECT * FROM "{sheet_url}"'
#st.write(query)

# Perform SQL query on the Google Sheet.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
# @st.cache_data(ttl=600)
# def run_query(query):
#    rows = cursor.execute(query, headers=1)
#    rows = rows.fetchall()
#    return rows

#sheet_url = st.secrets["private_gsheets_url"]
#rows = run_query(f'SELECT * FROM "{sheet_url}"')

#for row in rows:
#    st.write(row)


Preferences = st.selectbox(
"Your preferences:",
    ('Choose an option', 'Show me all the data!', 'Let me filter!', 'Show me the quick view options!'), index=0)

progress_bar = st.progress(0)
if Preferences != 'Choose an option':
    for perc_completed in range(100):
        time.sleep(0.02)
        progress_bar.progress(perc_completed+1)

    progress_bar.empty()

# Reads data from CSV
df = pd.read_csv("Miljøteknologi økosystem 1.0 –Kopi.csv")

if Preferences == 'Show me all the data!':

    st.success("Sure! Here you go ✅")

    col1, col2, col3, col4, col5 = st.columns(5)

    privateWaterUtilities = (df['Privat vandværk'].sum().astype(int))
    utilities = df['Kategorier v. metodeworkshop'].value_counts()["Forsyningsselskaber"]
    publicWaterUtilities = utilities-privateWaterUtilities

    privateWaterUtilities = str(privateWaterUtilities)
    publicWaterUtilities = str(publicWaterUtilities)
    
    with col1:
        st.metric("Total amount of organisations mapped:", len(df.index), help="This does not include public institutions or knowledge instituions like Universities or GTS institutes. It does also not include Networks, NGO's, industry organisations and likewise")
        
        waterAreaTotal= df['Vand'].sum()
        st.metric("Works with Water", waterAreaTotal.astype(int), help = f" {privateWaterUtilities} private water utilities is not included in this count")

    with col2:
        st.metric("Hereof utilities:", utilities.astype(int), help = f"Of the total amount of organisations mapped, {privateWaterUtilities} is private water utilities and {publicWaterUtilities} is water supply and waste water companies owned by municipalities")
        
        climateAdaptionTotal= df['Klimatilpasning'].sum()
        st.metric("Works with Climate Adaption", climateAdaptionTotal.astype(int))

    with col3:
        employeesTotal = df['Antal ansatte'].sum()
        st.metric("Employees", employeesTotal.astype(int), help="⚠️ Be aware that no. of employees is indicative only. The Danish Business Authority does not necesarrily recieve employment information about all companies")
        
        wasteRessourcesMaterialsTotal= df['Affald, ressourcer & materialer'].sum()
        st.metric("Works with Waste, Ressources and Materials", wasteRessourcesMaterialsTotal.astype(int))

    with col4:
        advisorsTotal= df['Rådgiver'].sum()
        st.metric("Consultants/Advisors", advisorsTotal.astype(int))
        
        airTotal= df['Luft'].sum()
        st.metric("Works with Air", airTotal.astype(int))        
    
    with col5:
        produceresTotal= df['Producent/Leverandør'].sum()
        st.metric("Producer/supplies", produceresTotal.astype(int))
    
        natureTotal= df['Natur'].sum()
        st.metric("Works with Nature", natureTotal.astype(int))
    
    #Warning regarding no of employees
    st.info("Be aware that comapnies can be work with multiple different environmental areas. ", icon="⚠️")
    st.markdown("---")

    # Map view
    st.title("Here's a map view:")

    mapData = df[df.Land != 'Grønland'].fillna(0)
    mapData['latitude']=pd.to_numeric(mapData['Latitude']) 
    mapData['longitude']=pd.to_numeric(mapData['Longitude'])
    gdf = gpd.GeoDataFrame(mapData, geometry=gpd.points_from_xy(mapData.Longitude, mapData.Latitude))
    px.set_mapbox_access_token("pk.eyJ1IjoiY2xlYW5hZG1pbiIsImEiOiJjbGVicDJ6cjAwZjlqM3dvZTNyOHlxbDIyIn0.Wf8RScJeyR6fHovnPIy5IA")

    mapType = st.radio('What map type do you want to view?', ('Simple Scatter map', 'Scatter map colored by region', 'Scatter Map colored by region and companies sized by no. of employees'))

    if mapType == 'Simple Scatter map':
        fig = px.scatter_mapbox(gdf,
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            hover_name="Organisationsnavn",
            hover_data=["CVR", "Hjemmeside", "Adresse"],
            height = 750,
            zoom=6,
            mapbox_style='dark')

        st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit") 

    elif mapType == 'Scatter map colored by region':
        fig = px.scatter_mapbox(gdf,
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            hover_name="Organisationsnavn",
            color="Region",
            hover_data=["CVR", "Hjemmeside", "Adresse"],
            height = 750,
            zoom=6,
            mapbox_style='dark')

        st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")             

    elif mapType == 'Scatter Map colored by region and companies sized by no. of employees':
        fig = px.scatter_mapbox(gdf,
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            hover_name="Organisationsnavn",
            color="Region",
            size="Antal ansatte", size_max=40,
            hover_data=["CVR", "Hjemmeside", "Adresse"],
            height = 750,
            zoom=6,
            mapbox_style='dark')

        st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit") 

    st.info("pssst! There's also three companies in Greenland (not plotted): FRESE A/S, Fresh Cool Water of  Greenland I/S and WSP Arctic A/S.", icon="ℹ️")
    
    mapDataDf = df['Region']
    mapDataDf = pd.DataFrame(data=mapDataDf)
    mapDataDf = mapDataDf.replace(to_replace="Kolding", value="Region Midtjylland")['Region']
    mapDataDf = mapDataDf.value_counts()

    container_3 = st.empty()
    button_E = container_3.button('Show data table', key="mapDataButton")
    if button_E:
        st.write(mapDataDf)
        container_3.empty()
        button_F = container_3.button('Hide data table')
    

    #Focus area distribution
    st.title('Focus area distribution:')
    focusArea = {'Environmental Area': ['Vand','Klimatilpasning','Affald, ressourcer & materialer','Luft  ','Natur'], 'Companies': [waterAreaTotal.astype(int),climateAdaptionTotal.astype(int),wasteRessourcesMaterialsTotal.astype(int),airTotal.astype(int),natureTotal.astype(int)]}
    focusAreaDf = pd.DataFrame(data=focusArea).sort_values(by='Companies', ascending=False)
    
    focusAreaChart= px.bar(
        focusAreaDf,
        x= 'Companies',
        y= 'Environmental Area',
        orientation = "h",
        title ="<b>Focus area distribution</b>",
        color = 'Environmental Area',
        text_auto=True

    )

    focusAreaChart.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False)),
        showlegend=False
    )

    st.plotly_chart(focusAreaChart, use_container_width=True)

    container_1 = st.empty()
    button_A = container_1.button('Show data table', key="focusAreaDataButton")
    if button_A:
        st.write(focusAreaDf)
        container_1.empty()
        button_B = container_1.button('Hide data table')


    #Data sources distribution
    #import plotly.graph_objects as go
    #dataSource = df['Kilde'].value_counts().rename_axis('Kilde').reset_index(name='Total')

    #fig = px.bar(
    #    dataSource,
    #    x='Total',
    #    y='Kilde',
    #    orientation = "h",
    #    color = 'Kilde'
    #)

    #fig.update_layout(
    #    plot_bgcolor="rgba(0,0,0,0)",
    #    xaxis=(dict(showgrid=False))
    #)
    
    #st.plotly_chart(fig, use_container_width=True)

    #Number of Employees
    st.title('Employee intervals:')
    employeesIntervals= df['Antal ansatte (interval)'].value_counts().rename_axis('Interval').reset_index(name='Employees')
    employeesIntervals = employeesIntervals[employeesIntervals.Interval != '0-0']

    employeesIntervalsChart= px.bar(
        employeesIntervals,
        x= 'Employees',
        y= 'Interval',
        orientation = "h",
        title ="<b>Employees (interval)</b>",
        color = 'Interval',
        text_auto=True

    )

    employeesIntervalsChart.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False)),
        showlegend=False
    )

    st.plotly_chart(employeesIntervalsChart, use_container_width=True)

    container_2 = st.empty()
    button_C = container_2.button('Show data table', key="employeesIntervalsButton")
    if button_C:
        st.write(employeesIntervals)
        container_2.empty()
        button_D = container_2.button('Hide data table')   





    
        




    

        

    



if Preferences == 'Show me the quick view options!':
    quickViewOptions = st.selectbox(
        "Select a quick view:",
        ('All companies, excl. utilities', 'All SMEs, excl. utilities', 'All large companies with 500+ employees, excluding utilities', 'Only public utilities', 'Only private water plants'))
    if quickViewOptions == 'All companies, excl. utilities':
        
        df.rename(columns = {'Kategorier v. metodeworkshop':'Kategorier_v_metodeworkshop'}, inplace = True)
        df = df[df.Kategorier_v_metodeworkshop != 'Forsyningsselskaber']

        st.success("Sure! Here you go ✅")

        col1, col2, col3, col4, col5 = st.columns(5)

        privateWaterUtilities = (df['Privat vandværk'].sum().astype(int))
        utilities = 0

        publicWaterUtilities = utilities-privateWaterUtilities

        privateWaterUtilities = str(privateWaterUtilities)
        publicWaterUtilities = str(publicWaterUtilities)
        
        with col1:
            st.metric("Total amount of organisations mapped:", len(df.index), help="This does not include public institutions or knowledge instituions like Universities or GTS institutes. It does also not include Networks, NGO's, industry organisations and likewise")
            
            waterAreaTotal= df['Vand'].sum()
            st.metric("Works with Water", waterAreaTotal.astype(int), help = f" {privateWaterUtilities} private water utilities is not included in this count")

        with col2:
            st.metric("Hereof utilities:", utilities, help = f"Of the total amount of organisations mapped, {privateWaterUtilities} is private water utilities and {publicWaterUtilities} is water supply and waste water companies owned by municipalities")
            
            climateAdaptionTotal= df['Klimatilpasning'].sum()
            st.metric("Works with Climate Adaption", climateAdaptionTotal.astype(int))

        with col3:
            employeesTotal = df['Antal ansatte'].sum()
            st.metric("Employees", employeesTotal.astype(int), help="⚠️ Be aware that no. of employees is indicative only. The Danish Business Authority does not necesarrily recieve employment information about all companies")
            
            wasteRessourcesMaterialsTotal= df['Affald, ressourcer & materialer'].sum()
            st.metric("Works with Waste, Ressources and Materials", wasteRessourcesMaterialsTotal.astype(int))

        with col4:
            advisorsTotal= df['Rådgiver'].sum()
            st.metric("Consultants/Advisors", advisorsTotal.astype(int))
            
            airTotal= df['Luft'].sum()
            st.metric("Works with Air", airTotal.astype(int))        
        
        with col5:
            produceresTotal= df['Producent/Leverandør'].sum()
            st.metric("Producer/supplies", produceresTotal.astype(int))
        
            natureTotal= df['Natur'].sum()
            st.metric("Works with Nature", natureTotal.astype(int))
        
        #Warning regarding no of employees
        st.info("Be aware that comapnies can be work with multiple different environmental areas. ", icon="⚠️")
        st.markdown("---")

        # Map view
        st.title("Here's a map view:")

        mapData = df[df.Land != 'Grønland'].fillna(0)
        mapData['latitude']=pd.to_numeric(mapData['Latitude']) 
        mapData['longitude']=pd.to_numeric(mapData['Longitude'])
        gdf = gpd.GeoDataFrame(mapData, geometry=gpd.points_from_xy(mapData.Longitude, mapData.Latitude))
        px.set_mapbox_access_token("pk.eyJ1IjoiY2xlYW5hZG1pbiIsImEiOiJjbGVicDJ6cjAwZjlqM3dvZTNyOHlxbDIyIn0.Wf8RScJeyR6fHovnPIy5IA")

        mapType = st.radio('What map type do you want to view?', ('Simple Scatter map', 'Scatter map colored by region', 'Scatter Map colored by region and companies sized by no. of employees'))

        if mapType == 'Simple Scatter map':
            fig = px.scatter_mapbox(gdf,
                lat=gdf.geometry.y,
                lon=gdf.geometry.x,
                hover_name="Organisationsnavn",
                hover_data=["CVR", "Hjemmeside", "Adresse"],
                height = 750,
                zoom=6,
                mapbox_style='dark')

            st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit") 

        elif mapType == 'Scatter map colored by region':
            fig = px.scatter_mapbox(gdf,
                lat=gdf.geometry.y,
                lon=gdf.geometry.x,
                hover_name="Organisationsnavn",
                color="Region",
                hover_data=["CVR", "Hjemmeside", "Adresse"],
                height = 750,
                zoom=6,
                mapbox_style='dark')

            st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit")             

        elif mapType == 'Scatter Map colored by region and companies sized by no. of employees':
            fig = px.scatter_mapbox(gdf,
                lat=gdf.geometry.y,
                lon=gdf.geometry.x,
                hover_name="Organisationsnavn",
                color="Region",
                size="Antal ansatte", size_max=40,
                hover_data=["CVR", "Hjemmeside", "Adresse"],
                height = 750,
                zoom=6,
                mapbox_style='dark')

            st.plotly_chart(fig, use_container_width=True, sharing="streamlit", theme="streamlit") 

        st.info("pssst! There's also three companies in Greenland (not plotted): FRESE A/S, Fresh Cool Water of  Greenland I/S and WSP Arctic A/S.", icon="ℹ️")
        mapDataDf = df['Region']
        mapDataDf = pd.DataFrame(data=mapDataDf)
        mapDataDf = mapDataDf.replace(to_replace="Kolding", value="Region Midtjylland")['Region']
        mapDataDf = mapDataDf.value_counts()

        container_3 = st.empty()
        button_E = container_3.button('Show data table', key="mapDataButton")
        if button_E:
            st.write(mapDataDf)
            container_3.empty()
            button_F = container_3.button('Hide data table')

        #Focus area distribution
        st.title('Focus area distribution:')
        focusArea = {'Environmental Area': ['Vand','Klimatilpasning','Affald, ressourcer & materialer','Luft','Natur'], 'Companies': [waterAreaTotal.astype(int),climateAdaptionTotal.astype(int),wasteRessourcesMaterialsTotal.astype(int),airTotal.astype(int),natureTotal.astype(int)]}
        focusAreaDf = pd.DataFrame(data=focusArea).sort_values(by='Companies', ascending=False)
        
        focusAreaChart= px.bar(
            focusAreaDf,
            x= 'Companies',
            y= 'Environmental Area',
            orientation = "h",
            title ="<b>Focus area distribution</b>",
            color = 'Environmental Area',
            text_auto=True

        )

        focusAreaChart.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=(dict(showgrid=False)),
            showlegend=False
        )

        st.plotly_chart(focusAreaChart, use_container_width=True)

        container_1 = st.empty()
        button_A = container_1.button('Show data table', key="focusAreaDataButton")
        if button_A:
            st.write(focusAreaDf)
            container_1.empty()
            button_B = container_1.button('Hide data table')


        #Data sources distribution
        #import plotly.graph_objects as go
        #dataSource = df['Kilde'].value_counts().rename_axis('Kilde').reset_index(name='Total')

        #fig = px.bar(
        #    dataSource,
        #    x='Total',
        #    y='Kilde',
        #    orientation = "h",
        #    color = 'Kilde'
        #)

        #fig.update_layout(
        #    plot_bgcolor="rgba(0,0,0,0)",
        #    xaxis=(dict(showgrid=False))
        #)
        
        #st.plotly_chart(fig, use_container_width=True)

        #Number of Employees
        st.title('Employee intervals:')
        employeesIntervals= df['Antal ansatte (interval)'].value_counts().rename_axis('Interval').reset_index(name='Employees')
        employeesIntervals = employeesIntervals[employeesIntervals.Interval != '0-0']


        employeesIntervalsChart= px.bar(
            employeesIntervals,
            x= 'Employees',
            y= 'Interval',
            orientation = "h",
            title ="<b>Employees (interval)</b>",
            color = 'Interval',
            text_auto=True

        )

        employeesIntervalsChart.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=(dict(showgrid=False)),
            showlegend=False
        )

        st.plotly_chart(employeesIntervalsChart, use_container_width=True)

        container_2 = st.empty()
        button_C = container_2.button('Show data table', key="employeesIntervalsButton")
        if button_C:
            st.write(employeesIntervals)
            container_2.empty()
            button_D = container_2.button('Hide data table')   





if Preferences == 'Let me filter!':
    st.write("Sure! Please start by selecting the regions you are interested in.")
    
    region_options = {
        "Region Nordjylland":"North Denmark Region",
        "Region Midtjylland":"Central Denmark Region",
        "Region Syddanmark":"Region of Southern Denmark",
        "Region Hovedstaden":"Captial Region of Denmark",
        "Region Sjælland":"Region Zealand",
    }
    
            # on the first run add variables to track in state
    if "all_option" not in st.session_state:
        st.session_state.all_option = True
        st.session_state.selected_options = ['Region Nordjylland', 'Region Midtjylland', 'Region Syddanmark', 'Region Hovedstaden', 'Region Sjælland']

    def check_change():
    # this runs BEFORE the rest of the script when a change is detected 
    # from your checkbox to set selectbox
        if st.session_state.all_option:
            st.session_state.selected_options = ['Region Nordjylland', 'Region Midtjylland', 'Region Syddanmark', 'Region Hovedstaden', 'Region Sjælland']
        else:
            st.session_state.selected_options = []
        return

    def multi_change():
    # this runs BEFORE the rest of the script when a change is detected
    # from your selectbox to set checkbox
        if len(st.session_state.selected_options) == 5:
            st.session_state.all_option = True
        else:
            st.session_state.all_option = False
        return

    selected_options = st.multiselect("Select one or more options:",
                ['Region Nordjylland', 'Region Midtjylland', 'Region Syddanmark', 'Region Hovedstaden', 'Region Sjælland'],key="selected_options", on_change=multi_change, format_func=lambda x: region_options.get(x))

    all = st.checkbox("Select all", key='all_option',on_change= check_change)
            # Ændring som led i at udvikle det som mere object oriented.
            # Vil tage udgangspunkt i streamlit_indberetning app fra streamlit_tests repo.
    df_altered = df

