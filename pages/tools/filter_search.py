import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from utils.globals import (
    OPTIONS_ADC,
    OPTIONS_SCOPE,
    OPTIONS_COUNTRY,
    OPTIONS_SEGMENT,
    OPTIONS_TECH
)

from utils.functions import (
    reset_filter_state,
    display_lesson_details,
    display_lesson_collapsed,
    display_lesson_overview
)


ss = st.session_state

ss.authenticator.login(location='unrendered')
if not 'authentication_status' in ss or ss.authentication_status in [False, None]:
    st.rerun() # Go back to login page


########## REMEMBER FILTERS ####################################################


def update_filter_state(initialize: bool=False):
    ''' Function to remember filter state, called everytime a lesson is selected.
        If initialize is True, it creates a dictionary in session state to store filter data '''
    if initialize:
        ss.filtersearch_filter_state = {
            'Title': '',
            'adc': None,
            'start_date': None,
            'end_date': None,
            'tech': None,
            'scope': None,
            'dest_country': None,
            'segment': None,
            'max_results': 25,
            'mode': 0,
            'collapse': False,
        }
    else:
        if 'filter_title' in ss: ss.filtersearch_filter_state['title'] = ss.filter_title
        if 'filter_adc' in ss: ss.filtersearch_filter_state['adc'] = ss.filter_adc
        if 'filter_start_date' in ss: ss.filtersearch_filter_state['start_date'] = ss.filter_start_date
        if 'filter_end_date' in ss: ss.filtersearch_filter_state['end_date'] = ss.filter_end_date
        if 'filter_tech' in ss: ss.filtersearch_filter_state['tech'] = ss.filter_tech
        if 'filter_scope' in ss: ss.filtersearch_filter_state['scope'] = ss.filter_scope
        if 'filter_dest_country' in ss: ss.filtersearch_filter_state['dest_country'] = ss.filter_dest_country
        if 'filter_segment' in ss: ss.filtersearch_filter_state['segment'] = ss.filter_segment
        if 'max_results' in ss: ss.filtersearch_filter_state['max_results'] = ss.max_results
        if 'filter_mode' in ss: ss.filtersearch_filter_state['mode'] = 0 if ss.filter_mode == 'AND' else 1
        if 'filter_collapse' in ss: ss.filtersearch_filter_state['collapse'] = ss.filter_collapse

# Delete all other pages remember filters except this one
reset_filter_state(except_page_key='filtersearch') 

# Initialize remember filters if not in state
if not 'filtersearch_filter_state' in ss:
    update_filter_state(initialize=True)


########## LESSON SELECTED #####################################################


### LIKE BUTTON ###

def like_button_clicked():
    ''' Called when the like button is clicked to add/remove like '''
    if ss.users.is_liked(ss.username, ss.filtersearch_lesson_selected):
        ss.users.remove_liked_lesson(ss.username, ss.filtersearch_lesson_selected)
    else:
        ss.users.add_liked_lesson(ss.username, ss.filtersearch_lesson_selected)


### DISPLAY LESSON ###

if 'filtersearch_lesson_selected' in ss:
    
    lesson_id = ss.filtersearch_lesson_selected
    user_id = ss.lessons.get_lesson_field(lesson_id, 'User_ID')

    # HEADER
    gobak_col, like_col = st.columns([5, 1])

    with gobak_col:
        st.button('⮜ Go back', key='search_goback')
        if ss.search_goback:
            # If go back button clicked, delete lesson ID from state to NOT display it in next rerun
            del ss.filtersearch_lesson_selected
            st.rerun()

    with like_col:
        with stylable_container(key='right_alignment', css_styles='{text-align:right}'):
            # Button type depends on whether the lesson is liked or not
            if ss.users.is_liked(ss.username, lesson_id): button_type = 'primary'
            else: button_type = 'secondary'
            st.button(label=f'❤ {int(ss.lessons.get_lesson_field(lesson_id, 'Likes'))}', key='like_button', 
                    type=button_type, on_click=like_button_clicked)
    
    # BODY
    st.title(ss.lessons.get_lesson_field(lesson_id, 'Title'))

    st.subheader('Details', divider='red')
    display_lesson_details(lesson_id)

    st.subheader('Description', divider='red')
    st.write(ss.lessons.get_lesson_field(lesson_id, 'description'))

    # AUTHOR (WIP)
    with st.expander('About the author :red[[UNDER CONSTRUCTION]]'):
        pic_col, text_col = st.columns([1, 3])
        pic_col.image('images/user.png')
        text_col.subheader(ss.users.get_user_field(user_id, 'Name'))
        text_col.write(f'Username: `{user_id}`')


