from typing import Callable
import streamlit as st
import datetime as dt

from streamlit_extras.tags import tagger_component
from streamlit_extras.stylable_container import stylable_container
from azure.storage.blob import BlobServiceClient

from .globals import (
    PAGE_KEYS,
    STATUS_ICON,
    STATUS_COLOR,
    TAG_FIELDS,
    MAX_DESC_LEN,
    OPTIONS_ADC,
    OPTIONS_COUNTRY,
    OPTIONS_SCOPE,
    OPTIONS_SEGMENT,
    OPTIONS_TECH,
)

ss = st.session_state

def reset_filter_state(except_page_key: str='') -> None:
    ''' Function to reset remember filters state.
        > Streamlit does not natively support to remember the state of the filters.
        That is, if you set some filters and then check a lesson and you go back
        THE FILTERS THAT YOU SELECTED WON'T BE REMEMBERED
        > We need to manually remember the filters. Solutions: each time a lesson is
        selected we remember the filters (save their values) before displaying the lesson
        > BUT!! If we navigate to another page we don't want to remember the filters then
        > SOLUTION: This function.
            > It erases the defaults from the session state: filters and selected lessons/drafts
            > EXCEPT one filter state (the current page filter state)'''

    for page_key in PAGE_KEYS:
        if page_key == except_page_key:
            continue

        # Delete filter state
        if f'{page_key}_filter_state' in ss:
            del ss[f'{page_key}_filter_state']

        # Delete lesson selected (note that not all pages have them all)
        if f'{page_key}_lesson_selected' in ss:
            del ss[f'{page_key}_lesson_selected']
        if f'{page_key}_draft_selected' in ss:
            del ss[f'{page_key}_draft_selected']
        if f'{page_key}_rejected_selected' in ss:
            del ss[f'{page_key}_rejected_selected']


def display_lesson_details(lesson_id: int) -> None:
    ''' Function that displays the lesson details (i.e. the value of each field)
        in a column fashion inside a container '''
    
    with st.container(border=True):
        # I declare new columns for each row to avoid mismatched lengths if a field is too long
        # Date and Scope fields need to be formatted 
        
        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns([2, 3, 2, 3])
        row2_col1, row2_col2, row2_col3, row2_col4 = st.columns([2, 3, 2, 3])
        row3_col1, row3_col2, row3_col3, row3_col4 = st.columns([2, 3, 2, 3])
        row4_col1, row4_col2, row4_col3, row4_col4 = st.columns([2, 3, 2, 3])
        row5_col1, row5_col2, row5_col3, row5_col4 = st.columns([2, 3, 2, 3])
        row6_col1, row6_col2, row6_col3, row6_col4 = st.columns([2, 3, 2, 3])

        row1_col1.write(f'**:grey-background[AdC:]**')
        row1_col2.write(ss.lessons.get_lesson_field(lesson_id, 'AdC'))
        row1_col3.write(f'**:grey-background[Scope:]**')
        scope_list = ss.lessons.get_lesson_field(lesson_id, 'Scope') # Returns a list
        row1_col4.write(', '.join(scope_list))

        row2_col1.write(f'**:grey-background[Technology:]**')
        tech_list = ss.lessons.get_lesson_field(lesson_id,'Technology')
        row2_col2.write(', '.join(tech_list))
        row2_col3.write(f'**:grey-background[Segment:]**')
        row2_col4.write(ss.lessons.get_lesson_field(lesson_id, 'Segment'))

        row3_col1.write(f'**:grey-background[Destination Country:]**')
        row3_col2.write(ss.lessons.get_lesson_field(lesson_id, 'Destination_Country'))
        row3_col3.write(f'**:grey-background[Date:]**')
        date = ss.lessons.get_lesson_field(lesson_id, 'Date') # Returns a datetime
        row3_col4.write(date.strftime('%d/%m/%Y'))

        row4_col1.write(f'**:grey-background[Client:]**')
        row4_col2.write(ss.lessons.get_lesson_field(lesson_id, 'Client'))
        row4_col3.write(f'**:grey-background[End User:]**')
        row4_col4.write(ss.lessons.get_lesson_field(lesson_id, 'End_User'))

        row5_col1.write(f'**:grey-background[IG Stakeholder:]**')
        row5_col2.write(ss.lessons.get_lesson_field(lesson_id, 'IG_Stakeholder'))
        row5_col3.write(f'**:grey-background[OG Stakeholder:]**')
        row5_col4.write(ss.lessons.get_lesson_field(lesson_id, 'OG_Stakeholder'))

        row6_col1.write(f'**:grey-background[User ID:]**')
        row6_col2.write(f'`{ss.lessons.get_lesson_field(lesson_id, 'User_ID')}`')
        row6_col3.write(f'**:grey-background[Lesson ID:]**')
        row6_col4.write(ss.lessons.get_lesson_field(lesson_id, 'Lesson_ID'))


