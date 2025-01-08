

<!-- 

IN VISUAL STUDIO CODE
> CTRL+SHIFT+V
FOR BETTER READABILITY

 -->


# LessonInSync

Web app for Power Systems BU experience exchange.
[Based on this doc](https://schneiderelectric-my.sharepoint.com/:w:/r/personal/sesa663731_se_com/_layouts/15/doc2.aspx?sourcedoc=%7B8bc5de1a-e0df-447f-8d3b-1f9b98958de1%7D&action=view&wdAccPdf=0&wdparaid=5F2F67C0).

## Requirements

Requirements are specified in `requirements.txt`. I user `pigar` to generate them. To install requirements run:
```
py -m pip install requirements.txt
```
Apart from the `pyodbc` module, it is also needed to have the [ODBC driver](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16) install on your computer.

## To run the app

To run the app execute the main script `lessonsinsync.py` from the main directory with the following command:
```
py -m streamlit run lessonsinsync.py
```


## Note on streamlit `rerun`, `session_state` and `cache`

Streamlit works in a veeery unique way. Everytime the user interacts with the app (changing pages, using widgets, reload the page, etc.) a `st.rerun()` event is raised. Then the *whole* script is run again, from top to bottom (if no other rerun events happen in the meantime, that could). Callbacks, raised by widgets, are executed as the *first* thing of reruns.

To save information between pages and reruns, we can use the `st.session_state` to save variables and widget states. It is essentially a very big and helpful dictionary. Note that even tought widgets are added automatically to session_state, widgets are only stateful for a short time, so it's always better to add them "manually".

Since *all* the script is rerun on every single user interaction, there are processes that too computational expensive that we'd rather not have them running every single time. Streamlit allows to store function returns in cache, by using either `st.cache_data` (for seriazable data) or `st.cache_resource` (for unseriazable data) decorators. If we have a function on cache, and we call it again with the *same parameters*, the function won't be executed: we will get the past execution cached result.


## Links to documentation

* [streamlit](https://docs.streamlit.io/): To learn how streamlit works and to find the specification of each widget.

* [streamlit_authenticator](https://github.com/mkhorasani/Streamlit-Authenticator): You can find snippets of code on how to use each widget.

* [streamlit_extras](https://extras.streamlit.app/): Good to find new functionalities to add to the app. I already use `tags` for showing the tags under a lesson in the filter results search and `stylable_container` to add CSS styles (for now only right alignment and background colors). 


## General overview

### Class interface for databases

Each database is stored inside a class to manage it more easily. That way we can query or modify the database by using a simple class method call. For LessonInSync we use the `Lessons` and `Users` classes.

### Lessons

Lessons have 4 statuses:

* `Accepted` lessons have been approved by an administrator, other users can browse them and save them. They are not editable since they are considered to be good.

* `Pending` lessons are lessons waiting for admin approval to be launched in the lesson pool. They are non-editable and only seen by the lesson author and admins.

* `Rejected` lessons are lessons rejected by an administrator, the reason of their rejection is written by the admin in a comment that is shown to the user. Users can edit rejected lessons and re-submit them, then they become pending again.

* `Draft` lessons are only seen by the user, they can be edited and submited as a pending lesson.

A lesson is a line in the `LessonsInSync_Lessons` Azure SQL databse, that has the following columns:

(`Lesson_ID`, `Status`, `User_ID`, `Title`, `AdC`, `Client`, `Scope`, `Technology`, `End_User`, `Segment`, `IG_Stakeholder`, `OG_Stakeholder`, `Destination_Country`, `Date`, `Description`, `Likes`, `Status_Comments`)

### Users

Users are split into two roles:

* `User` role will be the role of the majority of the userbase, they can create, browse and save lessons.

* `Admin` role users review submitted lesson so that they meet a minim quality and correction criteria before being available to all users to see. They can also grant and revoke admin roles to other users.

User data is stored in two ways as well:

* Every user is a line in the `LessonsInSync_Users` Azure SQL database, that has the following columns: (`User_ID`, `Role`, `Name`, `Liked_Lessons`)

* User credentials are stored in `config.yaml`. This file is managed by the `streamlit_authenticator.Authenticate` object. The main difference between this file and the users database is that this file stores the **hashed password** of each user.


## Multiuse functions

There are multiple visualizations that are the similar over different pages, to avoid repeating the same code over all those pages, general functions have been defined.

> This visualizations are **similar** but not the same. We need some type of differentiation _depending from which page we call this functions from or in which context_. Because this functions add variables to the state that are later on catched by those pages, we need to be extra careful with which keys we give to each variable.

That's why there are two important concepts:

* `page_key`: a key associated with a page that is passed in some functions to denote from which page we called the functions from, can be `mylessons`, `filtersearch`, `admin`.

* `form_type`: used when a user creates/modifies a lesson, can be: `new`, `rejected`, `draft`.

This is further explained later on in more depth.


### Filter state

Streamlit is rerun on every user interaction, that means that if a user selects some filters and then choses a lesson, reads it and goes back to the filters, _the filters they selected won't be saved_.

Thats why the app keeps track of the filter state manually. By performing these two tasks:

1. In every page, the **filter state is restarted** except the state of the current page. That is, if we are in `My Lessons` and then go to `Filter Search` we don't want to save the filter state of `My Lessons`, but we want to start to remember the state of the filters of `Filter Search`. 

    That's easily done with the function `reset_filter_state(except_page_key: str=''):`

2. Every time a lesson is selected, the **filter state is saved**. That is done by `update_filter_state(initialize: bool=False):`. It reads the info on the widgets and saves it to the state, this function is also used to initialize the filter state if specified to. This function is passed as a parameter to the function that print the overview of each lesson.


# File by file explanation

> Note: Each file begins with `ss.authenticator.login(location='unrendered')` to make sure that the user is stilled logged in.

## `lessonsinsync.py`

The main script from where the app is run. It's split in setup and navigation:

* **setup**: Establish connection to databases, instantiate `Lessons`, `Users` and `streamlit_authenticator.Authenticate` and store them in session state.

* **navigation**: Load pages. If no user is logged in, display the login/register page. Otherwise display all pages.

    > The role of the user is retrieved, if the user has admin roles they have an extra admin section.

## `my_lessons.py`, `filter_search.py` and `manage_lessons.py` 

> I will explain how `my_lessons.py` works extensively and then comment how it differs from the other two.

The `my_lessons.py` page is for the logged in user to see their lessons. It is simply a list of lessons that can be selected and read/modified.

1. The first part of this file is calling `reset_filter_state(except_page_key='mylessons')` in order to forget the filter state of other pages and start remembering the filter state of _this_ page. 

2. Then we check if the filter state of `page_key='mylessons'` is initialized, if not, we call `update_filter_state(initialize=True)`

    > Note that `reset_filter_state` is a function used by My Lessons, Filter Search and Manage Lessons (admin) defined in `functions.py`; while `update_filter_state` is defined in My Lessons, because **each page has a specific function to update their filter state** depending on the filters it has.

3. The rest of the page is a big if-elif-else block that has this structure:

    ```
    if mylessons_lesson_selected in session_state:
    elif mylessons_rejected_selected in session_state:
    elif mylessons_draft_selected in session_state:
    else:
    ```

    * The first three options display a lesson (accepted or pending), a rejected lesson and a draft respectively.

        `filter_search.py` only displays accepted lessons from all the userbase and allows for the current user to like the selected lesson.

        `manage_lessons.py` only displays pending lessons and allows for admins to accept/reject them and give comments.

        > The perks of how the lessons are displayed will be expained in `functions.py` since it varies from page to page.

    * If no lesson is selected to be displayed, we show the filter options. We use the **filter state** to display the previous values of the filters if there are any. Then we call the `Lessons.filter_by()` method passing all the relevant arguments (for example in My Lessons we _need_ to filter by the current logged in user ID).

        Then we display the lessons calling a function in `functions.py` that is responsible of the display and to **add the ID of a lesson to the state if the lesson is selected**.


## `functions.py`

The main purpose of this file is to unify processes/displays that are very similar over diffent pages. 

### `reset_filter_state`

It has already been explained that we need to remember the filters _manually_ while the user is browsing lessons for better experience. This functions deletes from the session state all pages filter state and selected lesson **except** (if wanted) a specified page key.

### `display_lesson_details`

This function is used in non-editable lesson view, to display the lesson fields in a nice box.


### `display_lesson_collapsed` and `display_lesson_overview`

These two functions are used to display the lessons when they appear as search results, either as an overview (title, author, date, tags and a part of the description) or collapsed (just title).

> One parameter that only `display_lesson_overview` has is `active_tags`. In the overview, below the short description I found it nice to display the 'tags' of the lesson. That is, the value of some of its fields. But it would be really nice if the options the user selected in the filters appeared red in the tags. Thats why, `Lessons.filter_by()` returns also the active tags of a lesson, that is, the fields of the lesson that are an option in some filter.

These functions also create a button to read/edit the lesson. These buttons have unique keys since they are appended the ID of the lesson (**keys must be unique in session state**). Clicking this **button** takes you to the full lesson display, internally it works by:

1. Saving the filter state. This is done by calling `update_filter_state()` that is passed to the function as a parameter (since each page has its own definition).

2. Adding `{page_key}_{type}_selected` to session state with the selected lesson ID. `page_key` can be 'mylessons', 'admin' or 'filtersearch' and `type` refers whether the lesson is to be displayed as 'lesson', 'rejected' or 'draft'.

3. Calling `st.rerun()` to rerun the app so that the selected lesson can be displayed (remember the if-elif-else structue of `my_lessons.py`!)

### `reset_form`, `submit_form` and `display_edit_lesson`

> Note: This three functions are used to submit new lessons and to edit drafts and rejected lessons (thought they all seem different from outside they're essentially the same). We use the parameter `form_type` to specify the case: 'new', 'rejected' and 'draft'.

The whole process goes as this:

1. Call `display_edit_lesson()` with a form_type. The 'rejected' and 'draft' cases _need_ also a lesson ID to be passed.

1. Choses the header and button text depending on the `form_type`.

2. In 'rejected' and 'draft' cases, we retrieve the already existing lesson's fields. If it's new we just leave it blank.

4. Create columns and display options.

5. Check if enough fields are filled to submit the lesson or save it as draft.

    *  To **submit** lesson must have: `Title`, `Client`, `User`, `AdC` and `Date`.

    * To save as **draft** lesson must have: `Title`, `User` and `Date`.

        > `User` is already filled (with the logged in user ID) and `Date` defaults to the current day.

6. If conditions are met, call `submit_form()`. We have to speficy the `form_type`. If its 'rejected' or 'draft' we also need to pass the lesson id. Also we can pass an extra parameter `as_draft=True` if we want to save the lesson as draft (independently if it already exists or not).

7. The first thing before updating the database is to calculate the new status. We use the following logic:

    ```
    if as_draft:
        if form_type == 'rejected': status = 'Rejected'
        else: status = 'Draft'
    else:
        status = 'Pending'
    ```

8. If `form_type='new'` we call `Lesson.add_entry()` and then `reset_form()`

9. If `form_type='rejected'/'draft'` we call `Lesson.update_entry()`, we don't clear the form fields.


## `classes.py`

Contains the definition of the `Lessons` and `User` classes, that are used to manage the corresponding databases `LessonsInSync_Lessons` and `LessonsInSync_Users` hosted in **Azure SQL**.

> The way the databases are managed boosts performance in terms of speed when filtering and retrieving fields, but the downside is that the databases are **not syncronized** until the user re-opens the app.

When `Lessons` and `Users` are instantiated they create a dataframe copy of the remote SQL database. When the user modifies lessons, likes lessons and such, the user's changes are pushed to the remote SQL and to the dataframe copy.

**BUT!** The other users' changes are do NOT reach the current user until they re-open the app.

> I think that this interface does not cause any operational issues apart from not being syncronized simutaneusly. ~~But who knows! Time will tell~~


## `manage_admins.py`

This pages is only for administrators an its purpose is to control administrator acces. It has two entries to enter a username and two buttons to grant/revoke admin. There is also a small table displayed below so that admins can check the status of each user.


## `globals.py`

Contains global variables that are used by some part of the app. What each variable does is already specified in the comments.


## Session related

#### `login.py`

Page with two tabs, one to login another to register. They already work fine and their implementation is mostly copied from the streamlit authenticator github.

#### `logout.py`

Just a logout button.

#### `credentials/config.yaml`

File that contains the hashed passwords of all users. Is is managed by the authenticator object. 

> For now it is stored locally but it would be ideal to move it to **Azure Storage** at some point.


## Pages to be further implemented

#### `dashboard.py`

Idea: When user logs in, they are greeted and shown some statistics: new lessons approved, new likes, new lessons they may be interested in, etc.

#### `my_account.py`

Where the user can change their data. Reset password widget is already working but still need to implement the forgot password widget in the login.

#### `likes.py`

Shows the user's liked lessons. For now it only displays the collapsed view of those lessons. Visualization can be improved.

#### `field_request.py`

**Idea**: The options in the dropdowns are specified in `globals.py`. If a user wants to use an option that is not in the dropdowns, they can make a request that needs to be later approved/rejected by an admin.

#### `intelligent_search.py`

Use **Azure AI Search** to allow searching using natural language. The page interface would be similar to `filter_search.py`, only the filter function should be changed.


## Future features

* In `my_lessons.py`, `filter_search.py` and `manage_lessons.py` add **arrows to navigate** between filter results. The filter function returns a list of IDs, using the number of results shown and a modulus it can be implemented easily. Disable buttons if no navigation available.

* Implement the `intelligent_search.py` using **Azure AI Search**.

* Implement the **forgot password** widget: user enters username, an email is sent to them with a new password that they can change in the reset password widget. Use [smtplib](https://docs.python.org/3/library/email.examples.html) python module.

* Allow to upload files/download files in lesson creation/view. Investigate how fields would be stored, in Azure?

* Store `config.yaml` file, that holds user credentials (espectially the hashed passwords) in **Azure Storage**. 