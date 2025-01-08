import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (CredentialsError, ForgotError, Hasher, LoginError,
                                               RegisterError, ResetError, UpdateError)

ss = st.session_state


# Create a logout widget
st.warning('Are you sure you want to log out?')
ss.authenticator.logout()