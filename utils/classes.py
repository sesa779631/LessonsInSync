import operator
import pyodbc
import jsonpickle
import pandas as pd
from datetime import datetime



class Lessons():
    ''' Class to manage the LessonsInSync_Lessons database.
        >>  The class creates a DataFrame replica of the SQL database by retrieving 
            everything on instantiation.
            WHY? The filter function is complex, it is easier to implement in python syntax.
            Also the number of queries to the server is reduced.
        >>  Everytime there is a modification the DataFrame is updated as well as
            the remote SQL database (parallel updating). '''


    # Columns that allow multichoice, they need to be treated carefully since they
    # are stored in the database as a serialized `list` generated with jsonpickle.
    _list_columns = ['Scope','Technology']
    

    def __init__(self, cursor: pyodbc.Cursor, table_name: str) -> None:
        ''' Lessons class constructor. Receives the cursor (shared over all tables)
            and the table_name of the lessons table '''

        query_col_data = f'''
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = N'{table_name}'
        '''
        query_values = f'''
        SELECT * FROM {table_name}
        '''
        cursor.execute(query_col_data)
        col_names = [col_data[0] for col_data in cursor.fetchall()]
        cursor.execute(query_values)
        values = [list(row) for row in cursor.fetchall()]

        self._cursor = cursor
        self._table_name = table_name
        self._lessons = pd.DataFrame(data=values, columns=col_names)
        self._lessons['Date'] = pd.to_datetime(self._lessons['Date']).dt.date # Convert date to datetime type


    def __get_index(self, lesson_id: int) -> int:
        ''' Internal method. Returns the index of the row of the given lesson ID'''
        return self._lessons.index[self._lessons['Lesson_ID'] == lesson_id].to_list()[0]


    def add_entry(self, status: str, user_id: str, title: str, adc: str, client: str, 
                  scope: list[str], tech: list[str], end_user: str, segment: str, ig_stkh: str, 
                  og_stkh: str, dest_country: str, date: datetime, desc: str) -> None:
        
        # Insert new row in the remote SQL
        add_row = f'''
        INSERT INTO {self._table_name}(Status, User_ID, Title, AdC, Client, Scope, Technology, End_User,\
                Segment, IG_Stakeholder, OG_Stakeholder, Destination_Country, Date, Description, Likes, Status_Comments)
        VALUES ('{status}', '{user_id}', '{title}', '{adc}', '{client}', '{jsonpickle.encode(scope)}',\
            '{jsonpickle.encode(tech)}', '{end_user}', '{segment}', '{ig_stkh}', '{og_stkh}', '{dest_country}', '{date}', '{desc}', 0, '')
        '''
        self._cursor.execute(add_row)
        self._cursor.commit()
        
        # The Lesson ID is the smallest available index (length of table)
        # That is lessons are numbered 0, 1, 2, ...
        query_lesson_id = f'''
        SELECT COUNT(Lesson_ID)
        FROM {self._table_name};
        '''
        self._cursor.execute(query_lesson_id)
        new_index = self._cursor.fetchval() - 1 # NEED TO SUBSTRACT 1

        # We insert new row at the end of the dataframe
        self._lessons.loc[new_index] = [
            new_index, status, user_id, title, adc, client, jsonpickle.encode(scope), 
            jsonpickle.encode(tech), end_user, segment, ig_stkh, og_stkh, dest_country, date, desc, '', 0
        ]


    def update_entry(self, lesson_id: int, status: str, user_id: str, title: str, adc: str, 
                     client: str, scope: list[str], tech: list[str], end_user: str, segment: str, ig_stkh: str, 
                     og_stkh: str, dest_country: str, date: datetime, desc: str) -> None:
        ''' Given a Lesson ID, updates that lesson's fields 
            (except number of likes that are managed separately)'''
        
        index = self.__get_index(lesson_id) # Index of lesson in dataframe
        # Fields that are not editable by the user need to be retrieved manually
        likes = self.get_lesson_field(lesson_id, 'Likes')
        status_comments = self.get_lesson_field(lesson_id, 'Status_Comments')

        # Update lesson in datafrane
        row = [lesson_id, status, user_id, title, adc, client, jsonpickle.encode(scope), 
               jsonpickle.encode(tech), end_user, segment, ig_stkh, og_stkh, dest_country, date, desc, status_comments, likes]
        self._lessons.loc[index] = {k:v for k,v in zip(self._lessons.columns, row)}
        
        # Update lesson in remote SQL
        update_row = f'''
        UPDATE {self._table_name}
        SET Status = '{status}', User_ID = '{user_id}', Title = '{title}', AdC = '{adc}', Client = '{client}',\
            Scope = '{jsonpickle.encode(scope)}', Technology = '{jsonpickle.encode(tech)}', End_User = '{end_user}', Segment = '{segment}',\
            IG_Stakeholder = '{ig_stkh}', OG_Stakeholder = '{og_stkh}', Destination_Country = '{dest_country}',\
            Date = '{date}', Description = '{desc}'
        WHERE Lesson_ID = {lesson_id};
        '''
        self._cursor.execute(update_row)
        self._cursor.commit()


    def filter_by(self, filters: dict[str, list[str]], mode: str='AND', status: list[str]=None,
                  max_results: int=25, sort_by: str=None, keywords: list[str]=None, start_date: str=None,
                  end_date: str=None, user_id: str=None) -> tuple[list[int], list[list[str]]]:
        ''' 
        The filter function.
        PARAMETERS:
            > filters: a dictionary {column_name: list_of_values} to filter the dataframe
                    if the column value is in the list
            > mode: defaults to 'AND', whether the results should match all the conditions
                    specified in filters or just one. 
                    It ONLY applies to filters and keywords, not to the other criteria explained below
            > status: if specified list of statuses that the filtered lessons must belong to
            > max_results: if specified max results returned by the function
            > sort_by: if specified column name to sort results by (otherwise it defaults
                    to greatest number of matches)
            > keywords: keywords to search for in the description of the lesson
            > start_date & end_date: if specified time window in which retrieve lessons from
            > user_id: if specified return only lessons of that user
        RETURNS:
            A tuple with two lists:
            > a list containing the IDs of the filtered lessons
            > a list containing the active tags of each lesson, the active tags are the fields
              of the lesson that match the filters
        '''

        # NOTE: use & and | instead of 'and' and 'or' to combine masks

        # Mode AND: operator=AND, mask=True. Mode OR: operator=OR, mask=False.
        # We filter by logically combining masks and then applying it to the dataframe in the end
        op = operator.and_ if mode=='AND' else operator.or_
        mask = pd.Series([True if mode=='AND' else False for _ in range(len(self._lessons))])

        # Dataframe to store the active tags of each lesson
        tags = self._lessons[['Lesson_ID']].copy()
        tags['Active Tags'] = [[] for _ in range(len(self._lessons))]
        
        # 1. Filter by the filter dictionary
        for key, values in filters.items():
            if values: # If the filter is not empty

                # 1.A If the column is a multichoice column
                if key in self._list_columns:
                    values_set = set(values)
                    for idx, str_expr in self._lessons[key].items():
                        # We check if the intersection of the two lists is empty or not
                        intersection = list(set(jsonpickle.decode(str_expr)) & values_set)
                        mask.loc[idx] = op(mask.loc[idx], len(intersection) > 0)
                        tags.at[idx, 'Active Tags'] = tags.at[idx, 'Active Tags'] + intersection

                # 1.B The column is a single value column   
                else:
                    for idx, cell_value in self._lessons[key].items():
                        mask.loc[idx] = op(mask.loc[idx], cell_value in values)
                        if cell_value in values:
                            tags.at[idx, 'Active Tags'] = tags.at[idx, 'Active Tags'] + [cell_value]

        # 2. Filter title by keywords
        if keywords and keywords[0] != '':
            kw_mask = pd.Series([False] * len(self._lessons))
            for kw in keywords:
                # We check keyword by keyword if the description contains it
                kw_mask = kw_mask | self._lessons['Title'].str.contains(kw, case=False)
            mask = op(mask, kw_mask) # Combine with master mask

        # 3. Filter by status
        if status:
            mask = mask & (self._lessons['Status'].isin(status))
        
        # 4. Filter by date
        if start_date:
            mask = mask & (start_date <= self._lessons['Date'])
        if end_date:
            mask = mask & (self._lessons['Date'] <= end_date)

        # 5. Filter by user ID
        if user_id:
            mask = mask & (self._lessons['User_ID'] == user_id)

        # Filter dataframe with mask (and cut results if max_results is not None)
        filtered_df = self._lessons[mask].head(max_results)

        if filtered_df.empty: # Corner case: no coincidences
            return [], []     # Return two empty lists
        
        # We also filter the tags dataframe to keep only the lessons that meet the conditions
        tags = tags[tags['Lesson_ID'].isin(filtered_df['Lesson_ID'])]

        # 6.A If specified to filter by a column, do it
        if sort_by:
            tags[sort_by] = filtered_df[sort_by] # Add that column to tags
            tags.sort_values(by=sort_by, inplace=True)
        
        # 6.B Otherwise sort by number of coincidences in tags
        else:        
            # Add new column that counts the number of coincidences (length of active tags list)
            tags['Coincidences'] = tags['Active Tags'].map(lambda x: len(x))
            if keywords and keywords[0] != '': 
                # Description containing keywords is a coincidence, we can add the keywords mask to add 1 easily
                # Note that while they have different sizes, they are added by index
                tags['Coincidences'] = tags['Coincidences'] + kw_mask
            tags.sort_values(by='Coincidences', ascending=False, inplace=True)

        # Return list of IDs and list of active tags 
        return list(tags['Lesson_ID']), list(tags['Active Tags'])
    
    
    def get_lesson_field(self, lesson_id: int, field: str) -> int | str | list[str]:
        ''' Given a lesson ID and a field name (aka a column name) returns
            that lesson's field (column) value '''

        index = self.__get_index(lesson_id)        

        # If field is a multicolumn choice, we need to decode it to return as list
        if field in self._list_columns:
            return jsonpickle.decode(self._lessons.at[index, field])
        
        # Otherwise the value at works just fine
        return self._lessons.at[index, field]
    
    
    def get_lesson_tags(self, lesson_id: int, fields: list[str]) -> list[str]:
        ''' Return the tags of a lesson, that is, a list of the specified fields '''

        lesson = self._lessons[self._lessons['Lesson_ID'] == lesson_id].iloc[0]
        tags = []
        for field in fields:
            # We need to make a distincion between multichoice fields and single value fields
            if lesson[field] and lesson[field] != 'None': 
                if field in self._list_columns:
                    tags += jsonpickle.decode(lesson[field])
                else:
                    tags.append(lesson[field])
        return tags
    

    def get_lesson_count(self, user_id: str) -> int:
        ''' Returns the number of lessons made by a user (pending, rejected and drafts included)'''
        return self._lessons[self._lessons['User_ID'] == user_id].shape[0]
    

    def set_lesson_status(self, lesson_id: int, status: str, comments: str='') -> None:
        ''' Changes the status of a lesson to the specified status '''
        index = self.__get_index(lesson_id)
        self._lessons.at[index, 'Status'] = status
        self._lessons.at[index, 'Status_Comments'] = comments

        change_status = f'''
        UPDATE {self._table_name}
        SET Status = '{status}', Status_Comments = '{comments}'
        WHERE Lesson_ID = {lesson_id};
        '''
        self._cursor.execute(change_status)
        self._cursor.commit()


    def add_like(self, lesson_id: int) -> None:
        ''' Adds a like to the lesson of the given ID '''
        index = self.__get_index(lesson_id)
        likes = self._lessons.at[index, 'Likes']
        self._lessons.at[index, 'Likes'] = likes + 1
        
        add_like = f'''
        UPDATE {self._table_name}
        SET Likes = {likes + 1}
        WHERE Lesson_ID = {lesson_id};
        '''
        self._cursor.execute(add_like)
        self._cursor.commit()


    def remove_like(self, lesson_id: int) -> None:
        ''' Removes a like from the lesson of the given ID '''
        index = self.__get_index(lesson_id)
        likes = self._lessons.at[index, 'Likes']
        self._lessons.at[index, 'Likes'] = likes - 1
        
        remove_like = f'''
        UPDATE {self._table_name}
        SET Likes = {likes - 1}
        WHERE Lesson_ID = {lesson_id};
        '''
        self._cursor.execute(remove_like)
        self._cursor.commit()
    



