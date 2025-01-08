import streamlit as st
from utils.functions import reset_filter_state

ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss['authentication_status'] in [False, None]:
    st.rerun() # Go back to login page
reset_filter_state()


def grant_admin():
    if not ss.users.exists_username(ss.grant_admin_username):
        st.toast('User does not exists', icon='⚠️')
    else:
        ss.users.grant_admin(ss.grant_admin_username)
        st.toast('Admin granted successfully')

def revoke_admin():
    if not ss.users.exists_username(ss.revoke_admin_username):
        st.toast('User does not exists', icon='⚠️')
    elif ss.username == ss.revoke_admin_username:
        st.toast('You cannot revoke your own admin status', icon='🤪')
    else:
        ss.users.revoke_admin(ss.revoke_admin_username)
        st.toast('Admin revoked successfully')


st.title('Manage admins')

with st.form(key='grant_admin_form', clear_on_submit=True, border=False):
    col1, col2 = st.columns([2, 1])
    col1.text_input(label='-', key='grant_admin_username', label_visibility='collapsed', placeholder='username')
    col2.form_submit_button('Grant admin', type='primary', use_container_width=True, on_click=grant_admin)


with st.form(key='revoke_admin_form', clear_on_submit=True, border=False):
    col1, col2 = st.columns([2, 1])
    col1.text_input(label='-', key='revoke_admin_username', label_visibility='collapsed', placeholder='username')
    col2.form_submit_button('Revoke admin', type='primary', use_container_width=True, on_click=revoke_admin)


st.subheader('All users', divider='red')
users = ss.users.get_users()
st.dataframe(users, use_container_width=True)