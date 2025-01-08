import streamlit as st
import datetime as dt
from streamlit_extras.stylable_container import stylable_container

from utils.globals import (
    STATUS_ICON,
    STATUS_OPTIONS
)

from utils.functions import (
    reset_filter_state,
    display_lesson_details,
    display_lesson_collapsed,
    display_lesson_overview,
    display_edit_lesson
)

ss = st.session_state
ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss['authentication_status'] in [False, None]:
    st.rerun()  # Go back to login page

########## REMEMBER FILTER STATE ###############################################


def update_filter_state(initialize: bool=False):
    ''' Function to remember filter state, called everytime a lesson is selected.
        If initialize is True, it creates a dictionary in session state to store filter data '''
    if initialize:
        ss.mylessons_filter_state = {
            'title': '',
            'status': None,
            'collapse': False
        }
    else:
        if 'mylessons_title' in ss: ss.mylessons_filter_state['title'] = ss.mylessons_title
        if 'mylessons_status' in ss: ss.mylessons_filter_state['status'] = ss.mylessons_status
        if 'mylessons_collapse' in ss: ss.mylessons_filter_state['collapse'] = ss.mylessons_collapse

# Delete all other pages remember filters except this one
reset_filter_state(except_page_key='mylessons')

# Initialize remember filters if not in state
if not 'mylessons_filter_state' in ss:
    update_filter_state(initialize=True)



########## DISPLAY LESSON ######################################################


if 'mylessons_lesson_selected' in ss:
    id = ss.mylessons_lesson_selected

    goback_col, status_col = st.columns([3, 1])

    with goback_col:
        st.button('⮜ Go back', key='mylessons_goback')
        if ss.mylessons_goback:
            # If go back button clicked, delete ID from state to NOT display it in next rerun
            del ss.mylessons_lesson_selected
            st.rerun()

    with status_col:
        status = ss.lessons.get_lesson_field(id, 'Status')
        with stylable_container(key='right_alignment', css_styles='{text-align:right}'):
            st.button(f'Status: {STATUS_ICON[status]} **{status}**', use_container_width=True)

    st.title(ss.lessons.get_lesson_field(id, 'Title'))

    st.subheader('Details', divider='red')
    display_lesson_details(id)

    st.subheader('Description', divider='red')
    st.write(ss.lessons.get_lesson_field(id, 'Description'))


########## DISPLAY DRAFT #######################################################


elif 'mylessons_draft_selected' in ss:
    id = ss.mylessons_draft_selected

    if ss.lessons.get_lesson_field(id, 'Status') in ['Pending', 'Accepted']:
        # Change to a non-editable visualization
        ss.mylessons_lesson_selected = ss.mylessons_draft_selected
        del ss.mylessons_draft_selected
        st.rerun()

    goback_col, warning_col = st.columns(2)

    with goback_col:
        # Go back to My Lessons page by deleting draft_selected from session_state
        st.button("⮜ Go back", key='mylessons_goback')
        if ss.mylessons_goback or ss.lessons.get_lesson_field(id, 'Status') != 'Draft':
            del ss.mylessons_draft_selected
            st.rerun()

    with warning_col:
        with stylable_container(key='right_alignment', css_styles='{text-align:right}'):
            st.write(":red[Changes aren't saved automatically]")

    display_edit_lesson(lesson_id=id, form_type='draft', border=False)


########## DISPLAY REJECTED ####################################################


elif 'mylessons_rejected_selected' in ss:

    id = ss.mylessons_rejected_selected

    if ss.lessons.get_lesson_field(id, 'Status') in ['Pending', 'Accepted']:
        # Change to a non-editable visualization
        ss.mylessons_lesson_selected = ss.mylessons_rejected_selected
        del ss.mylessons_rejected_selected
        st.rerun()

    goback_col, warning_col = st.columns(2)

    with goback_col:
        # Go back to My Lessons page by deleting draft_selected from session_state
        st.button("⮜ Go back", key='mylessons_goback')
        if ss.mylessons_goback:
            del ss.mylessons_rejected_selected
            st.rerun()

    with warning_col:
        with stylable_container(key='right_alignment', css_styles='{text-align:right}'):
            st.write(":red[Changes aren't saved automatically]")

    display_edit_lesson(lesson_id=id, form_type='rejected', border=False)
    st.error(f'**Administrator comments:** {ss.lessons.get_lesson_field(id, 'Status_Comments')}')



########## MY LESSONS ##########################################################


else:
    st.title('My Lessons')

    ### FILTERS

    # Show filers in cols
    col1, col2 = st.columns([2, 1])
    col1.text_input(label='Title contains', placeholder='Introduce keywords',
                    value=ss.mylessons_filter_state['title'], key='mylessons_title')
    col2.multiselect(label='Status', options=STATUS_OPTIONS, 
                    default=ss.mylessons_filter_state['status'], key='mylessons_status')
    st.toggle(label='Collapse results',  value=ss.mylessons_filter_state['collapse'], 
            key='mylessons_collapse')

    # Call filter method
    filtered_lessons, active_tags = ss.lessons.filter_by(
        filters={},
        user_id=ss.username,
        keywords=ss.mylessons_title.split(' '), 
        status=ss.mylessons_status,
        mode='AND'
    )


    ### DISPLAY LESSONS/DRAFTS RESULTS

    for id, tags in zip(filtered_lessons, active_tags):
        if ss.mylessons_collapse:
            display_lesson_collapsed(lesson_id=id, page_key='mylessons', show_status=True,
                                    update_filter_state=update_filter_state)
        else:
            display_lesson_overview(lesson_id=id, page_key='mylessons', show_status=True, 
                                    active_tags=tags, update_filter_state=update_filter_state)