class Users():
    ''' Class to manage the LessonsInSync_Users database.
        >>  The class creates a DataFrame replica of the SQL database by retrieving 
            everything on instantiation. 
        >>  Everytime there is a modification the DataFrame is updated as well as
            the remote SQL database (parallel updating). 
        >>  It stores the reference of the lessons instance because it needs to user its methods'''
    

    _list_fields = ['Liked_Lessons'] # Fields that contained, encoded, handled separately


    def __init__(self, table_name: str, cursor: pyodbc.Cursor, lessons: Lessons) -> None:
        ''' Users class constructor, takes the table_name, the cursor shared over all tables
            and the instance of the Lessons class '''

        query_col_data = f'''
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = N'{table_name}'
        '''
        query_values = f'''
        SELECT * FROM {table_name}
        '''
        cursor.execute(query_col_data)
        col_names = [col_data[0] for col_data in cursor.fetchall()]
        cursor.execute(query_values)
        values = [list(row) for row in cursor.fetchall()]

        self._cursor = cursor
        self._table_name = table_name
        self._users = pd.DataFrame(data=values, columns=col_names)
        self._lessons = lessons        


    def __get_index(self, user_id: str) -> None:
        ''' Returns the index in the dataframe of the given user ID '''
        return self._users.index[self._users['User_ID'] == user_id].to_list()[0]
    
    def exists_username(self, user_id: str) -> bool:
        ''' Returns True if the given username exists in the database '''
        return user_id in self._users['User_ID'].values

    def add_new_user(self, user_id: str, name: str) -> None:
        ''' Adds a new user to the Users database.
            Liked_Lessons is a list field, so its serialization is stored '''
                
        new_index = len(self._users.index) # To add at the bottom of dataframe
        self._users.loc[new_index] = [user_id, 'User', name, jsonpickle.encode([])]

        # Update changes also in remote SQL
        add_row = f'''
        INSERT INTO {self._table_name}(User_ID, Role, Name, Liked_Lessons)
        VALUES ('{user_id}', 'User', '{name}', '{jsonpickle.encode([])}')
        '''
        self._cursor.execute(add_row)
        self._cursor.commit()

    
    def grant_admin(self, user_id: str) -> None:
        ''' To grant admin role to the specified user ID. User ID must be valid '''

        index = self.__get_index(user_id)
        self._users.at[index, 'Role'] = 'Admin'
        
        grant_admin = f'''
        UPDATE {self._table_name}
        SET Role = 'Admin'
        WHERE User_ID = '{user_id}';
        '''
        self._cursor.execute(grant_admin)
        self._cursor.commit()

    def revoke_admin(self, user_id: str) -> None:
        ''' To revoke admin role to the specified user ID. User ID must be valid '''

        index = self.__get_index(user_id)
        self._users.at[index, 'Role'] = 'User'
        
        revoke_admin = f'''
        UPDATE {self._table_name}
        SET Role = 'User'
        WHERE User_ID = '{user_id}';
        '''
        self._cursor.execute(revoke_admin)
        self._cursor.commit()
    

    def get_users(self) -> pd.DataFrame:
        ''' Returns dataframe with users data (Name, User_ID, Role)'''
        return self._users[['Name', 'User_ID', 'Role']]

    def get_user_field(self, user_id: str, field: str) -> str | list[str]:
        ''' Returns the field (column value) of the given user ID '''
        index = self.__get_index(user_id)
        if field in self._list_fields:
            return jsonpickle.decode(self._users.at[index, field])
        return self._users.at[index, field]
    
    
    def is_liked(self, user_id: str, lesson_id: int) -> bool:
        ''' Returns True whether given user has liked the given lesson '''
        return lesson_id in self.get_user_field(user_id, 'Liked_Lessons')
    
    
    def add_liked_lesson(self, user_id: str, lesson_id: int) -> None:
        ''' Adds a like to the given lesson BY the specified user.
            Lesson should not have been liked by the user before '''

        # Retrive lesson and add like
        liked_lessons = self.get_user_field(user_id, 'Liked_Lessons')
        liked_lessons.append(int(lesson_id))
        self._lessons.add_like(lesson_id)

        # Update dataframe
        index = self.__get_index(user_id)
        self._users.at[index, 'Liked_Lessons'] = jsonpickle.encode(liked_lessons)
        
        # Update remote SQL
        update_liked_lessons = f'''
        UPDATE {self._table_name}
        SET Liked_Lessons = '{jsonpickle.encode(liked_lessons)}'
        WHERE User_ID = '{user_id}';
        '''
        self._cursor.execute(update_liked_lessons)
        self._cursor.commit()

    def remove_liked_lesson(self, user_id: str, lesson_id: int) -> None:
        ''' Removes a like from the given lesson BY the scpecified user.
            Lesson should have been liked by the user before '''
        
        # Retrieve lesson and deduct like
        liked_lessons = self.get_user_field(user_id, 'Liked_Lessons')
        liked_lessons.remove(int(lesson_id))
        self._lessons.remove_like(lesson_id)

        # Update dataframe
        index = self.__get_index(user_id)
        self._users.at[index, 'Liked_Lessons'] = jsonpickle.encode(liked_lessons)

        # Update remote SQL
        update_liked_lessons = f'''
        UPDATE {self._table_name}
        SET Liked_Lessons = '{jsonpickle.encode(liked_lessons)}'
        WHERE User_ID = '{user_id}';
        '''
        self._cursor.execute(update_liked_lessons)
        self._cursor.commit()


    # def get_num_admins()