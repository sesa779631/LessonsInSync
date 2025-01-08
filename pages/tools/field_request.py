import streamlit as st
from utils.functions import reset_filter_state
ss = st.session_state

ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss.authentication_status in [False, None]:
    st.rerun() # Go back to login page
reset_filter_state()

st.title('Filter Field Request')

st.info('IDEA: USERS CAN REQUEST NEW OPTIONS FOR THE DROPDOWNS. ADMINS MUST VERIFY FIRST')