########## DISPLAY FILTERS #####################################################


else:

    st.title('Filter Search')

    # Display filters
    with st.container(border=False):
        st.header('Filters')
    
        row1_col1, row1_col2 = st.columns([2, 1])
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row3_col1, row3_col2, row3_col3 = st.columns(3)
        row4_col1, row4_col2, row4_col3 = st.columns([1, 2, 1])
        row1_col1.text_input(label='Title contains', value=ss.filtersearch_filter_state['Title'],
                             placeholder='Introduce keywords', key='filter_title')
        row1_col2.multiselect(label='AdC', options=OPTIONS_ADC, 
                              default=ss.filtersearch_filter_state['adc'], key='filter_adc')
        
        row2_col1.date_input(label='Start date', value=ss.filtersearch_filter_state['start_date'], 
                             format='DD/MM/YYYY', key='filter_start_date')
        row2_col2.date_input(label='End Date', value=ss.filtersearch_filter_state['end_date'], 
                             format='DD/MM/YYYY', key='filter_end_date')
        row2_col3.multiselect(label='Technology', options=OPTIONS_TECH, 
                              default=ss.filtersearch_filter_state['tech'], key='filter_tech')
        
        row3_col1.multiselect(label='Scope', options=OPTIONS_SCOPE, 
                              default=ss.filtersearch_filter_state['scope'], key='filter_scope')
        row3_col2.multiselect(label='Destination Country', options=OPTIONS_COUNTRY, 
                              default=ss.filtersearch_filter_state['dest_country'], key='filter_dest_country')
        row3_col3.multiselect(label='Segment', options=OPTIONS_SEGMENT, 
                              default=ss.filtersearch_filter_state['segment'], key='filter_segment')
        
        row4_col1.radio(label='Filter mode', options=['AND', 'OR'],
                        index=ss.filtersearch_filter_state['mode'], key='filter_mode')
        row4_col2.slider(label='Results shown', min_value=5, max_value=50, 
                         value=ss.filtersearch_filter_state['max_results'], key='max_results')
        row4_col3.markdown('<small>Visualization</small>', unsafe_allow_html=True)
        row4_col3.toggle(label='Collapse results', value=ss.filtersearch_filter_state['collapse'], key='filter_collapse')

    # Call the macro filtering method
    filtered_lessons, active_tags = ss.lessons.filter_by(
        filters={
            'Scope': ss.filter_scope,
            'Segment': ss.filter_segment,
            'Destination_Country': ss.filter_dest_country,
            'AdC': ss.filter_adc,
            'Technology': ss.filter_tech
        },
        start_date=ss.filter_start_date,
        end_date=ss.filter_end_date,
        keywords=ss.filter_title.split(' '),
        mode=ss.filter_mode,
        max_results=ss.max_results,
        status=['Approved'] # Only approved in filter search
    ) 

    # Display results
    st.header('Results')
    for lesson_id, act_tags in zip(filtered_lessons, active_tags):
        if ss.filter_collapse:
            display_lesson_collapsed(lesson_id=lesson_id, page_key='filtersearch', 
                                     update_filter_state=update_filter_state)
        else:
            display_lesson_overview(lesson_id=lesson_id, page_key='filtersearch', active_tags=act_tags,
                                    update_filter_state=update_filter_state)