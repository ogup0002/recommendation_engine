from flask import Flask, Response
from flask_restful import Api, Resource, reqparse
import pymysql
import pandas as pd
import requests

app = Flask(__name__)
# api = Api(app)


conn = pymysql.connect(
        user="sittofit",
        password="0AxPzbedoJFNTfPj67Pr",
        host="db.sittofit.tk",
        port=3306,
        database="sittofit",
        cursorclass = pymysql.cursors.DictCursor)
cursorObject = conn.cursor() 



# incoming_args = reqparse.RequestParser()
# incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
# incoming_args.add_argument("preference", type=str, help = "User Preferences as a list.")
# incoming_args.add_argument("rating", type=int, help = 'User rating can only be number 1 or 2.')

preferences = {}
ratings = pd.DataFrame()
# def abort_ ()

# class Preference(Resource):
#     def get(self):
#         return preferences[web_id]
@app.route("/", methods = ['PUT'])
def put():
    incoming_args = reqparse.RequestParser()
    incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
    incoming_args.add_argument("preference", type=str, help = "User Preferences as a list.")
    args = incoming_args.parse_args()
    preferences = args
    print(preferences)
    
    # cursorObject.execute('''select * from user_pref''')
    df = pd.DataFrame([preferences])
    d1 = '''INSERT INTO user_pref (web_id,pref) values (%s, %s)'''
    d2 = '''UPDATE user_pref set web_id = %s, pref = %s where web_id = %s'''

    val1 = (df["web_id"][0], df["preference"][0])
    val2 = (df['web_id'][0], df["preference"][0], df["web_id"][0])

    user_data = pd.read_sql('''select * from user_pref''', conn)
    if df['web_id'][0] in user_data['web_id'].values:
        ## UPDATE
        cursorObject.execute(d2, val2)
        conn.commit()
    else:
        cursorObject.execute(d1, val1)
        conn.commit()   
    return {'view': 'Success'}

@app.route("/rating", methods = ['PUT'])
def rating_():
    incoming_args = reqparse.RequestParser()
    incoming_args.add_argument("web_id", type=int, help = "Browser ID, only integer value accepted.")
    incoming_args.add_argument("iid", type=int, help = "Item ID, only 4 digit integer value accepted.")
    incoming_args.add_argument("rating", type=int, help = 'User rating can only be number 1 or 2.')
    args = incoming_args.parse_args()
    ratings = args
    print(ratings)

    df = pd.DataFrame([ratings])
    print(df)
    d1 = '''INSERT INTO user_rating (web_id, iid, rating) values (%s, %s, %s)'''
    d2 = '''UPDATE user_rating set web_id = %s, iid = %s, rating = %s where (web_id = %s and iid = %s)'''

    val1 = (df["web_id"][0], df["iid"][0], df['rating'][0])
    val2 = (df['web_id'][0], df["iid"][0], df["rating"][0], df['web_id'][0], df["iid"][0])

    user_rating = pd.read_sql('''select * from user_rating''', conn)
    comp1 = [df['web_id'][0], df['iid'][0]]
    comp2 = [user_rating['web_id'].values, user_rating['iid'].values]
    if comp1 == comp2:
        ## UPDATE
        cursorObject.execute(d2, val2)
        conn.commit()
    else:
        cursorObject.execute(d1, val1)
        conn.commit()
    return {'view': 'You have arrived here'} 

