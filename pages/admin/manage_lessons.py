import streamlit as st
import pandas as pd
from streamlit_extras.stylable_container import stylable_container

from utils.globals import (
    STATUS_OPTIONS,
    STATUS_ICON
)

from utils.functions import (
    reset_filter_state,
    display_lesson_details,
    display_lesson_collapsed,
    display_lesson_overview
)

ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss['authentication_status'] in [False, None]:
    st.rerun() # Go back to login page


def update_filter_state(initialize: bool=False):
    if initialize:
        ss.admin_filter_state = {
            'description':'',
            'lesson_id': None,
            'status': ['Pending'], # Because main purpose is to manage pending
            'max_results': 25,
            'collapse': False
        }
    else:
        if 'admin_description' in ss: ss.admin_filter_state['description'] = ss.admin_description
        if 'admin_lesson_id' in ss: ss.admin_filter_state['lesson_id'] = ss.admin_lesson_id
        if 'admin_status' in ss: ss.admin_filter_state['status'] = ss.admin_status
        if 'admin_max_results' in ss: ss.admin_filter_state['max_results'] = ss.admin_max_results
        if 'admin_collapse' in ss: ss.admin_filter_state['collapse'] = ss.admin_collapse

reset_filter_state(except_page_key='admin')
if not 'admin_filter_state' in ss:
    update_filter_state(initialize=True)


def update_status():
    lesson_id = ss.admin_lesson_selected
    status = ss.status_selectbox
    comments = ss.status_comments

    if status == 'Rejected' and comments == '':
        st.toast(body='Comments are mandatory for rejected lessons', icon='⚠️')
    else:
        ss.lessons.set_lesson_status(lesson_id=lesson_id, status=status, comments=comments)
        ss.status_comments = ''
        st.toast('Status changed successfully')
        del ss.admin_lesson_selected


if 'admin_lesson_selected' in ss:

    id = ss.admin_lesson_selected
    status = ss.lessons.get_lesson_field(id, 'Status')
    goback_col, status_col = st.columns([3, 1])

    with goback_col:
        st.button('⮜ Go back', key='admin_goback')
        if ss.admin_goback:
            del ss.admin_lesson_selected
            st.rerun()

    with status_col:
        with stylable_container(key='right_alignment', css_styles='{text-align:right}'):
            st.button(f'Status: {STATUS_ICON[status]} **{status}**', use_container_width=True)

    st.title(ss.lessons.get_lesson_field(id, 'Title'))

    st.subheader('Details', divider='red')

    display_lesson_details(id)

    st.subheader('Description', divider='red')

    st.write(ss.lessons.get_lesson_field(id, 'Description'))


    with stylable_container(key='color_background', css_styles='{background: #dedede; border-radius: 0.5rem;}'):
        with st.form(border=True, key='change_status', clear_on_submit=False):
            st.markdown('#### Change status')

            col1, col2 = st.columns([2, 1])
            # NOTE format selectbox
            col1.selectbox('Status', options=['Approved', 'Rejected'], label_visibility='collapsed', 
                           index=None, key='status_selectbox')
            col2.form_submit_button('Submit', type='primary', use_container_width=True, on_click=update_status)
            
            st.text_area(label='Comments', key='status_comments', label_visibility='collapsed', 
                         placeholder='Comments (mandatory if lesson rejected)')


else:
    st.title('Manage Lessons')

    row1_col1, row1_col3 = st.columns([2, 1])
    row2_col1, row2_col2, row2_col3 = st.columns([1, 2, 1])

    row1_col1.text_input(label='Title contains', placeholder='Introduce keywords',
                         value=ss.admin_filter_state['description'], key='admin_title')

    row2_col1.number_input(label='Lesson ID', placeholder='Ex: 42',
                           value=None, step=1, key='admin_lesson_id') # Works funny with defaults

    row1_col3.multiselect(label='Status', options=STATUS_OPTIONS[:3],
                   default=ss.admin_filter_state['status'], key='admin_status', disabled=False)
    
    row2_col2.slider(label='Results shown', min_value=5, max_value=50, 
              value=ss.admin_filter_state['max_results'], key='admin_max_results')
    
    row2_col3.markdown('<small>Visualization</small>', unsafe_allow_html=True)
    row2_col3.toggle(label='Collapse results', value=ss.admin_filter_state['collapse'], key='admin_collapse')

    st.info('Lessons are sorted so that older lessons are shown first.')

    if ss.admin_lesson_id != None:
        filtered_lessons, tags = [ss.admin_lesson_id], [[]]

    else:
        filtered_lessons, tags = ss.lessons.filter_by(
            filters={},
            keywords=ss.admin_title.split(' '),
            status=ss.admin_status if len(ss.admin_status) > 0 else STATUS_OPTIONS[:3],
            sort_by='Date',
            mode='AND'
        )

    for id, tags in zip(filtered_lessons, tags):
        if ss.admin_collapse:
            display_lesson_collapsed(lesson_id=id, page_key='admin', show_status=True,
                                     update_filter_state=update_filter_state)
        else:
            display_lesson_overview(lesson_id=id, page_key='admin', 
                                    show_status=True, active_tags=tags,
                                    update_filter_state=update_filter_state)