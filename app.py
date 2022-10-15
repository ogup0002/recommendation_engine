#Imports
from flask import Flask, Response
from flask_restful import Api, Resource, reqparse
import pymysql
import pandas as pd
import requests
from sklearn.naive_bayes import GaussianNB
from flask_cors import CORS
#App inititation
app = Flask(__name__)
api = Api(app)
#bypass CORS policy of the browser
CORS(app)
#Database connection to AWS MySQL instance
conn = pymysql.connect(
        user="sittofit",
        password="0AxPzbedoJFNTfPj67Pr",
        host="db.sittofit.tk",
        port=3306,
        database="recommendation",
        cursorclass = pymysql.cursors.DictCursor)
#Cursor object to run query in Python env
cursorObject = conn.cursor() 



preferences = {}
ratings = pd.DataFrame()

#Route for Rating function 
@app.route("/rating", methods = ['PUT'])
def rating_():
    #Parse json data object in the API call
    incoming_args = reqparse.RequestParser()
    incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
    incoming_args.add_argument("iid", type=int, help = "Item ID, only 4 digit integer value accepted.")
    incoming_args.add_argument("rating", type=int, help = 'User rating can only be number 1 or 2.')
    args = incoming_args.parse_args()
    #Store the ratings 
    ratings = args
    # print(ratings)
    #Fetch unique user id from parsed object  
    user_id = int(args['web_id'])
    # print(user_id)
    #Fetch item id as iid from parsed object
    iid = int(args['iid'])
    # print(iid)
    #Create panda dataframe of the user rating and the item id
    df = pd.DataFrame([ratings])
    # print(df)
    #Query to Insert user rating to the database
    d1 = '''INSERT INTO user_rating (web_id, iid, rating) values (%s, %s, %s)'''
    #Query to Updare user rating for the item id in the database if it already exist
    d2 = '''UPDATE user_rating set web_id = %s, iid = %s, rating = %s where (web_id = %s and iid = %s)'''
    #Query values for Insert 
    val1 = (df["web_id"][0], df["iid"][0], df['rating'][0])
    #Query values for Update
    val2 = (df['web_id'][0], df["iid"][0], df["rating"][0], df['web_id'][0], df["iid"][0])

    # user_rating = pd.read_sql('''select * from user_rating''', conn)
    # comp1 = [df['web_id'][0], df['iid'][0]]
    #Query to fetch the user rating of the item id
    sql_query = 'select * from user_rating where (web_id = "{}" and iid = "{}")'.format(user_id, iid)
    #Create dataframe of the stored user rating for the user id and the item id
    check = pd.read_sql(sql_query, conn)
    check = check[check['iid'] == iid]
    #print(check)
    # comp2 = [user_rating['web_id'].values, user_rating['iid'].values]
    #Check if check database is empty (which means there is no data for the matching user id and item id)
    if not check.empty:
        ## UPDATE
        cursorObject.execute(d2, val2)
        conn.commit()
    else:
        #INSERT
        cursorObject.execute(d1, val1)
        conn.commit()
#     conn.close() #Bug fixed
    return {'view': 'You have arrived here'} 
#Route for storing Preference
@app.route("/preference", methods = ['PUT'])
def preference():
    #Parse json data object in the API call
    incoming_args = reqparse.RequestParser()
    incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
    incoming_args.add_argument("preference", type=str, help = "List of preference (Python style) as a string")
    args = incoming_args.parse_args()
    preferences = args
    # user_id = preferences['web_id']
    # pref = preferences['pref']
    # print(user_id)
    # pref = []
    # for i in range(len(preferences['pref'])):
    #     a = ''.join(preferences['pref'][i])
    #     pref.append(a)
    #Create empty dataframe of the unique user id and preference 
    df = pd.DataFrame(columns = ['web_id', 'preference'])
    #Parse Json object into a list of two values (preference is passed as single string in value 2)
    lis = [preferences['web_id'], preferences['preference']]
    print(lis)
    #Store the lis value in the dataframe
    df = pd.DataFrame([lis], columns = ['web_id', 'preference'])
    # print(df)
    print(df['preference'][0])
    #Query to Insert user preference to the database
    d1 = '''INSERT INTO user_preference (web_id, preference) values (%s, %s)'''
    #Query to Updare user preference for the item id in the database if it already exist
    d2 = '''UPDATE user_preference set web_id = %s, preference = %s where (web_id = %s)'''
    #Query values for Insert
    val1 = (df["web_id"][0], df["preference"][0])
    #Query values for Update
    val2 = (df['web_id'][0], df["preference"][0], df['web_id'][0])
    #Query to fetch the user preference of the item id
    user_rating = pd.read_sql('''select * from user_preference''', conn)
    comp1 = df['web_id'][0]
    #Fetch rows from the column where user preference is for unique user id
    comp2 = user_rating.loc[user_rating['web_id'] == df['web_id'][0]]
    # print(comp2)
    #Check if user preference already exists
    if not comp2.empty:
        ## UPDATE
        cursorObject.execute(d2, val2)
        conn.commit()
        print('Inserted')
    else:
        ##INSERT
        cursorObject.execute(d1, val1)
        conn.commit()

