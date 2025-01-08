import pyodbc
import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth

from utils.classes import Lessons, Users


ss = st.session_state # Shorter


########## SETUP ###############################################################


if not 'setup' in ss: # Only run once

    # Table names
    LESSONS_TABLE_NAME = 'LessonsInSync_Lessons'
    USERS_TABLE_NAME = 'LessonsInSync_Users'

    # Obtained from azure database -> connection strings section
    CONNECTION_STRING = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:iberiadata.database.windows.net,1433;\
        Database=iberia_database;Uid=data_team_admin;Pwd={9G#2$mM`9d.cQO%};Encrypt=yes;TrustServerCertificate=no;\
        Connection Timeout=30;'

    # Create connection and cursor
    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    # Create Lessons and Users instance and save in state
    ss.lessons = Lessons(cursor=cursor, table_name=LESSONS_TABLE_NAME)
    ss.users = Users(cursor=cursor, table_name=USERS_TABLE_NAME, lessons=ss.lessons)

    # Credentials path on session_state since needed in other places
    ss.USERS_CREDENTIALS_PATH = 'utils/credentials/config.yaml' 

    ss.setup = True # Add to state to avoid executing this again


if not 'authenticator' in ss: # Only run once(?)

    # Load config file that contains the credentials
    with open(ss.USERS_CREDENTIALS_PATH, 'r', encoding='utf-8') as file:
        ss.config = yaml.load(file, Loader=SafeLoader)

    # Creating the authenticator object
    ss.authenticator = stauth.Authenticate(
        credentials=ss.config['credentials'],
        # I don't know what a cookie is or how it doesn't work without it
        cookie_name=ss.config['cookie']['name'],
        cookie_key=ss.config['cookie']['key'],
        cookie_expiry_days=ss.config['cookie']['expiry_days']
        # NOTE: Can provide a validator object
    )


########## NAVIGATION ##########################################################


# Pages

login_page = st.Page('pages/session/login.py', title='Log in')
logout_page = st.Page('pages/session/logout.py', title='Log out', icon='⬅️')

dashboard = st.Page('pages/account/dashboard.py', title='Dashboard', icon='🏠')
my_account = st.Page('pages/account/my_account.py', title='My Account', icon='👤')
my_lessons = st.Page('pages/account/my_lessons.py', title='My Lessons', icon='📒')
likes = st.Page('pages/account/likes.py', title='Likes', icon='❤️')

submit = st.Page('pages/tools/submit.py', title='Submit', icon='📝')
filter_search = st.Page('pages/tools/filter_search.py', title='Filter Search', icon='🔍')
intelligent_search = st.Page('pages/tools/intelligent_search.py', title='Intelligent Search', icon='🪄')
field_request = st.Page('pages/tools/field_request.py', title='Field Request', icon='🙏')

manage_lessons = st.Page('pages/admin/manage_lessons.py', title='Manage Lessons', icon='🛠️')
manage_admins = st.Page('pages/admin/manage_admins.py', title='Manage Admins', icon='🕶️')


if 'authentication_status' in ss and ss.authentication_status == True:
    # If authenticated, enter app, show menu

    # Change sidebar menu in function of user role
    user_role = ss.users.get_user_field(ss.username, 'Role')
    match user_role:
        case 'User':
            pg = st.navigation({
                'Account': [dashboard, my_account, my_lessons, likes, logout_page],
                'Tools': [submit, filter_search, intelligent_search, field_request]
            })
        case 'Admin':
            pg = st.navigation({
                'Account': [dashboard, my_account, my_lessons, likes, logout_page],
                'Tools': [submit, filter_search, intelligent_search, field_request],
                'Admin': [manage_lessons, manage_admins]
            })

else: 
    # If not authenticated, show only login page
    pg = st.navigation([login_page])


pg.run() # Start app