def display_lesson_collapsed(lesson_id: int, page_key: str, 
    update_filter_state: Callable=None, show_status: bool=False) -> None:
    ''' 
    Displays the given lesson collapsed
    PARAMETERS:
        > lesson_id: ID of the lesson to display
        > page_key: key of the page from which the function is called from. It's important
            since the names of the variables stored in session state depend on the page_key
        > update_filter_state: a function that updates the filter state before changing
            the display to show a lesson/draft. The function is defined in the page where
            display_lesson_collapsed so the function is different depending on the page is called from
        > show_status: whether to show the status of the lesson (e.g. filtersearch has no interest in status)
    '''
    
    ### DISPLAY

    status = ss.lessons.get_lesson_field(lesson_id, 'Status')

    with st.container(border=True):
        title_col, readmore_col = st.columns([6, 1])

        with title_col:
            if show_status: icon = f'{STATUS_ICON[status]} ' # The space after is important!!
            else: icon = '' # No icon
            st.markdown(f'#### {icon}{ss.lessons.get_lesson_field(lesson_id, 'Title')}')
            
        with readmore_col:
            if status in ['Rejected', 'Draft']: 
                # If draft/rejected the arrow changes to a pen, and the button key has different name
                label = '✎'
                button_key = f'{page_key}_edit_{lesson_id}'
            else: 
                label = '⮞' 
                button_key = f'{page_key}_readmore_{lesson_id}'

            # Inside stylable container allows for right alignment
            with stylable_container(key='right_alignment', css_styles='{text-align:right}'):
                # Readmore/edit button
                st.button(label=label, key=button_key)

    ### SELECTED LESSON/DRAFT EVENT

    if ss[button_key]:
        # If button is clicked, we need to add a new selected variable to session_state
        # This selected variable will be catched in the next rerun and the lesson/draft will be displayed
        if status == 'Draft': selected_key = f'{page_key}_draft_selected'
        elif status == 'Rejected': selected_key = f'{page_key}_rejected_selected'
        else: selected_key = f'{page_key}_lesson_selected'

        if update_filter_state: update_filter_state()   # If specified, we save the filter sate
        ss[selected_key] = lesson_id                    # We retrieve the selected lesson/draft by ID
        st.rerun()                                      # Rerun to show selected lesson/draft


