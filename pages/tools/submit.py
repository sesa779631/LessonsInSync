import streamlit as st

from utils.functions import (
    display_edit_lesson,
    reset_filter_state
)


ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss.authentication_status in [False, None]:
    st.rerun() # Go back to login page
reset_filter_state()


# FIND A WAY TO SUPRESS DUPLICATE WIDGET WARNING
st.error('TOML workaround for duplicate widget warning not working. Review.')


# Display new lesson form
display_edit_lesson(form_type='new', border=True)