import streamlit as st
import streamlit.components.v1 as components
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu

#For login part (necsesary for streamlit_authenticator)
import yaml
from yaml import load, dump
from yaml.loader import SafeLoader

from PIL import Image

# To send user detail to newly registered user
import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


###################################

#IMPORTANT This page is only visible if logged in user has name "Emil Hansen"

###################################


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

with open('./assets/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

#Register a new user
try:
    if authenticator.register_user('Register user', preauthorization=False):
        st.success('User registered successfully ✅')

        #Syncs new user information to config.yaml file
        with open('./assets/config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

        # Sends e-mail to newly registered user
        lastUsername = list(config['credentials'].get('usernames'))[-1]
        newUserEmail = config['credentials'].get('usernames').get(lastUsername).get("email")
        newUserName = config['credentials'].get('usernames').get(lastUsername).get("name")

        try:
            subject = "Your new user on CLEAN Insights"
            sender_email = "noreply@cleancluster.dk"
            receiver_email = newUserEmail
            password = st.secrets["server_password"]
            port = 587
            smtp_server = "smtp.office365.com"

            # Create a multipart message and set headers
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject

            # Add body to email
            html = """\
            <html>
            <body>
                <span>Hi $(Name)!</span><br><br>
                <span>A new personal user for https://clean-insights.streamlit.app/ has been created for you. Here's your username.</span><br>
                <span><b>Username:</b> $(username)</span><br><br>
                <span>Please reset your password the first time you try to log in. This is done by entering your username and pressing the Login button</span><br><br>
                <span>Best regards</span><br>
                <span>CLEAN</span>
                </p>
            </body>
            </html>
            """
            html = html.replace("$(Name)", newUserName)
            html = html.replace("$(username)", lastUsername)

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

        #Catch email sending error
        except Exception as e:
            st.write(e)
            st.sidebar.warning(e)

except Exception as e:
    st.error(e)