def display_lesson_overview(lesson_id: int, page_key: str, active_tags: list[str], 
    update_filter_state: Callable=None, show_status: bool=False) -> None:
    ''' 
    Displays the given lesson
    PARAMETERS:
        > lesson_id: ID of the lesson to display
        > page_key: key of the page from which the function is called from. It's important
            since the names of the variables stored in session state depend on the page_key
        > active_tags: tags that match the filters, will be shown in diffent color
        > update_filter_state: a function that updates the filter state before changing
            the display to show a lesson/draft. The function is defined in the page where
            display_lesson_collapsed so the function is different depending on the page is called from
        > show_status: whether to show the status of the lesson (e.g. filtersearch has no interest in status)
    '''

    ### DISPLAY

    status = ss.lessons.get_lesson_field(lesson_id, 'Status')

    with st.container(border=True):
        # Header: author and date
        author_col, date_col = st.columns(2)
        with author_col:
            user_id = ss.lessons.get_lesson_field(lesson_id, 'User_ID')
            st.markdown(f'_By: {ss.users.get_user_field(user_id, 'Name')}_')
        with date_col:
            # Inside a stylable container for right alignment
            with stylable_container(key='right_alignment', css_styles='{text-align:right}'):
                date = ss.lessons.get_lesson_field(lesson_id, 'Date')
                st.markdown(f'_Date created: {date.strftime('%d/%m/%Y')}_')

        # Title
        st.markdown(f'### :red[{ss.lessons.get_lesson_field(lesson_id, 'Title')}]')

        # Lesson/draft description cut to maximum characters allowed in overview
        desc = ss.lessons.get_lesson_field(lesson_id, 'Description')
        if len(desc) > MAX_DESC_LEN: desc = desc[:MAX_DESC_LEN] + '...'
        st.markdown(f'{desc}')

        #Añadir el documento de esa lesson????

        # Display all lesson tags, but if the tag is active, display in red
        all_tags = ss.lessons.get_lesson_tags(lesson_id, TAG_FIELDS)
        colors = ['red' if tag in active_tags else 'lightslategrey' for tag in all_tags]
        if show_status:
            all_tags = [status] + all_tags
            colors = [STATUS_COLOR[status]] + colors
        tagger_component(content='Tags:', tags=all_tags, color_name=colors)

        # Button text and key change depending on status
        if status == 'Draft': 
            label = 'Edit lesson'
            button_key = f'{page_key}_edit_{lesson_id}'
        else: 
            label = 'Read more'
            button_key = f'{page_key}_readmore_{lesson_id}'

        # Readmore/edit button
        st.button(label=label, type='secondary', use_container_width=True, key=button_key)
        
    ### SELECTED LESSON/DRAFT EVENT

    if ss[button_key]:
        # If button is clicked, we need to add a new selected variable to session_state
        # This selected variable will be catched in the next rerun and the lesson/draft will be displayed
        if status == 'Draft': selected_key = f'{page_key}_draft_selected'
        elif status == 'Rejected': selected_key = f'{page_key}_rejected_selected'
        else: selected_key = f'{page_key}_lesson_selected'

        if update_filter_state: update_filter_state()   # If specified, we save the filter sate
        ss[selected_key] = lesson_id                    # We retrieve the selected lesson/draft by ID
        st.rerun()                                      # Rerun to show selected lesson/draft


def reset_form(form_type: str) -> None:
    ''' Clears all fields of the page_key specified '''
    
    ss[f'{form_type}_title'] = ''
    ss[f'{form_type}_adc'] = None
    ss[f'{form_type}_client'] = ''
    ss[f'{form_type}_scope'] = []
    ss[f'{form_type}_tech'] = []
    ss[f'{form_type}_end_user'] = ''
    ss[f'{form_type}_segment'] = None
    ss[f'{form_type}_ig_stkh'] = ''
    ss[f'{form_type}_og_stkh'] = ''
    ss[f'{form_type}_dest_country'] = None
    ss[f'{form_type}_desc'] = ''
    # ss[f'{page_key}_files'] = None