@app.route("/cards", methods = ['GET'])
def cards():
    url = "https://api.openweathermap.org/data/2.5/weather?lat=-37.840935&lon=144.946457&appid=c92389d6904463e3cb24208905434fd9"
    response = requests.get(url)
    json = response.json()
    weather = json['weather'][0]['main']

    ## DATA
    data = pd.read_csv('outdoor.csv')
    data = data.drop(['Unnamed: 0','Rating'], axis = 1)

    ## User RATING Data
    id = [1011, 1074, 1273, 1180, 2002]
    Rating = [2,2, 1, 1, 2]
    user = pd.DataFrame()
    user["id"] = id
    user["Rating"] = Rating
    #DUMMY DATA ------------ TO BE DELETED
    pref = ['Walking', 'Cardio', 'Cycling', 'Dog']
    if 'Cycling' in pref:
        if weather == 'Rain':
            n = 2
        else:
            n = 3
    else:
        if weather == 'Rain':
            n = 2
        else:
            n = 3
    temp = data
    merged = pd.merge(temp, user, on = 'id', how = 'left')
    merged['Rating'] = merged['Rating'].fillna(0)
    merged = merged.astype({'Rating': 'int64'})
    temp1 = pd.DataFrame(columns = ["Title", "Theme","Sub Theme","Latitude","Longitude","Green Space","id","Walking","Cardio","Sightseeing","Rating", "Content"])
    temp2 = pd.DataFrame(columns = ["Title", "Theme","Sub Theme","Latitude","Longitude","Green Space","id","Walking","Cardio","Sightseeing","Rating", "Content"])
    temp3 = pd.DataFrame(columns = ["Title", "Theme","Sub Theme","Latitude","Longitude","Green Space","id","Walking","Cardio","Sightseeing","Rating", "Content"])
    if 'Walking' in pref:
        temp1 = merged[merged.Walking != False]
    if 'Cardio' in pref:
        temp2 = merged[merged.Cardio != False]
    if 'Sightseeing' in pref:
        temp3 = merged[merged.Sightseeing != False]
    # merging data as rows are reduced
    concat = pd.concat([temp1, temp2, temp3])
    if concat.empty:
        concat = temp

    from sklearn.naive_bayes import GaussianNB
    if len(concat[(concat['Rating'] != 0)]) < 50:
        df_elements = concat.sample(n)
    else:
    #     len(concat[(concat['Rating'] != 0)]) > 50
    #     train, test = train_test_split(concat, test_size = 0.2)
        concat["Theme"] = concat["Theme"].astype('category')
        d1 = dict(enumerate(concat['Theme'].cat.categories))
        concat["Sub Theme"] = concat["Sub Theme"].astype('category')
        d2 = dict(enumerate(concat['Sub Theme'].cat.categories))
        concat["Theme"] = concat["Theme"].cat.codes
        concat["Sub Theme"] = concat["Sub Theme"].cat.codes

        train = concat.loc[concat['Rating'] != 0]
        test = concat.loc[concat['Rating'] == 0]
        x_train = train.loc[:, ~train.columns.isin(['Rating', 'Title'])]
        y_train = train['Rating']
        x_test = test.loc[:, ~test.columns.isin(['Rating', 'Title'])]
        y_test = test['Rating']
        from sklearn.naive_bayes import GaussianNB
        gnb = GaussianNB()
        gnb.fit(x_train, y_train)
        y_pred = gnb.predict(x_test)
        train['Rating'] = y_train
        test['Rating'] = y_pred

        pred = pd.concat([train, test])
        pred = pred.loc[pred['Rating'] == 2]
        pred['Theme'] = pred['Theme'].map(d1)
        pred['Sub Theme'] = pred['Sub Theme'].map(d2)
        df_elements = pred.sample(n)
    df_elements = df_elements.drop(['Walking', 'Cardio', 'Sightseeing', 'Green Space'], axis = 1)

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
        bike = pd.read_csv('bicycle.csv')
        bike.drop(['Unnamed: 0'], axis = 1)
    #     bike['Rating'] = 0
        
        temp = bike
        bikemerged = pd.merge(temp, user, on = 'id', how = 'left')
        bikemerged['Rating'] = bikemerged['Rating'].fillna(0)
        bikemerged = bikemerged.astype({'Rating': 'int64'})
        bike_high = bikemerged.loc[bikemerged['Rating'] == 2]
        selection = bike_high.sample(1)
        if selection.empty:
            record = bike.sample(1)
        else:
            lon, lat = selection['Longitude'], selection['Latitude'] 
            bikemerged['haversine_calc'] = [haversine(lon,lat, bikemerged['Longitude'][i], bikemerged['Latitude'][i])for i in range(len(bike))]
            bikemerged = bikemerged[bikemerged["haversine_calc"]>0]
            bikemerged = bikemerged.drop(['Unnamed: 0'], axis = 1)
            record = bikemerged.loc[bikemerged.haversine_calc == bikemerged.haversine_calc.min()]
            record = record.drop(['haversine_calc'], axis = 1)

    output = pd.concat([df_elements, record])

    # INDOOR ACTIVITY
    indoor = pd.DataFrame()
    Title = ['Yoga', 'Skipping a rope', 'Body Weight Training', 'Stretching', 'Taking the stairs', 'Dancing', 'Hula Hoop', 'Pilates']
    Theme = ['Low Intensity', 'High Intensity', 'Low Intensity', 'Low Intensity', 'High Intensity', 'High Intensity', 'High Intensity', 'Low Intensity']
    SubTheme = ['Meditation', 'Endurance Training', 'Muscle Building', 'Muscle Building', 'Endurance Training', 'Endurance Training', 'Endurance Training', 'Meditation']
    id = [3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008]
    indoor['Title'] = Title
    indoor['Theme'] = Theme
    indoor['Sub Theme'] = SubTheme
    indoor['id'] = id

    indoor = pd.merge(indoor, user, on = 'id', how = 'left')
    indoor['Rating'] = indoor['Rating'].fillna(0)
    indoor = indoor.astype({'Rating': 'int64'})


    if 'Cardio' in pref:
        indoor_act = indoor.loc[indoor['Theme'] == 'High Intensity']
        indoor_act = indoor_act.sample(3)
    else:
        indoor_act = indoor.loc[indoor['Theme'] == 'Low Intensity']
        indoor_act = indoor_act.sample(3)
        
    if weather == 'Rain':
        indoor_act = indoor_act.sample(3)
    else:
        indoor_act = indoor_act.sample(2)

    output_final = pd.concat([output, indoor_act]).sample(6)

    out = output_final.to_json(orient='index')    
    # print(out)


    return out

@app.route("/trial", methods = ['GET'])
def hello():
    return {"Hello": "Hello world says hi!"}

if __name__ == "__main__":
    app.run()


# return Response(df.to_json(orient="records"), mimetype='application/json')
