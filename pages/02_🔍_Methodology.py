import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from six import BytesIO
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu

from PIL import Image

# Sets up Favicon, webpage title and layout
favicon = Image.open(r"./assets/favicon.png")

st.set_page_config(
    page_title = "Methodology",
    page_icon = favicon,
    layout="wide"
)

# Top sidebar CLEAN logo + removal of "Made with Streamlit" & Streamlit menu + no padding top and bottom
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

def style_bullets():
    st.markdown('''
    <style>
    [data-testid="stMarkdownContainer"] ul{
        padding-left:40px;
    }
    </style>
    ''', unsafe_allow_html=True)

def convert_excel(path, sheet_name = 'Ark1'):
    df = pd.read_excel(path, sheet_name)
    return df

def to_excel(df: pd.DataFrame):
    output = BytesIO() 
    writer = pd.ExcelWriter(output, engine='xlsxwriter') 
    df.to_excel(writer, sheet_name='Sheet1') 
    writer.close() 
    processed_data = output.getvalue() 
    return processed_data

st.sidebar.info("The mapping is done by CLEAN in partnership with IRIS Group and the Danish Patent and Trademark Office. The full report will be published in June 2023.", icon="ℹ️")

st.title('Methodology')
st.subheader("Extracting data")

st.markdown("The data vizualised and shown are based on data extracts of patent applications published in the years 2011-2022 from the PATSTAT database.")
st.markdown("PATSTAT contains bibliographical data relating to more than 100 million patent documents from leading industrialised and developing countries.")
st.markdown("Data has been extracted and processed by the Danish Patent and Trademark Office.")


st.subheader("Filtering")
st.markdown("Prior to extracting the data, CLEAN and IRIS Group consulted the Danish Patent and Trademark Office in order to define the extract filters. The following was agreed upon:")
st.markdown("- Only applicants who are not also inventors and who have an address in DK, US, DE, SE, NL, FI, CH, JP, KR, IL, NO, CA or one of the 27 EU countries are included.")
st.markdown("- A defined selection of IPC/CPC classes is assigened each of CLEAN's environmental technology subareas. The extract takes a starting point in these classes.")
st.markdown("- Specifically for the subarea 'Water', a combination of IPC/CPC classes with certain keywords in the title and/or abstracts has been used.")
style_bullets()

st.subheader("IPC/CPC classes related to environmental technology", help="The CPC is a patent classification system developed by the European Patent Office (EPO) and United States Patent and Trademark Office (USPTO) that contains approximately 200,000 subgroups. The IPC is a hierarchical classification system consisting of about 70,000 subgroups.")
st.markdown("Below, you can find the exact distribution of IPC/CPC classes used:")

CPC_IPC_klasser = convert_excel("./data/CPC_IPC_klasser.xlsx", sheet_name="v2lang")

CPC_IPC_klasser = CPC_IPC_klasser.fillna('')

data_table = st.experimental_data_editor(CPC_IPC_klasser, use_container_width=True)

if st.download_button(
    "Download shown data (.xlsx)", 
    to_excel(data_table),
    "IPC_&_CPC_Classes.xlsx"
)

