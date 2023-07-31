import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from streamlit_extras.chart_container import chart_container


import time
from streamlit_js_eval import streamlit_js_eval, copy_to_clipboard, create_share_link, get_geolocation
import pandas as pd
import plotly.express as px
import geopandas as gpd
import altair as alt
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from six import BytesIO
from pyxlsb import open_workbook as open_xlsb
import plotly.graph_objects as go
import re
import squarify

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.mode.chained_assignment = None  # default='warn'

#For login part (necsesary for streamlit_authenticator)
import yaml
from yaml import load, dump
from yaml.loader import SafeLoader

#To add logo
from PIL import Image

# Sets up Favicon, webpage title and layout
favicon = Image.open(r"./assets/favicon.ico")

st.set_page_config(
    page_title = "Patents dashboard",
    page_icon = favicon,
    layout="wide"
)

# Top sidebar logo + removal of "Made with Streamlit" & Streamlit menu + no padding top and bottom
def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url("https://cleancluster.box.com/shared/static/n193qtvcr80u4xpop4koqm5wkruo20xw.png");
                background-repeat: no-repeat;
                background-position: 20px 20px;
                background-size: 265px;
                width: 325px;
                height: 200px;
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

#To delete Admin page, when user is not admin
from pathlib import Path
from streamlit.source_util import (
    page_icon_and_name, 
    calc_md5, 
    get_pages,
    _on_pages_changed
)

# Login menu in sidebar
with open('./assets/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Login', 'sidebar')

##### Helper functions #####
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

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def to_excel(df: pd.DataFrame):
    output = BytesIO() 
    writer = pd.ExcelWriter(output, engine='xlsxwriter') 
    df.to_excel(writer, sheet_name='Sheet1') 
    writer.close() 
    processed_data = output.getvalue() 
    return processed_data

@st.cache_data

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

#Inital hides admin page and starts particles vizualisation (height cannot be set dynamically - wokring issue)
delete_page("📄 Patent Applications", "Admin")


#If user is not logged in and has not tried loggin in
if st.session_state["authentication_status"] == None:
    st.sidebar.warning('Please enter your username and password 🔑')

    #Particles vizualisation
    with open(r"./assets/connected_dots_viz.html") as f: 
        html_data = f.read()
        browser_width = streamlit_js_eval(js_expressions='window.innerWidth', key = 'WIDTH')
        st.components.v1.html(html_data, width=browser_width, height=775, scrolling=False)

#If user has tried loggin in, but has not entered correct credentials
elif st.session_state["authentication_status"] == False:
    st.sidebar.error("Username/password is incorrect.")
    #Particles vizualisation
    with open(r"./assets/connected_dots_viz.html") as f: 
        html_data = f.read()
        browser_width = streamlit_js_eval(js_expressions='window.innerWidth', key = 'WIDTH')
        st.components.v1.html(html_data, width=browser_width, height=775, scrolling=False)

