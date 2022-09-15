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
        database="recommendation",
        cursorclass = pymysql.cursors.DictCursor)
cursorObject = conn.cursor() 



preferences = {}
ratings = pd.DataFrame()


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

@app.route("/cards", methods = ['PUT'])
def cards():
    url = "https://api.openweathermap.org/data/2.5/weather?lat=-37.840935&lon=144.946457&appid=c92389d6904463e3cb24208905434fd9"
    response = requests.get(url)
    json = response.json()
    weather = json['weather'][0]['main']

    ## DATA
    data = pd.read_sql('''select * from outdoor''', conn)
    # data= data.drop(['Rating'], axis = 1)
    # data = data.astype({'Rating': 'int64'})

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
    
    temp1 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","Rating"])
    temp2 = pd.DataFrame(columns = ["id", "title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","Rating"])
    temp3 = pd.DataFrame(columns = ["id","title", "theme","sub_theme","latitude","longitude","green_space","walking","cardio","sightseeing","Rating"])
    if 'Walking' in pref:
        temp1 = merged[merged.walking != False]
    if 'Cardio' in pref:
        temp2 = merged[merged.cardio != False]
    if 'Sightseeing' in pref:
        temp3 = merged[merged.sightseeing != False]
    

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
        concat["theme"] = concat["theme"].astype('category')
        d1 = dict(enumerate(concat['theme'].cat.categories))
        concat["sub_theme"] = concat["sub_theme"].astype('category')
        d2 = dict(enumerate(concat['sub_theme'].cat.categories))
        concat["theme"] = concat["theme"].cat.codes
        concat["sub_theme"] = concat["sub_theme"].cat.codes

        train = concat.loc[concat['Rating'] != 0]
        test = concat.loc[concat['Rating'] == 0]
        x_train = train.loc[:, ~train.columns.isin(['Rating', 'title'])]
        y_train = train['Rating']
        x_test = test.loc[:, ~test.columns.isin(['Rating', 'title'])]
        y_test = test['Rating']
        from sklearn.naive_bayes import GaussianNB
        gnb = GaussianNB()
        gnb.fit(x_train, y_train)
        y_pred = gnb.predict(x_test)
        train['Rating'] = y_train
        test['Rating'] = y_pred

        pred = pd.concat([train, test])
        pred = pred.loc[pred['Rating'] == 2]
        pred['theme'] = pred['theme'].map(d1)
        pred['sub_theme'] = pred['sub_theme'].map(d2)
        df_elements = pred.sample(n)
    df_elements = df_elements.drop(['walking', 'cardio', 'sightseeing', 'green_space'], axis = 1)
    
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
        bike = pd.read_sql('''select * from bicycle''', conn)

        temp = bike
        bikemerged = pd.merge(temp, user, on = 'id', how = 'left')
        bikemerged['Rating'] = bikemerged['Rating'].fillna(0)
        bikemerged = bikemerged.astype({'Rating': 'int64'})
        bike_high = bikemerged.loc[bikemerged['Rating'] == 2]
        selection = bike_high.sample(1)
        if selection.empty:
            record = bike.sample(1)
        else:
            lon, lat = selection['longitude'], selection['latitude'] 
            bikemerged['haversine_calc'] = [haversine(lon,lat, bikemerged['longitude'][i], bikemerged['latitude'][i])for i in range(len(bike))]
            bikemerged = bikemerged[bikemerged["haversine_calc"]>0]
    #         bikemerged = bikemerged.drop(['Unnamed: 0'], axis = 1)
            record = bikemerged.loc[bikemerged.haversine_calc == bikemerged.haversine_calc.min()]
            record = record.drop(['haversine_calc'], axis = 1)

    output = pd.concat([df_elements, record])

    # INDOOR ACTIVITY
    indoor = pd.read_sql('''select * from indoor''', conn)

    indoor = pd.merge(indoor, user, on = 'id', how = 'left')
    indoor['Rating'] = indoor['Rating'].fillna(0)
    indoor = indoor.astype({'Rating': 'int64'})


    if 'Cardio' in pref:
        indoor_act = indoor.loc[indoor['theme'] == 'High Intensity']
        indoor_act = indoor_act.sample(3)
    else:
        indoor_act = indoor.loc[indoor['theme'] == 'Low Intensity']
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
    app.run(debug=True)


# return Response(df.to_json(orient="records"), mimetype='application/json')

