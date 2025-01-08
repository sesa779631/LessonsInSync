import yaml
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError,
                                               RegisterError, ResetError, UpdateError)

ss = st.session_state


login_tab, register_tab = st.tabs(['Login', 'Register'])

with login_tab:
    # Create a login widget
    try:
        ss.authenticator.login(sleep_time=0)
    except LoginError as e:
        st.error(e)

    if ss.authentication_status is None:
        st.warning('Please enter your username and password')
    elif ss.authentication_status is False:
        st.error('Username/password is incorrect')

    with st.expander('Forgot password?'):
        st.write('Reset password widget') # NOTE: TO BE DONE

with register_tab:
    # Create a register user widget
    try:
        email, username, name = ss.authenticator.register_user(
            domains=['se.com'],
            pre_authorization=False, 
            captcha=False, 
            clear_on_submit=True
        )
        if username:
            st.success('User registered successfully')
            ss.users.add_new_user(username, name)

            # Hash password and save to config file
            Hasher.hash_passwords(ss.config['credentials'])
            with open(ss.USERS_CREDENTIALS_PATH, 'w', encoding='utf-8') as file:
                yaml.dump(ss.config, file, default_flow_style=False)

    except RegisterError as e:
        st.error(e)