def submit_form(form_type: str, update_id: int = None, as_draft: bool = False) -> None:
    ''' 
    Called when a lesson is created or modified
    PARAMETERS:
        > form_type: type of the form ('new', 'draft', 'rejected')
        > update_id: if the lesson already exists and we want to update it, its ID
        > as_draft: whether we want to save the lesson as draft (if the lesson exists or not)
    '''
    if as_draft:
        if form_type == 'rejected':
            status = 'Rejected'  # We want to remember that the lesson is Rejected
        else:
            status = 'Draft'  # Update draft or save new lesson as draft
    else:
        status = 'Pending'  # If submitted, always status is Pendind

    if form_type == 'new':  # The lesson does NOT exist
        ss.lessons.add_entry(
            title=ss[f'{form_type}_title'],
            adc=ss[f'{form_type}_adc'],
            client=ss[f'{form_type}_client'],
            scope=ss[f'{form_type}_scope'],
            tech=ss[f'{form_type}_tech'],
            end_user=ss[f'{form_type}_end_user'],
            segment=ss[f'{form_type}_segment'],
            ig_stkh=ss[f'{form_type}_ig_stkh'],
            og_stkh=ss[f'{form_type}_og_stkh'],
            dest_country=ss[f'{form_type}_dest_country'],
            date=ss[f'{form_type}_date'],
            user_id=ss[f'{form_type}_user'],
            desc=ss[f'{form_type}_desc'],
            status=status,
            #files= ss[f'{form_type}_files'] #Quitarlo?
        )

    elif form_type in ['draft', 'rejected']:  # The lesson already exists
        ss.lessons.update_entry(
            lesson_id=update_id,
            title=ss[f'{form_type}_title'],
            adc=ss[f'{form_type}_adc'],
            client=ss[f'{form_type}_client'],
            scope=ss[f'{form_type}_scope'],
            tech=ss[f'{form_type}_tech'],
            end_user=ss[f'{form_type}_end_user'],
            segment=ss[f'{form_type}_segment'],
            ig_stkh=ss[f'{form_type}_ig_stkh'],
            og_stkh=ss[f'{form_type}_og_stkh'],
            dest_country=ss[f'{form_type}_dest_country'],
            date=ss[f'{form_type}_date'],
            user_id=ss[f'{form_type}_user'],
            desc=ss[f'{form_type}_desc'],
            status=status,
            #files= ss[f'{form_type}_files'] #Quitarlo?
        )
    
    if as_draft:
        message = 'Changes saved.'
    else:
        message = 'Form submitted successfully'
    st.toast(body=message)

    if form_type == 'new':
        reset_form(form_type=form_type)
    
    uploaded_file = ss[f'{form_type}_files']
    if uploaded_file is not None:
        upload_azure(uploaded_file)

