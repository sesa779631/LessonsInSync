import yaml
import streamlit as st
from utils.functions import (
    reset_filter_state
)

ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss['authentication_status'] in [False, None]:
    st.rerun() # Go back to login page
reset_filter_state()



st.title(f'Welcome, {ss.name}')
st.write(f'Your role: **{ss.users.get_user_field(ss.username, 'Role')}**')


col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.metric(label='Total Lessons:', value=ss.lessons.get_lesson_count(ss.username),
                  delta='3 (this statistic is fake)')
