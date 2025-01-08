import yaml
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError,
                                               RegisterError, ResetError, UpdateError)
from utils.functions import (
    reset_filter_state
)

ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss.authentication_status in [False, None]:
    st.rerun() # Go back to login page
reset_filter_state()


def update_password(args: dict):
    # Hash password and save to config file
    Hasher.hash_passwords(ss.config['credentials'])
    with open(ss.USERS_CREDENTIALS_PATH, 'w', encoding='utf-8') as file:
        yaml.dump(ss.config, file, default_flow_style=False)


st.title('My Account')

profile_tab, reset_password_tab = st.tabs(['Profile', 'Reset password'])

with profile_tab:
    # WIP
    st.write(f'User: {ss.users.get_user_field(ss.username, 'User_ID')}')
    st.write(f'Name: {ss.users.get_user_field(ss.username, 'Name')}')
    st.write(f'Role: {ss.users.get_user_field(ss.username, 'Role')}')

with reset_password_tab:
    if st.session_state.authentication_status:
        try:
            if ss.authenticator.reset_password(
                    username=ss.username,
                    clear_on_submit=True,
                    callback=update_password,
                ):
                st.success('Password modified successfully')
        except ResetError as e:
            st.error(e)