def display_edit_lesson(form_type: str, lesson_id: int=None, border: bool=False):
    ''' 
    Used to display the widgets to either create a new lesson or modify a draft/rejected lesson. 
    PARAMETERS:
        > form_type: either 'new', 'rejected' or 'draft'
        > lesson_id: if the lesson already exists we need its ID to modify it
        > border: whether the container has a border of not '''
    
    # Headers and buttons names change according to form_type
    if form_type == 'new':
        header = 'Submit new lesson'
        submit_label = 'Submit lesson'
        as_draft_label = 'Save draft'
    elif form_type == 'rejected':
        header = f'Edit lesson `ID={lesson_id}`'
        submit_label = 'Re-submit lesson'
        as_draft_label = 'Save as draft'
    elif form_type == 'draft':
        header = f'Edit draft `ID={lesson_id}`'
        submit_label = 'Submit draft'
        as_draft_label = 'Save draft'

    # If the lesson already exists, retrieve its fields
    title =         '' if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Title')
    scope =         None if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Scope')
    segment =       None if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Segment')
    dest_country =  None if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Destination_Country')
    adc =           None if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'AdC')
    tech =          None if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Technology')
    ig_stkh =       '' if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'IG_Stakeholder')
    date =          None if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Date')
    client =        '' if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Client')
    end_user =      '' if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'End_User')
    og_stkh =       '' if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'OG_Stakeholder')
    desc =          '' if form_type=='new' else ss.lessons.get_lesson_field(lesson_id, 'Description')

    with st.container(border=border):
        # Title
        st.subheader(header, divider='red')

        # Create columns (by rows to avoid mismatched columns)
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        row3_col1, row3_col2, row3_col3 = st.columns(3)
        row4_col1, row4_col2, row4_col3 = st.columns(3)
        row5_col1, row5_col2 = st.columns([2, 2])

        # Display allllllll the widgets, their keys depend on the form_type!]

        row1_col1.text_input(label='Title:red[*]', key=f'{form_type}_title', max_chars=100, value=title)
        row2_col1.multiselect(label='Scope', options=OPTIONS_SCOPE, key=f'{form_type}_scope', default=scope)
        row3_col1.selectbox(label='Segment', options=OPTIONS_SEGMENT, key=f'{form_type}_segment',
                            index=OPTIONS_SEGMENT.index(segment) if segment in OPTIONS_SEGMENT else None)
        row4_col1.selectbox(label='Destination Country', options=OPTIONS_COUNTRY, key=f'{form_type}_dest_country',
                            index=OPTIONS_COUNTRY.index(dest_country) if dest_country in OPTIONS_COUNTRY else None)

        row1_col2.selectbox(label='AdC:red[*]', options=OPTIONS_ADC, key=f'{form_type}_adc',
                            index=OPTIONS_ADC.index(adc) if adc in OPTIONS_ADC else None)
        row2_col2.multiselect(label='Technology', options=OPTIONS_TECH, key=f'{form_type}_tech',default=tech)
        row3_col2.text_input(label='IG Stakeholder', key=f'{form_type}_ig_stkh', value=ig_stkh)
        row4_col2.date_input(label='Date:red[*]', value=date if date else dt.datetime.now(), 
                             format='DD/MM/YYYY', key=f'{form_type}_date')

        row1_col3.text_input(label='Client:red[*]', key=f'{form_type}_client', value=client)
        row2_col3.text_input(label='End User', key=f'{form_type}_end_user', value=end_user)
        row3_col3.text_input(label='OG Stakeholder', key=f'{form_type}_og_stkh', value=og_stkh)
        row4_col3.text_input(label='User:red[*]', value=ss.username, disabled=True, key=f'{form_type}_user')
        uploaded_file = row5_col1.file_uploader("Lesson's files", key=f'{form_type}_files', disabled=False)
        
        # NOTE 
        #if uploaded_file is not None:
            #upload_azure(uploaded_file,title)
        row5_col2.text_area(label='Description', key=f'{form_type}_desc', max_chars=1000, value=desc)

        # Conditions where the buttons are disables, always date and title, to submit need some more fields
        submit_disabled = ('' in [ss[f'{form_type}_title'], ss[f'{form_type}_client'], ss[f'{form_type}_user']] ) \
                           or (None in [ss[f'{form_type}_adc'], ss[f'{form_type}_date']])
        as_draft_disabled = ('' in [ss[f'{form_type}_title'], ss[f'{form_type}_user']] or None == ss[f'{form_type}_date'])

        st.markdown('<small>Fields marked with (:red[*]) are mandatory.</small>', unsafe_allow_html=True)
        if submit_disabled: help_text = ':red[You still have mandatory fields empty!]'
        else:               help_text = ''

        # Button to submit lesson
        st.button(label=submit_label, type='primary', disabled=submit_disabled, use_container_width=True, on_click=submit_form, 
                  kwargs={'form_type': form_type, 'update_id': lesson_id}, help=help_text, key='submit_lesson_button')
    
    
        # Button to save as draft
        st.button(label=as_draft_label, type='secondary', use_container_width=True, on_click=submit_form, 
                  kwargs={'form_type': form_type, 'update_id': lesson_id, 'as_draft': True}, key='save_as_draft_button',
                  disabled=as_draft_disabled)
        
        
    

#Function creation to upload documents to 
def upload_azure(uploaded_file):
    try:
        # Blob service connection
        connect_str = 'DefaultEndpointsProtocol=https;AccountName=mlstorageiberia;AccountKey=UaMctGtF7/03jsI4CI2kuWcvHWxpn5wwUeoKSOfBoQTDEPFjEO4cLSIq9WMIDZ82FTX6r71vXJaJ+AStPpSJ7g==;EndpointSuffix=core.windows.net'
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)

        # Container_name creation to access to azure container
        container_name = "lessonsinsync"
        container_client = blob_service_client.get_container_client(container_name)
            
            # Interaction with a specific blob client
        blob_client = container_client.get_blob_client(uploaded_file.name)
        blob_client.upload_blob(uploaded_file, overwrite=True)
            
            #Success message
        st.success("File uploaded successfully")
                       
    except Exception as e:
        st.error(f"Error uploading file: {e}")