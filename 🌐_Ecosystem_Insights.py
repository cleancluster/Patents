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
from six import BytesIO
from pyxlsb import open_workbook as open_xlsb
import plotly.graph_objects as go
import re
import squarify

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

## Table of contents
class Toc:

    def __init__(self):
        self._items = []
        self._placeholder = None
    
    def title(self, text):
        self._markdown(text, "h1")

    def header(self, text):
        self._markdown(text, "h2", " " * 2)

    def subheader(self, text):
        self._markdown(text, "h3", " " * 4)

    def placeholder(self, sidebar=False):
        self._placeholder = st.sidebar.empty() if sidebar else st.empty()

    def generate(self):
        if self._placeholder:
            self._placeholder.markdown("\n".join(self._items), unsafe_allow_html=True)
    
    def _markdown(self, text, level, space=""):
        #key = "".join(filter(str.isalnum, text)).lower()
        key = re.sub('[^0-9a-zA-Z]+', '-', text).lower()


        st.markdown(f"<{level} id='{key}'>{text}</{level}>", unsafe_allow_html=True)
        self._items.append(f"{space}* <a href='#{key}'>{text}</a>")

toc = Toc()

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

##### Helper functions #####
def to_excel(df: pd.DataFrame):
    output = BytesIO() 
    writer = pd.ExcelWriter(output, engine='xlsxwriter') 
    df.to_excel(writer, sheet_name='Sheet1') 
    writer.close() 
    processed_data = output.getvalue() 
    return processed_data

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
    
@st.cache_data
def convert_excel(path, sheet_name = 'Sheet1', pri = False):
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
with st.sidebar:
    st.header("Table of contents")
    toc.placeholder()
    st.markdown(" ")

toc.header("Fundamental metrics")
st.sidebar.info('Patents are fundamental prerequisites for innovation and growth. On this page, we have curated 10 years of patent application activity data into useful insights. Data is from the Danish Patent and Trademark Office. You can read more about the data and method at the end of this page', icon="ℹ️")