#     conn.close()


    return {"View": "Success"}

#Route for Populating cards function 
@app.route("/cards", methods = ['PUT'])
def cards():
    #Parse json data object in the API call
    incoming_args = reqparse.RequestParser()
    incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
    args = incoming_args.parse_args()
    #Fetch user id from the parsed json object
    user_id = args['web_id']
    #Fetch weather data for Melbourne CBD
    url = "https://api.openweathermap.org/data/2.5/weather?lat=-37.840935&lon=144.946457&appid=c92389d6904463e3cb24208905434fd9"
    response = requests.get(url)
    json = response.json()
    #Access weather from the json object
    weather = json['weather'][0]['main']
    # user_id = 4321
    ## DATA
    data = pd.read_sql('''select * from outdoor''', conn)
    # data= data.drop(['Rating'], axis = 1)
    # data = data.astype({'Rating': 'int64'})

    ## User RATING Dummy Data
    # id = [1011, 1074, 1273, 1180, 2002]
    # Rating = [2,2, 1, 1, 2]
    # user = pd.DataFrame()
    # user["id"] = id
    # user["Rating"] = Rating
    
    # User Rating
    sql_query = 'select * from user_rating where web_id = "{}"'.format(user_id)
    user = pd.read_sql(sql_query, conn)
    #Make column name consistent with logic
    user = user.rename(columns={"iid": "id"})
    # User Preference
    sql_query = 'select * from user_preference where web_id = "{}"'.format(user_id)
    pref = pd.read_sql(sql_query, conn)
    pref = pref['preference'][0]
    print(pref)
    #Filter data according to user preference and set the number of output for Outdoor activities
    if 'Cycling' in pref:
        if weather == 'Rain':
            n = 3
        else:
            n = 2
    else:
        if weather == 'Rain':
            n = 3
        else:
            n = 4
    #Create temp of the data
    temp = data
    #User Ratings without the userid so it can be joint with activity data
    user = user.drop(['web_id'], axis = 1)
    #Check if there are user ratings for any item id
    if not user.empty:
        #Perform left join of user ratings on activity data
        merged = pd.merge(temp, user, on = 'id', how = 'left')
        #Fill empty ratings for all items as 0
        merged['rating'] = merged['rating'].fillna(0)
        merged = merged.astype({'rating': 'int64'})
    else:
        #If no user rating is present
        merged = temp
        #Fill all item rating as 0
        merged['rating'] = 0
        # merged['Rating'] = merged['Rating'].fillna(0)
        #Change data type of Rating to Int
        merged = merged.astype({'rating': 'int64'})
    #Create new dataframes to filter different preference choice
    temp1 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    temp2 = pd.DataFrame(columns = ["id", "title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    temp3 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    #Check for different preferences and create boolean data
    if 'Walking' in pref:
        temp1 = merged[merged.walking != False]
    if 'Cardio' in pref:
        temp2 = merged[merged.cardio != False]
    if 'Sightseeing' in pref:
        temp3 = merged[merged.sightseeing != False]


    # merging data as rows are reduced
    concat = pd.concat([temp1, temp2, temp3])
    #Check if no preference, use outdoor data as it is, data remains unfiltered
    if concat.empty:
        concat = temp
    #Reload library    
    from sklearn.naive_bayes import GaussianNB
    #Check if 50 user ratings are present for a user
    if len(concat[(concat['rating'] != 0)]) < 50:
        #If user rating count is less than 50, take random data
        df_elements = concat.sample(n)
    else:
        #If more than 50 user ratings is present for a user
        
        #Convert columns to category type for modelling
        concat["theme"] = concat["theme"].astype('category')
        #Create dict for category to their respective codes mapping
        d1 = dict(enumerate(concat['theme'].cat.categories))
         #Convert columns to category type for modelling
        concat["sub_theme"] = concat["sub_theme"].astype('category')
        #Create dict for category to their respective codes mapping
        d2 = dict(enumerate(concat['sub_theme'].cat.categories))
        #Change column values to category codes
        concat["theme"] = concat["theme"].cat.codes
        concat["sub_theme"] = concat["sub_theme"].cat.codes
        
        #Machine learning model to predict activities for user
        #train set of items with rating 1 or 2
        train = concat.loc[concat['rating'] != 0]
        #test set of items with rating 0
        test = concat.loc[concat['rating'] == 0]
        #Features for training
        x_train = train.loc[:, ~train.columns.isin(['rating', 'title'])]
        #Label set (rating)
        y_train = train['rating']
        #Features for testing
        x_test = test.loc[:, ~test.columns.isin(['rating', 'title'])]
        #Label set (rating)
        y_test = test['rating']
        #from sklearn.naive_bayes import GaussianNB
        #Define Gaussian Naive Bayes model
        gnb = GaussianNB()
        #Fit model on training set
        gnb.fit(x_train, y_train)
        #Make predictions on testing set (without labels)
        y_pred = gnb.predict(x_test)
        #Merging label column back to dataframes
        train['rating'] = y_train
        test['rating'] = y_pred

        #Merge train and test data
        pred = pd.concat([train, test])
        #Fetch items with rating as 2
        pred = pred.loc[pred['rating'] == 2]
        #Map category codes to actual field value in Theme and SubTheme
        pred['theme'] = pred['theme'].map(d1)
        pred['sub_theme'] = pred['sub_theme'].map(d2)
        #Sample the n number of rows from pred
        df_elements = pred.sample(n)
    #Remove preference boolean columns    
    df_elements = df_elements.drop(['walking', 'cardio', 'sightseeing', 'green_space'], axis = 1)
    # print(df_elements)

    from math import radians, cos, sin, asin, sqrt
    # HAVERSINE DISTANCE CALCULATION
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r
    # If cycling is in user preference
    if 'Cycling' in pref:
        #Fetch data for cycling from database
        bike = pd.read_sql('''select * from bicycle''', conn)
        #Leave original data unchnaged
        temp = bike

    #     if not user.empty:
        #Perform left join of bicycle data on user ratings
        bikemerged = pd.merge(temp, user, on = 'id', how = 'left')
        #Fill 0 where rating is not present
        bikemerged['rating'] = bikemerged['rating'].fillna(0)
        #Convert datatype of rating to int
        bikemerged = bikemerged.astype({'rating': 'int64'})
        #Fetch records where user rating for item is 2
        bike_high = bikemerged.loc[bikemerged['rating'] == 2]
        
        if not bike_high.empty:
            #If no user rating is present, randomly sample a record
            selection = bike_high.sample(1)
        else:
            bikemerged = bike
            #Fill 0 where user rating is not present
            bikemerged['rating'] = 0
            #Change dtype of rating to int
            bikemerged = bikemerged.astype({'rating': 'int64'})
            bike_high = bikemerged
            #Randomly sample a record
            selection = bike_high.sample(1)
        #Check if filtered data returned empty
        if selection.empty:
            record = bike.sample(1)
        else:
            #Calculate nearest distance with the liked record of the user
            lon, lat = selection['longitude'], selection['latitude'] 
            bikemerged['haversine_calc'] = [haversine(lon,lat, bikemerged['longitude'][i], bikemerged['latitude'][i])for i in range(len(bike))]
            bikemerged = bikemerged[bikemerged["haversine_calc"]>0]
    #         bikemerged = bikemerged.drop(['Unnamed: 0'], axis = 1)
            record = bikemerged.loc[bikemerged.haversine_calc == bikemerged.haversine_calc.min()]
            record = record.drop(['haversine_calc'], axis = 1)
        #Merge outdoor activities with bicycle
        output = pd.concat([df_elements, record])
    else:
        #If cycling is not a user preference, no element of cycling will be added
        output = df_elements

    # INDOOR ACTIVITY
    indoor = pd.read_sql('''select * from indoor''', conn)

    if not user.empty:
        #If user rating is present
        indoor = pd.merge(indoor, user, on = 'id', how = 'left')
        indoor['rating'] = indoor['rating'].fillna(0)
        indoor = indoor.astype({'rating': 'int64'})
    else:
        indoor['rating'] = 0

    if 'Cardio' in pref:
        # If cardio is in user preference, only take high intensity theme data
        indoor_act = indoor.loc[indoor['theme'] == 'High Intensity']
        #Randomly take 3 indoor activities
        indoor_act = indoor_act.sample(3)

    else:
        #If cardio is not in user preference, only take low intensity theme
        indoor_act = indoor.loc[indoor['theme'] == 'Low Intensity']
        #Randomly take 3 indoor activities
        indoor_act = indoor_act.sample(3)

    if weather == 'Rain':
        #Reduce number of rows if weather is rain
        indoor_act = indoor_act.sample(3)
        print(indoor_act)
    else:
        #if not raining, take rows as 3
        indoor_act = indoor_act.sample(3)
    #Randomly sample 4 rows from the final number of rows collected through each type of activity
    output_final = pd.concat([output, indoor_act]).sample(4)

    out = output_final.to_json(orient='index')    
    # print(out)

#     conn.close()
    return out


#Route for populating Popular cards 
@app.route("/popular", methods = ['PUT'])
def popularity():
    #Parse json data object in the API call
    incoming_args = reqparse.RequestParser()
    incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
    args = incoming_args.parse_args()
    #Fetch user id from the parsed json object
    user_id = args['web_id']
    #Fetch weather data for Melbourne CBD
    url = "https://api.openweathermap.org/data/2.5/weather?lat=-37.840935&lon=144.946457&appid=c92389d6904463e3cb24208905434fd9"
    response = requests.get(url)
    json = response.json()
    #Access weather from the json object
    weather = json['weather'][0]['main']
    # user_id = 4321
    ## DATA
    data = pd.read_sql('''select * from outdoor''', conn)
    
    sql_query = 'select * from user_rating where rating = 2'
    user = pd.read_sql(sql_query, conn)
    #Make column name consistent with logic
    user = user.rename(columns={"iid": "id"})
    # User Preference
    sql_query = 'select * from user_preference where web_id = "{}"'.format(user_id)
    pref = pd.read_sql(sql_query, conn)
    pref = pref['preference'][0]
    print(pref)
    #Filter data according to user preference and set the number of output for Outdoor activities
    if 'Cycling' in pref:
        if weather == 'Rain':
            n = 3
        else:
            n = 2
    else:
        if weather == 'Rain':
            n = 3
        else:
            n = 4
    #Create temp of the data
    temp = data
    #User Ratings without the userid so it can be joint with activity data
    user = user.drop(['web_id'], axis = 1)
    #Check if there are user ratings for any item id
    if not user.empty:
        #Perform left join of user ratings on activity data
        merged = pd.merge(temp, user, on = 'id', how = 'left')
        #Fill empty ratings for all items as 0
        merged['rating'] = merged['rating'].fillna(0)
        print(merged)
        merged = merged.astype({'rating': 'int64'})
    else:
        #If no user rating is present
        merged = temp
        #Fill all item rating as 0
        merged['rating'] = 0
        # merged['Rating'] = merged['Rating'].fillna(0)
        #Change data type of Rating to Int
        merged = merged.astype({'rating': 'int64'})
    #Create new dataframes to filter different preference choice
    temp1 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    temp2 = pd.DataFrame(columns = ["id", "title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    temp3 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    #Check for different preferences and create boolean data
    if 'Walking' in pref:
        temp1 = merged[merged.walking != False]
    if 'Cardio' in pref:
        temp2 = merged[merged.cardio != False]
    if 'Sightseeing' in pref:
        temp3 = merged[merged.sightseeing != False]


    # merging data as rows are reduced
    concat = pd.concat([temp1, temp2, temp3])
    #Check if no preference, use outdoor data as it is, data remains unfiltered
    if concat.empty:
        concat = temp
    #Reload library
    from sklearn.naive_bayes import GaussianNB
    #Check if 50 user ratings are present for a user
    concat_new = concat.loc[concat['rating'] == 2]
    if concat_new.empty:
        #If no users rating is available in the database for any user, randomly sample n rows
        df_elements = concat.sample(n)
    elif len(concat_new) < n:
        #If available users ratings is less than the number of rows required for n, randomly sample n rows
        df_elements = concat.sample(n)
    else:
        #If users ratings is available, randomly sample the rating 2 rows 
        df_elements = concat_new.sample(n)
    #Remove preference boolean columns
    df_elements = df_elements.drop(['walking', 'cardio', 'sightseeing', 'green_space'], axis = 1)
    # print(df_elements)

    from math import radians, cos, sin, asin, sqrt
    # HAVERSINE DISTANCE CALCULATION
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    if 'Cycling' in pref:
        #Fetch data for cycling from database
        bike = pd.read_sql('''select * from bicycle''', conn)
        #Leave original data unchnaged
        temp = bike

    #     if not user.empty:
        #Perform left join of bicycle data on user ratings
        bikemerged = pd.merge(temp, user, on = 'id', how = 'left')
        #Fill 0 where rating is not present
        bikemerged['rating'] = bikemerged['rating'].fillna(0)
        #Convert datatype of rating to int
        bikemerged = bikemerged.astype({'rating': 'int64'})
        #Fetch records where user rating for item is 2
        bike_high = bikemerged.loc[bikemerged['rating'] == 2]
        if not bike_high.empty: 
            #If no user rating is present, randomly sample a record
            selection = bike_high.sample(1)
        else:
            bikemerged = bike
            #Fill 0 where user rating is not present
            bikemerged['rating'] = 0
        #Change dtype of rating to int
            bikemerged = bikemerged.astype({'rating': 'int64'})
            bike_high = bikemerged
        #Randomly sample a record
            selection = bike_high.sample(1)
        #Check if filtered data returned empty
        if selection.empty:
            record = bike.sample(1)
        else:
            #Calculate nearest distance with the liked record of the user
            lon, lat = selection['longitude'], selection['latitude'] 
            bikemerged['haversine_calc'] = [haversine(lon,lat, bikemerged['longitude'][i], bikemerged['latitude'][i])for i in range(len(bike))]
            bikemerged = bikemerged[bikemerged["haversine_calc"]>0]
    #         bikemerged = bikemerged.drop(['Unnamed: 0'], axis = 1)
            #Merge outdoor activities with bicycle
            record = bikemerged.loc[bikemerged.haversine_calc == bikemerged.haversine_calc.min()]
            record = record.drop(['haversine_calc'], axis = 1)

        output = pd.concat([df_elements, record])
    else:
        #If cycling is not a user preference, no element of cycling will be added
        output = df_elements

    # INDOOR ACTIVITY
    indoor = pd.read_sql('''select * from indoor''', conn)

    if not user.empty:
        #If user rating is present
        indoor = pd.merge(indoor, user, on = 'id', how = 'left')
        indoor['rating'] = indoor['rating'].fillna(0)
        indoor = indoor.astype({'rating': 'int64'})
    else:
        indoor['rating'] = 0

    if 'Cardio' in pref:
        # If cardio is in user preference, only take high intensity theme data
        indoor_act = indoor.loc[indoor['theme'] == 'High Intensity']
        #Randomly take 3 indoor activities
        indoor_act = indoor_act.sample(3)

    else:
        #If cardio is not in user preference, only take low intensity theme
        indoor_act = indoor.loc[indoor['theme'] == 'Low Intensity']
        #Randomly take 3 indoor activities
        indoor_act = indoor_act.sample(3)

    if weather == 'Rain':
        #Reduce number of rows if weather is rain
        indoor_act = indoor_act.sample(3)
        print(indoor_act)
    else:
        #if not raining, take rows as 3
        indoor_act = indoor_act.sample(3)
    #Randomly sample 4 rows from the final number of rows collected through each type of activity
    output_final = pd.concat([output, indoor_act]).sample(4)

    out = output_final.to_json(orient='index')    
    # print(out)

#     conn.close()
    return out




#Route for populating single cards 
@app.route("/crosscard", methods = ['PUT'])
def crosscard():
        #Parse json data object in the API call
    incoming_args = reqparse.RequestParser()
    incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
    args = incoming_args.parse_args()
    #Fetch user id from the parsed json object
    user_id = args['web_id']
    #Fetch weather data for Melbourne CBD
    url = "https://api.openweathermap.org/data/2.5/weather?lat=-37.840935&lon=144.946457&appid=c92389d6904463e3cb24208905434fd9"
    response = requests.get(url)
    json = response.json()
    #Access weather from the json object
    weather = json['weather'][0]['main']
    # user_id = 4321
    ## DATA
    data = pd.read_sql('''select * from outdoor''', conn)
    # data= data.drop(['Rating'], axis = 1)
    # data = data.astype({'Rating': 'int64'})

    ## User RATING Dummy Data
    # id = [1011, 1074, 1273, 1180, 2002]
    # Rating = [2,2, 1, 1, 2]
    # user = pd.DataFrame()
    # user["id"] = id
    # user["Rating"] = Rating
    # User Rating
    sql_query = 'select * from user_rating where web_id = "{}"'.format(user_id)
    user = pd.read_sql(sql_query, conn)
    #Make column name consistent with logic
    user = user.rename(columns={"iid": "id"})
    # User Preference
    sql_query = 'select * from user_preference where web_id = "{}"'.format(user_id)
    pref = pd.read_sql(sql_query, conn)
    pref = pref['preference'][0]
    print(pref)
    #Filter data according to user preference and set the number of output for Outdoor activities
    if 'Cycling' in pref:
        if weather == 'Rain':
            n = 3
        else:
            n = 2
    else:
        if weather == 'Rain':
            n = 3
        else:
            n = 4
    #Create temp of the data
    temp = data
    #User Ratings without the userid so it can be joint with activity data
    user = user.drop(['web_id'], axis = 1)
     #Check if there are user ratings for any item id
    if not user.empty:
        #Perform left join of user ratings on activity data
        merged = pd.merge(temp, user, on = 'id', how = 'left')
        #Fill empty ratings for all items as 0
        merged['rating'] = merged['rating'].fillna(0)
        merged = merged.astype({'rating': 'int64'})
    else:
        #If no user rating is present
        merged = temp
        #Fill all item rating as 0
        merged['rating'] = 0
        # merged['Rating'] = merged['Rating'].fillna(0)
        #Change data type of Rating to Int
        merged = merged.astype({'rating': 'int64'})
    #Create new dataframes to filter different preference choice
    temp1 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    temp2 = pd.DataFrame(columns = ["id", "title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    temp3 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","rating"])
    #Check for different preferences and create boolean data
    if 'Walking' in pref:
        temp1 = merged[merged.walking != False]
    if 'Cardio' in pref:
        temp2 = merged[merged.cardio != False]
    if 'Sightseeing' in pref:
        temp3 = merged[merged.sightseeing != False]


    # merging data as rows are reduced
    concat = pd.concat([temp1, temp2, temp3])
    #Check if no preference, use outdoor data as it is, data remains unfiltered
    if concat.empty:
        concat = temp

    from sklearn.naive_bayes import GaussianNB
    #Check if 50 user ratings are present for a user
    if len(concat[(concat['rating'] != 0)]) < 50:
        #If user rating count is less than 50, take random data
        df_elements = concat.sample(n)
    else:
        #If more than 50 user ratings is present for a user
        #Convert columns to category type for modelling
        concat["theme"] = concat["theme"].astype('category')
        #Create dict for category to their respective codes mapping
        d1 = dict(enumerate(concat['theme'].cat.categories))
        #Convert columns to category type for modelling
        concat["sub_theme"] = concat["sub_theme"].astype('category')
        #Create dict for category to their respective codes mapping
        d2 = dict(enumerate(concat['sub_theme'].cat.categories))
        #Change column values to category codes
        concat["theme"] = concat["theme"].cat.codes
        concat["sub_theme"] = concat["sub_theme"].cat.codes
        
        #Machine learning model to predict activities for user
        #train set of items with rating 1 or 2
        train = concat.loc[concat['rating'] != 0]
        #test set of items with rating 0
        test = concat.loc[concat['rating'] == 0]
        #Features for training
        x_train = train.loc[:, ~train.columns.isin(['rating', 'title'])]
        #Label set (rating)
        y_train = train['rating']
        #Features for testing
        x_test = test.loc[:, ~test.columns.isin(['rating', 'title'])]
        #Label set (rating)
        y_test = test['rating']
        from sklearn.naive_bayes import GaussianNB
        #Define Gaussian Naive Bayes model
        gnb = GaussianNB()
        #Fit model on training set
        gnb.fit(x_train, y_train)
        #Make predictions on testing set (without labels)
        y_pred = gnb.predict(x_test)
        #Merging label column back to dataframes
        train['rating'] = y_train
        test['rating'] = y_pred
        #Merge train and test data
        pred = pd.concat([train, test])
        #Fetch items with rating as 2
        pred = pred.loc[pred['rating'] == 2]
        #Map category codes to actual field value in Theme and SubTheme
        pred['theme'] = pred['theme'].map(d1)
        pred['sub_theme'] = pred['sub_theme'].map(d2)
        #Sample the n number of rows from pred
        df_elements = pred.sample(n)
    #Remove preference boolean columns 
    df_elements = df_elements.drop(['walking', 'cardio', 'sightseeing', 'green_space'], axis = 1)
    # print(df_elements)

    from math import radians, cos, sin, asin, sqrt
    # HAVERSINE DISTANCE CALCULATION
    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

            # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r
    # If cycling is in user preference
    if 'Cycling' in pref:
        #Fetch data for cycling from database
        bike = pd.read_sql('''select * from bicycle''', conn)
        #Leave original data unchnaged
        temp = bike

    #     if not user.empty:
        #Perform left join of bicycle data on user ratings
        bikemerged = pd.merge(temp, user, on = 'id', how = 'left')
        #Fill 0 where rating is not present
        bikemerged['rating'] = bikemerged['rating'].fillna(0)
        #Convert datatype of rating to int
        bikemerged = bikemerged.astype({'rating': 'int64'})
        #Fetch records where user rating for item is 2
        bike_high = bikemerged.loc[bikemerged['rating'] == 2]
        if not bike_high.empty:    
                #If no user rating is present, randomly sample a record
            selection = bike_high.sample(1)
        else:
            bikemerged = bike
        #Fill 0 where user rating is not present
            bikemerged['rating'] = 0
                #Change dtype of rating to int
            bikemerged = bikemerged.astype({'rating': 'int64'})
            bike_high = bikemerged
            #Randomly sample a record
            selection = bike_high.sample(1)
        #Check if filtered data returned empty
        if selection.empty:
            record = bike.sample(1)
        else:
            #Calculate nearest distance with the liked record of the user
            lon, lat = selection['longitude'], selection['latitude'] 
            bikemerged['haversine_calc'] = [haversine(lon,lat, bikemerged['longitude'][i], bikemerged['latitude'][i])for i in range(len(bike))]
            bikemerged = bikemerged[bikemerged["haversine_calc"]>0]
    #         bikemerged = bikemerged.drop(['Unnamed: 0'], axis = 1)
            record = bikemerged.loc[bikemerged.haversine_calc == bikemerged.haversine_calc.min()]
            record = record.drop(['haversine_calc'], axis = 1)
        #Merge outdoor activities with bicycle
        output = pd.concat([df_elements, record])
    else:
        #If cycling is not a user preference, no element of cycling will be added
        output = df_elements

    # INDOOR ACTIVITY
    indoor = pd.read_sql('''select * from indoor''', conn)

    if not user.empty:
        #If user rating is present
        indoor = pd.merge(indoor, user, on = 'id', how = 'left')
        indoor['rating'] = indoor['rating'].fillna(0)
        indoor = indoor.astype({'rating': 'int64'})
    else:
        indoor['rating'] = 0

    if 'Cardio' in pref:
        # If cardio is in user preference, only take high intensity theme data
        indoor_act = indoor.loc[indoor['theme'] == 'High Intensity']
        #Randomly take 3 indoor activities
        indoor_act = indoor_act.sample(3)

    else:
        #If cardio is not in user preference, only take low intensity theme
        indoor_act = indoor.loc[indoor['theme'] == 'Low Intensity']
        #Randomly take 3 indoor activities
        indoor_act = indoor_act.sample(3)

    if weather == 'Rain':
        #Reduce number of rows if weather is rain
        indoor_act = indoor_act.sample(3)
        print(indoor_act)
    else:
        #if not raining, take rows as 3
        indoor_act = indoor_act.sample(2)
    #Randomly sample 1 row from the final number of rows collected through each type of activity
    output_final = pd.concat([output, indoor_act]).sample(1)

    out = output_final.to_json(orient='index')    
    # print(out)
#     conn.close()

    return out





@app.route("/trial", methods = ['GET'])
def hello():
    return {"Hello": "Hello world says hi!"}

if __name__ == "__main__":
    app.run(debug=True)


# return Response(df.to_json(orient="records"), mimetype='application/json')