#If user has logged in. 
elif st.session_state["authentication_status"]:
    st.header("Key metrics")

    if "rådata" not in st.session_state:
        st.session_state.rådata = convert_excel("./data/Miljøteknologi rådata_new2.xlsx", sheet_name="Sheet1", pri=False)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Patent applications", '{:,}'.format(len(st.session_state.rådata)).replace(',','.'))
        st.metric("Patents within Water", '{:,}'.format((st.session_state.rådata["Vand"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")

    with col2:
        st.metric("Countries included:", '{:,}'.format(len(st.session_state.rådata["person_ctry_code"].unique())).replace(',','.'), help="Specific countries has been excluded. This includes: Luxembourg, United States Virgin Islands, Monaco, Cook Islands, Liechtenstein, Cayman Islands")
        st.metric("Patents within Climate adaptation", '{:,}'.format((st.session_state.rådata["Klimatilpasning"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")
    with col3:
        st.metric("Patents applied for by Danish companies", '{:,}'.format((st.session_state.rådata["person_ctry_code"]=="Denmark").sum()).replace(',','.'))
        st.metric("Patents within Waste, Ressources and Materials", '{:,}'.format((st.session_state.rådata["Affald"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")

    with col4:
        st.metric("Number of companies", '{:,}'.format(len(st.session_state.rådata["psn_name"].unique())).replace(',','.'), help="The total number of unique companies applying for patents.")
        st.metric("Patents within Air", '{:,}'.format((st.session_state.rådata["Luft"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")

    with col5:
        st.metric("Number of Danish companies:", '{:,}'.format(len(st.session_state.rådata[st.session_state.rådata["person_ctry_code"]=="Denmark"]["psn_name"].unique())).replace(',','.'), help="The number of unique danish companies applying for patents.")
        st.metric("Patents within Nature",'{:,}'.format((st.session_state.rådata["Natur"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")

    if "number_of_instances" not in st.session_state:
        st.session_state.number_of_instances = 10
    st.markdown("""---""")

    st.sidebar.write(f'Welcome *{st.session_state["name"]}* 👋')
    st.sidebar.write("Please proceed by setting the following filters:")
    input1 = st.sidebar
    input2 = st.sidebar
    

    st.header("Country comparison")
    with input1:
        single_country = st.checkbox("Inspect a specific country", value=True, key="single_country_selectbox")
        checked = st.checkbox(label="View patents per 100.000 inhabitants", value=True, key="norm_checkbox")
        if single_country:
            with input2:
                select_country = st.selectbox(
                'Which country would you like to inspect?',
                (list(st.session_state.rådata["person_ctry_code"].unique())), index=[i for i, x in enumerate(list(st.session_state.rådata["person_ctry_code"].unique()=="Denmark")) if x][0])
        if not single_country:
            with input2:
                st.session_state.number_of_instances = st.number_input('Choose the amount of top countries you would like to view:', value = st.session_state.number_of_instances, key="number_countries_input")
    

    st.sidebar.markdown("""---""")
    st.sidebar.info('Patents are fundamental prerequisites for innovation and growth. On this page, we have curated 10 years (2011-2022) of patent application activity data into useful insights. Data is from the PATSTAT database, processed by the Danish Patent and Trademark Office. You can read more about the data and method on the methodology page.', icon="ℹ️")
    st.sidebar.markdown("""---""")
    authenticator.logout('Logout', 'sidebar')

    if checked:
        x_values = "Patents/(inhabitants/100000)"
    if not checked:
        x_values = "Patents"

    if "patents_map" not in st.session_state:
        st.session_state.patents_map = convert_excel("data/patents_all_map2.xlsx", sheet_name = "Sheet1")

    b = st.session_state.patents_map
    b = b.sort_values(by=x_values, ascending=False)
    b.reset_index(drop=True, inplace=True)
    if single_country:
        mark = b[b["country"]==select_country].index[0]+89
    if not single_country:
        mark = st.session_state.number_of_instances

    fig2 = go.Figure(data=go.Choropleth(
        locations = b[:mark]['ISO_3_alpha'],
        z = b[:mark][x_values],
        text = b[:mark]['country'],
        colorscale = 'algae',
        autocolorscale=False,
        reversescale=False,
        marker_line_color='darkgray',
        marker_line_width=0.5,
        colorbar_title = "No. of Patents",
    ))
    fig2.update_geos(scope="world", visible=False, resolution=50, showcountries=True, lataxis_showgrid=False, lonaxis_showgrid=False)
    fig2.update_layout(
        title_text='Patent applications of countries mapped',
        margin=dict(l=0, r=0, b=0, t=25),
        height=625,
        geo=dict(
            showframe=False,
            showcoastlines=True,
        ),
        geo_bgcolor="#0E1117"
    )
    st.plotly_chart(fig2, use_container_width=True, sharing="streamlit", theme="streamlit")

    st.text(" ")
    st.text(" ")

    if single_country:
        mark = b[b["country"]==select_country].index[0]+6
        b['highlight'] = b['country'].apply(lambda x: x == select_country)
    if not single_country:
        mark = st.session_state.number_of_instances
        b['highlight'] = b['country'].apply(lambda x: x == "Denmark")

    patents = alt.Chart(b[:mark]).mark_bar().encode(
        y = alt.Y("country:N",sort='-x'),
        x = alt.X(x_values+":Q"),
        color=alt.condition(
        alt.datum.highlight,
        alt.value('#367366'),
        alt.value('#85C7A6')),
        tooltip=['country', x_values+":Q"]
    ).properties(
        title="Top countries applying for environmental tachnology patents (2011-2022)"
    )

    with chart_container(data=b[:mark], export_formats = (["CSV"])):
        st.altair_chart(patents, use_container_width=True)

    st.write(" ")


    top_15_grouped_normed = convert_excel("./data/Yearly_change_plot_patents.xlsx", sheet_name="Sheet1")
    top_15_grouped_normed = top_15_grouped_normed.rename(columns={"person_ctry_code":"Country"})
    chart10 = alt.Chart(top_15_grouped_normed).mark_line().encode(
        x=alt.X('earliest_publn_year:O', axis=alt.Axis(title='Year')),
        y=alt.Y('patents_normed:Q'),
        color=alt.Color('Country:N', legend=alt.Legend(title='Country')),
        tooltip=["Country:N"]
    ).properties(
        title="Yearly development in amount of applications for a preselected set of countries"
    ).transform_calculate(tt="datum.x+' value'")

    tt = chart10.mark_line(strokeWidth=30, opacity=0.01)
    chart10 = chart10 + tt

    with chart_container(data=top_15_grouped_normed, export_formats = (["CSV"])):
        st.altair_chart(chart10, use_container_width=True)

    st.write(" ")
    st.write(" ")
    
    # Teknikområde opdeling:
    if "tech_normed" not in st.session_state:
        st.session_state.tech_normed = convert_excel("./data/teknikområde_opdelinger_normed.xlsx", sheet_name="Sheet1")
        st.session_state.tech_normed = st.session_state.tech_normed.rename(columns={"Natur": "Soil, Water & Nature", "Luft": "Air", "Vand": "Water in the technosphere", "Klimatilpasning": "Climate adaptation", "Affald": "Waste, Resources & Materials"})
        st.session_state.tech_normed.drop(st.session_state.tech_normed[st.session_state.tech_normed["country"]=="Cayman Islands"].index, axis=0, inplace=True)
        
    if "tech" not in st.session_state:
        st.session_state.tech = convert_excel("./data/teknikområde_opdelinger.xlsx", sheet_name="Sheet1")
        st.session_state.tech = st.session_state.tech.rename(columns={"Natur": "Soil, Water & Nature", "Luft": "Air", "Vand": "Water in the technosphere", "Klimatilpasning": "Climate adaptation", "Affald": "Waste, Resources & Materials"})
        st.session_state.tech.drop(st.session_state.tech[st.session_state.tech["country"]=="Cayman Islands"].index, axis=0, inplace=True)
    
    if checked:
        x = st.session_state.tech_normed
    if not checked:
        x = st.session_state.tech

    options = st.multiselect(
    'Select one or more subareas to view distribution of patents:',
    ['Water', 'Air', 'Waste', 'Climate', 'Nature'],
    ['Water'])

    if "selected_tech" not in st.session_state:
        st.session_state.selected_tech = []

    def onclick():
        x_temp = x[st.session_state.selected_tech]
        x_temp["sum"] = x_temp.sum(axis=1)
        x_temp["country"] = x["country"]
        x_temp = x_temp.sort_values(by="sum", ascending=False)
        x_temp.reset_index(drop=True, inplace=True)
        if single_country:
            mark2 = x_temp[x_temp["country"]==select_country].index[0]+6
        if not single_country:
            mark2 = st.session_state.number_of_instances
        top_k = list(x_temp["country"][:mark2])
        x_temp = x_temp.drop("sum", axis=1)
        x_temp = x_temp.melt(id_vars=['country'], var_name='tech', value_name='patents')
        x_temp = x_temp[x_temp["country"].isin(top_k)]
        x_temp["country"] = x_temp['country'].str.strip()
        x_temp['order'] = x_temp['tech'].replace({val: i for i, val in enumerate(['Soil, Water & Nature', 'Air', 'Water in the technosphere', 'Climate adaptation', "Waste, Resources & Materials"])})
        return x_temp

    altered_x = onclick()

    if options:
        if "Water in the technosphere" not in st.session_state.selected_tech and "Water" in options:
            st.session_state.selected_tech.append("Water in the technosphere")
        elif "Water in the technosphere" in st.session_state.selected_tech and "Water" not in options:
            st.session_state.selected_tech.remove("Water in the technosphere")

        if "Air" not in st.session_state.selected_tech and "Air" in options:
            st.session_state.selected_tech.append("Air")
        elif "Air" in st.session_state.selected_tech and "Air" not in options:
            st.session_state.selected_tech.remove("Air")

        if "Waste, Resources & Materials" not in st.session_state.selected_tech and "Waste" in options:
            st.session_state.selected_tech.append("Waste, Resources & Materials")
        elif "Waste, Resources & Materials" in st.session_state.selected_tech and "Waste" not in options:
            st.session_state.selected_tech.remove("Waste, Resources & Materials")

        if "Climate adaptation" not in st.session_state.selected_tech and "Climate" in options:
            st.session_state.selected_tech.append("Climate adaptation")
        elif "Climate adaptation" in st.session_state.selected_tech and "Climate" not in options:
            st.session_state.selected_tech.remove("Climate adaptation")

        if "Soil, Water & Nature" not in st.session_state.selected_tech and "Nature" in options:
            st.session_state.selected_tech.append("Soil, Water & Nature")
        elif "Soil, Water & Nature" in st.session_state.selected_tech and "Nature" not in options:
            st.session_state.selected_tech.remove("Soil, Water & Nature")
        altered_x = onclick()

    color_scale = alt.Scale(domain=['Soil, Water & Nature', 'Air', 'Water in the technosphere', 'Climate adaptation', 'Waste, Resources & Materials'],
                    range=['#FF5300', '#FCAA00', '#293972', '#5D9BA8', '#85C7A6'])

    if single_country:
        line_condition = alt.condition(
            alt.datum.country == select_country,
            alt.value(2), 
            alt.value(0)   
        )
        line = alt.Chart(altered_x.loc[altered_x['country'] == select_country]).mark_rule(color="red").encode(
        y='country:N',
        size=line_condition,
        )

    if checked:
        tech_chart = alt.Chart(altered_x).mark_bar().encode(
            x=alt.X('patents:Q', stack='zero', axis=alt.Axis(title='Patents per 100.000 inhabitants')),
            y=alt.Y('country:N', axis=alt.Axis(title='country'), sort="-x"),
            color=alt.Color('tech:N', sort=['Soil, Water & Nature', 'Air', 'Water in the technosphere', 'Climate adaptation', 'Waste, Resources & Materials'], scale=color_scale, legend=alt.Legend(title='Focus area')),
            order=alt.Order("order:N", sort="ascending"),
            tooltip=['country:N', 'tech:N', 'patents:Q']
        )

    if not checked:
        tech_chart = alt.Chart(altered_x).mark_bar().encode(
        x=alt.X('patents:Q', stack='zero', axis=alt.Axis(title='Patents')),
        y=alt.Y('country:N', axis=alt.Axis(title='country'), sort="-x"),
        color=alt.Color('tech:N', scale=color_scale, legend=alt.Legend(title='Focus area')),
        order=alt.Order("order:N", sort="ascending"),
        tooltip=['country:N', 'tech:N', 'patents:Q']
        )

    # A horizontal bar plot showcasing how the patents spread across focus areas
    st.write("**Patents applications distributed by subareas for top countries**")
    if single_country:
        st.altair_chart(tech_chart, use_container_width=True)
        altered_x = altered_x.drop(["order"], axis=1)
        if st.download_button(
            label="Download data (.xlsx)",
            data = to_excel(altered_x),
            file_name="CLEAN_Patents_FocusAreas_"+select_country+".xlsx",
            key='tech-data',
        ): st.toast('Data was sucessfully exported', icon='✅')

    if not single_country:
        st.altair_chart(tech_chart, use_container_width=True)
        altered_x = altered_x.drop(["order"], axis=1)
        st.download_button(
            label="Download data (.xlsx)",
            data = to_excel(altered_x),
            file_name="CLEAN_Patents_FocusAreas.xlsx",
            key='tech-data',
        )




    if single_country:
        st.markdown("""---""")
        st.header("The companies")
        arr1, arr2 = st.columns(2)
        with arr1:
            amount_companies = '{:,}'.format(len(st.session_state.rådata[st.session_state.rådata["person_ctry_code"] == str(select_country)]["psn_name"].unique())).replace(',','.')
            amount_patents = '{:,}'.format((st.session_state.rådata["person_ctry_code"]==str(select_country)).sum()).replace(',','.')
            
            amount_pantents_per_100000_inhabitats = st.session_state.patents_map.loc[st.session_state.patents_map['country'] == str(select_country), 'Patents/(inhabitants/100000)'].item()
            amount_pantents_per_100000_inhabitats_rounded = round(amount_pantents_per_100000_inhabitats, 2)
            
            st.write(f'The **{amount_companies}** companies of **{select_country}** has applied for a total of **{amount_patents} patents** related to environmental technology during 2011-2021.')
            st.write(f'That is **{amount_pantents_per_100000_inhabitats_rounded}** patent applications / 100.000 inhabitants.')
            st.session_state.number_of_companies = st.number_input('How many companies would you like to view?', value = 10, key="number_companies_input")
            if "companies" not in st.session_state:
                st.session_state.companies = st.session_state.rådata.groupby(["person_ctry_code", "psn_name"]).size()
            companies = st.session_state.companies.loc[select_country].sort_values(ascending=False)[0:st.session_state.number_of_companies].reset_index()
            companies = companies.rename(columns={0:"patents"})
            companies = companies.rename(columns={"psn_name":"company"})
            edited_comp = st.data_editor(companies, use_container_width=True)
            if st.download_button(
            "Download data (.xlsx)", 
            to_excel(edited_comp),
            "company_data_"+select_country+".xlsx", 
            use_container_width=True
            ): st.toast('Data was sucessfully exported', icon='✅')
        with arr2:
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")
            st.write(" ")

            st.write("- **Column sorting:** Sort columns by clicking on their headers.")
            st.write("- **Search:** Search through data by clicking a table, using hotkeys (⌘ Cmd + F or Ctrl + F) to bring up the search bar, and using the search bar to filter data.")
            st.write("- **Copy to clipboard:** Select one or multiple cells, copy them to the clipboard and paste them into your favorite spreadsheet software.")
            

    spread_df = convert_excel("./data/spread_data.xlsx", sheet_name="Sheet1")
    if single_country:
        mark3 = spread_df[spread_df["Country"]==select_country].index[0]+6
        spread_df['Highlight'] = spread_df['Country'].apply(lambda x: x == select_country)

    if not single_country:
        mark3 = st.session_state.number_of_instances
        spread_df['Highlight'] = spread_df['Country'].apply(lambda x: x == "Denmark")

    chart2 = alt.Chart(spread_df[:mark3]).mark_bar().encode(
        y = alt.Y("Country:N",sort='-x'),
        x = alt.X("Spread:Q", axis=alt.Axis(title="Spred (total no. of companies/country / total no. of patent applications)")),
        color=alt.condition(
        alt.datum.Highlight,
        alt.value('#367366'),
        alt.value('#85C7A6')),
        tooltip=["Country:N", "Spread:Q"]
    ).properties(
        title="Spread of patents across a country's companies"
    )

    st.write(" ")
    st.write(" ")

    # Display chart in Streamlit
    with chart_container(data=spread_df[:mark3], export_formats = (["CSV"])):
        st.altair_chart(chart2, use_container_width=True)

    st.markdown("""---""")

    #st.header("Yearly development in amount of applications")  