if "rådata" not in st.session_state:
    st.session_state.rådata = convert_excel("./Data/Miljøteknologi rådata_new2.xlsx", sheet_name="Sheet1", pri=False)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Patent applications", '{:,}'.format(len(st.session_state.rådata)).replace(',','.'))
    st.metric("Patents within water", '{:,}'.format((st.session_state.rådata["Vand"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")

with col2:
    st.metric("Countries included:", '{:,}'.format(len(st.session_state.rådata["person_ctry_code"].unique())).replace(',','.'), help="Specific countries has been excluded. This includes: Luxembourg, United States Virgin Islands, Monaco, Cook Islands, Liechtenstein, Cayman Islands")
    st.metric("Patents within  \n climate adaptation", '{:,}'.format((st.session_state.rådata["Klimatilpasning"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")
with col3:
    st.metric("Patents applied for by Danish companies", '{:,}'.format((st.session_state.rådata["person_ctry_code"]=="Denmark").sum()).replace(',','.'))
    st.metric("Patents within Waste,  \n Ressources and Materials", '{:,}'.format((st.session_state.rådata["Affald"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")

with col4:
    st.metric("Number of Danish companies:", '{:,}'.format(len(st.session_state.rådata[st.session_state.rådata["person_ctry_code"]=="Denmark"]["psn_name"].unique())).replace(',','.'), help="The number of danish companies responsible for the patent applications.")
    st.metric("Patents within Air", '{:,}'.format((st.session_state.rådata["Luft"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")

with col5:
    st.metric("TBD", "TBD")
    st.metric("Patents within Nature",'{:,}'.format((st.session_state.rådata["Natur"]).count()).replace(',','.'), help="Some patent applications are counted within multiple environmental areas")


# st.info("For the following conclusions, the number of patents per country is presented as number of patents per 100.000 inhabitants")
if "number_of_instances" not in st.session_state:
    st.session_state.number_of_instances = 10
st.markdown("""---""")

input1, input2 = st.columns(2)

toc.header("Overall patents")
with input1:
    single_country = st.checkbox("Check if you wish to inspect a specific country", value=True, key="single_country_selectbox")
    checked = st.checkbox(label="Check to set the patents as per 100.000 inhabitants", value=True, key="norm_checkbox")
    if single_country:
        with input2:
            select_country = st.selectbox(
            'Which country would you like to inspect?',
            (list(st.session_state.rådata["person_ctry_code"].unique())), index=[i for i, x in enumerate(list(st.session_state.rådata["person_ctry_code"].unique()=="Denmark")) if x][0])
    if not single_country:
        with input2:
            st.session_state.number_of_instances = st.number_input('Choose the top number of countries', value = st.session_state.number_of_instances, key="number_countries_input")
            # st.write('You have chosen to show ', st.session_state.number_of_instances,' countries')


if checked:
    x_values = "patents/(inhabitants/100000)"
    title_patents = "Plot comparing patents pr. 100.000 inhabitants for countries"
if not checked:
    x_values = "patents"
    title_patents ="Plot comparing patents for countries"

if "patents_map" not in st.session_state:

    st.session_state.patents_map = convert_excel("Data/patents_all_map2.xlsx", sheet_name = "Sheet1")

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

    colorscale = 'YlGn',

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

        #projection_type="natural earth" #'equirectangular'
    ),

    geo_bgcolor="#0E1117"
)

st.plotly_chart(fig2, use_container_width=True, sharing="streamlit", theme="streamlit")


if single_country:
    st.download_button(
        label="⬇️ Download data as .xlsx",
        # data=(b[:mark]).to_csv(index=False).encode(),
        data = to_excel(b[:mark]),
        file_name="CLEAN_Patents_"+select_country+".xlsx",
        # mime="text/csv",
        key='patents-data',
        use_container_width=True
    )
if not single_country:
    st.download_button(
        label="⬇️ Download data as .xlsx",
        # data=(b[:mark]).to_csv(index=False).encode(),
        data = to_excel(b[:mark]),
        file_name="CLEAN_Patents.xlsx",
        # mime="text/csv",
        key='patents-data',
        use_container_width=True
    )

if single_country:
    st.write("##")
    toc.header("Company information")
    arr1, arr2 = st.columns(2)
    with arr1:
        amount_companies = '{:,}'.format(len(st.session_state.rådata[st.session_state.rådata["person_ctry_code"] == str(select_country)]["psn_name"].unique())).replace(',','.')
        amount_patents = '{:,}'.format((st.session_state.rådata["person_ctry_code"]==str(select_country)).sum()).replace(',','.')
        amount_pantents_per_100000_inhabitats = st.session_state.patents_map.loc[st.session_state.patents_map['country'] == str(select_country), 'patents/(inhabitants/100000)'].item()
        amount_pantents_per_100000_inhabitats_rounded = round(amount_pantents_per_100000_inhabitats, 2)
        st.write(f'The **{amount_companies}** companies of **{select_country}** has applied for a total of **{amount_patents} patents** related to environmental technology during 2011-2021.')
        st.write(f'That is **{amount_pantents_per_100000_inhabitats_rounded}** patent applications / 100.000 inhabitants.')
        st.session_state.number_of_companies = st.number_input('How many companies would you like to view?', value = 10, key="number_companies_input")
        if "companies" not in st.session_state:
            st.session_state.companies = st.session_state.rådata.groupby(["person_ctry_code", "psn_name"]).size()
        companies = st.session_state.companies.loc[select_country].sort_values(ascending=False)[0:st.session_state.number_of_companies].reset_index()
        companies = companies.rename(columns={0:"patents"})
        companies = companies.rename(columns={"psn_name":"company"})
        edited_comp = st.experimental_data_editor(companies, use_container_width=True)
        st.download_button(
        "⬇️ Download data as .xlsx", 
        #edited_comp.to_csv(index=False).encode(),
        to_excel(edited_comp),
        "company_data_"+select_country+".xlsx", 
        use_container_width=True
        )
    with arr2:
        st.write(" ")
        st.write(" ")
        
        st.write("- Column sorting: sort columns by clicking on their headers.")
        st.write("- Column resizing: resize columns by dragging and dropping column header borders.")
        st.write("- Table resizing: resize tables by dragging and dropping the bottom right corner.")
        st.write("- Search: search through data by clicking a table, using hotkeys (⌘ Cmd + F or Ctrl + F) to bring up the search bar, and using the search bar to filter data.")
        st.write("- Copy to clipboard: select one or multiple cells, copy them to the clipboard and paste them into your favorite spreadsheet software.")
        st.write("- Click on cells to edit them.")
        st.write("- To add new rows, scroll to the bottom-most row and click on the “+” sign in any cell.")
        st.write("- To delete rows, select one or more rows and press the delete key on your keyboard.")

st.write("##")
if "tech_normed" not in st.session_state:
    st.session_state.tech_normed = convert_excel("./Data/teknikområde_opdelinger_normed.xlsx", sheet_name="Sheet1")
    st.session_state.tech_normed = st.session_state.tech_normed.rename(columns={"Natur": "Soil, Water & Nature", "Luft": "Air", "Vand": "Water in the technosphere", "Klimatilpasning": "Climate adaptation", "Affald": "Waste, Resources & Materials"})
    st.session_state.tech_normed.drop(st.session_state.tech_normed[st.session_state.tech_normed["country"]=="Cayman Islands"].index, axis=0, inplace=True)
    
if "tech" not in st.session_state:
    st.session_state.tech = convert_excel("./Data/teknikområde_opdelinger.xlsx", sheet_name="Sheet1")
    st.session_state.tech = st.session_state.tech.rename(columns={"Natur": "Soil, Water & Nature", "Luft": "Air", "Vand": "Water in the technosphere", "Klimatilpasning": "Climate adaptation", "Affald": "Waste, Resources & Materials"})
    st.session_state.tech.drop(st.session_state.tech[st.session_state.tech["country"]=="Cayman Islands"].index, axis=0, inplace=True)

toc.header("Focus area patents")
# Teknikområde opdeling:
if checked:
    x = st.session_state.tech_normed
if not checked:
    x = st.session_state.tech

st.markdown("""---""")
col_vand, col_luft, col_affald, col_klima, col_natur = st.columns(5)
water_img = Image.open('Data/fokusområde_vand_i_teknosfæren_color.png')
air_img = Image.open("Data/fokusområde_luft_color.png")
garbage_img = Image.open("Data/fokusområde_affald_ressourcer_materialer_color.png")
climate_img = Image.open("Data/fokusområde_klimatilpasning_color.png")
nature_img = Image.open("Data/fokusområde_jord_vand_natur_color.png")


w = 50
with col_vand:
    st.image(water_img, width=w)
with col_luft:
    st.image(air_img, width=w)
with col_affald:
    st.image(garbage_img, width=w)
with col_klima:
    st.image(climate_img, width=w)
with col_natur:
    st.image(nature_img, width=w)


col_vand2, col_luft2, col_affald2, col_klima2, col_natur2 = st.columns(5)
with col_vand2:
    water_button = st.button("Water", key="Water_tech")
with col_luft2:
    air_button = st.button("Air", key="Air_tech")
with col_affald2:
    garbage_button = st.button("Waste", key="Waste_tech")
with col_klima2:
    climate_button = st.button("Climate", key="Climate_tech")
with col_natur2:
    nature_button = st.button("Nature", key="Nature_tech")


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
    # highlight_category = x_temp.loc[x_temp['Country'] == "Denmark", 'Country'].iloc[0]
    # x_temp['Highlight'] = x_temp['country'].apply(lambda x: x == "Denmark")
    return x_temp

altered_x = onclick()
if water_button:
    if "Water in the technosphere" not in st.session_state.selected_tech:
        st.session_state.selected_tech.append("Water in the technosphere")
    else:
        st.session_state.selected_tech.remove("Water in the technosphere")
    altered_x = onclick()

if air_button:
    if "Air" not in st.session_state.selected_tech:
        st.session_state.selected_tech.append("Air")
    else:
        st.session_state.selected_tech.remove("Air")
    altered_x = onclick()

if garbage_button:
    if "Waste, Resources & Materials" not in st.session_state.selected_tech:
        st.session_state.selected_tech.append("Waste, Resources & Materials")
    else:
        st.session_state.selected_tech.remove("Waste, Resources & Materials")
    altered_x = onclick()

if climate_button:
    if "Climate adaptation" not in st.session_state.selected_tech:
        st.session_state.selected_tech.append("Climate adaptation")
    else:
        st.session_state.selected_tech.remove("Climate adaptation")
    altered_x = onclick()

if nature_button:
    if "Soil, Water & Nature" not in st.session_state.selected_tech:
        st.session_state.selected_tech.append("Soil, Water & Nature")
    else:
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
        x=alt.X('patents:Q', stack='zero', axis=alt.Axis(title='Patents pr. 100.00 inhabitants')),
        y=alt.Y('country:N', axis=alt.Axis(title='country'), sort="-x"),
        color=alt.Color('tech:N', sort=['Soil, Water & Nature', 'Air', 'Water in the technosphere', 'Climate adaptation', 'Waste, Resources & Materials'], scale=color_scale, legend=alt.Legend(title='Focus area')),
        order=alt.Order("order:N", sort="ascending"),
        tooltip=['country:N', 'tech:N', 'patents:Q']
    )

# labelColor=alt.condition(alt.datum.country == 'Denmark', alt.value('red'), alt.value('white'))

if not checked:
    tech_chart = alt.Chart(altered_x).mark_bar().encode(
    x=alt.X('patents:Q', stack='zero', axis=alt.Axis(title='Patents')),
    y=alt.Y('country:N', axis=alt.Axis(title='country'), sort="-x"),
    color=alt.Color('tech:N', scale=color_scale, legend=alt.Legend(title='Focus area')),
    order=alt.Order("order:N", sort="ascending"),
    tooltip=['country:N', 'tech:N', 'patents:Q']
    )


# st.write("A horizontal bar plot showcasing how the patents spread across focus areas")
if single_country:
    st.altair_chart(tech_chart, use_container_width=True) #+line
    altered_x = altered_x.drop(["order"], axis=1)
    st.download_button(
        label="⬇️ Download data as .xlsx",
        #data=altered_x.to_csv(index=False).encode(),
        data = to_excel(altered_x),
        file_name="CLEAN_Patents_FocusAreas_"+select_country+".xlsx",
        # mime="text/csv",
        key='tech-data',
        use_container_width=True
    )
if not single_country:
    st.altair_chart(tech_chart, use_container_width=True)
    altered_x = altered_x.drop(["order"], axis=1)
    st.download_button(
        label="⬇️ Download data as .xlsx",
        #data=altered_x.to_csv(index=False).encode(),
        data = to_excel(altered_x),
        file_name="CLEAN_Patents_FocusAreas.xlsx",
        # mime="text/csv",
        key='tech-data',
        use_container_width=True
    )


toc.header("Extra information")

spread_df = convert_excel("./Data/spread_data.xlsx", sheet_name="Sheet1")
if single_country:
    mark3 = spread_df[spread_df["Country"]==select_country].index[0]+6
    spread_df['Highlight'] = spread_df['Country'].apply(lambda x: x == select_country)

if not single_country:
    mark3 = st.session_state.number_of_instances
    spread_df['Highlight'] = spread_df['Country'].apply(lambda x: x == "Denmark")

chart2 = alt.Chart(spread_df[:mark3]).mark_bar().encode(
    y = alt.Y("Country:N",sort='-x'),
    x = alt.X("Spread:Q", axis=alt.Axis(title="Number of patents / number of different companies that applied for a patent")),
    color=alt.condition(
    alt.datum.Highlight,
    alt.value('#367366'),
    alt.value('#85C7A6')),
    tooltip=["Country:N", "Spread:Q"]
).properties(
    title="Plot of the spread of patents across companies"
)


# Display chart in Streamlit
st.altair_chart(chart2, use_container_width=True)

top_15_grouped_normed = convert_excel("./Data/Yearly_change_plot_patents.xlsx", sheet_name="Sheet1")
top_15_grouped_normed = top_15_grouped_normed.rename(columns={"person_ctry_code":"Country"})
chart10 = alt.Chart(top_15_grouped_normed).mark_line().encode(
    x=alt.X('earliest_publn_year:O', axis=alt.Axis(title='Year')),
    y=alt.Y('patents_normed:Q'),
    color=alt.Color('Country:N', legend=alt.Legend(title='Country')),
    tooltip=["Country:N"]
).properties(
    title="Change in patents on a yearly basis for a preselected set of countries"
).transform_calculate(tt="datum.x+' value'")

tt = chart10.mark_line(strokeWidth=30, opacity=0.01)
chart10 = chart10 + tt
st.altair_chart(chart10, use_container_width=True)

toc.header("FAQ & methodology")
st.subheader("Extracting data") 
st.markdown("The data vizualised and shown are based on data extracts of patent applications published in the years 2011-2022 from the PATSTAT database.") 
st.markdown("PATSTAT contains bibliographical data relating to more than 100 million patent documents from leading industrialised and developing countries.") 
st.markdown("Data has been extracted and processed by the Danish Patent and Trademark Office.") 

st.subheader("Filtering") 
st.markdown("Prior to extracting the data, CLEAN and IRIS Group consulted the Danish Patent and Trademark Office in order to define the extract filters. The following was agreed upon:") 
st.markdown("- Only applicants who are not also inventors and who have an address in DK, US, DE, SE, NL, FI, CH, JP, KR, IL, NO, CA or one of the 27 EU countries are included.") 
st.markdown("- A defined selection of IPC/CPC classes is assigened each of CLEAN's environmental technology subareas. The extract takes a starting point in these classes.") 
st.markdown("- Specifically for the subarea 'Water', a combination of IPC/CPC classes with certain keywords in the title and/or abstracts has been used.") 
# style_bullets() ???

st.subheader("IPC/CPC classes related to environmental technology") #help="The CPC is a patent classification system developed by the European Patent Office (EPO) and United States Patent and Trademark Office (USPTO) that contains approximately 200,000 subgroups. The IPC is a hierarchical classification system consisting of about 70,000 subgroups.") 
st.markdown("Below, you can find the exact distribution of IPC/CPC classes used:") 
CPC_IPC_klasser = convert_excel("./Data/CPC_IPC_klasser.xlsx", sheet_name="v2lang") 
CPC_IPC_klasser = CPC_IPC_klasser.fillna('') 
data_table = st.experimental_data_editor(CPC_IPC_klasser, use_container_width=True) 

st.download_button( "⬇️ Download data (.xlsx)", to_excel(data_table), "IPC_&_CPC_Classes.xlsx")

toc.generate()