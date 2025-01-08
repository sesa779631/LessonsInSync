import streamlit as st

from utils.functions import (
    display_lesson_details,
    display_lesson_collapsed,
    display_lesson_overview,
    reset_filter_state
)

ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss['authentication_status'] in [False, None]:
    st.rerun() # Go back to login page
reset_filter_state()


if 'mylikes_lesson_selected' in ss:
    id = ss.mylikes_lesson_selected
    
    st.button('⮜ Go back', key='mylikes_goback')
    if ss.mylikes_goback:
        del ss.mylikes_lesson_selected
        st.rerun()

    st.title(ss.lessons.get_lesson_field(id, 'Title'))
    st.subheader('Details', divider='red')
    display_lesson_details(id)
    st.subheader('Description', divider='red')
    st.write(ss.lessons.get_lesson_field(id, 'Description'))

else:
    st.title('Your likes')
    st.info('MOLT MOOOOLT MILLORABLE')

    liked_lessons = ss.users.get_user_field(ss.username, 'Liked_Lessons')

    for id in liked_lessons:
        display_lesson_collapsed(lesson_id=id, page_key='mylikes')
