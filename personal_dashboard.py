
# Imports for dashboard
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go

import psycopg2
from psycopg2 import Error

# import requests
# import csv
# import json

from datetime import datetime
# from datetime import timezone
# from datetime import date

import matplotlib.pyplot as plt
import matplotlib.dates as mdates 
import pandas as pd

from peloton import PelotonWorkout


'''
The following script has been a way for me to play around with my own Peloton fitness data. My family's Peloton bicycle and my most recent download of the Peloton Digital Application
has been motivating my workouts during this period of social distancing. As a data person, I have been fascinated by the amount of data amassed, shared and available for visualization 
while working out. At any given moment, there are people across the world riding with me, running with or stretching with me. I know when a friend has a taken a new class and I know if I have beat 
my record from the previous day. How does Peloton do it? What is the data structure underlying and powering the app, the tablet, the website, the notifications? 

I must give credit to 
https://github.com/geudrik/peloton-api
https://rdrr.io/github/elliotpalmer/pelotonr/api/

where I initially discovered API endpoints. As I believe the best way to explore data is to struggle and wrangle with it myself while at the same time wanting to refamiliarize myself 
with Python, Pandas and data manipulation, I began my own script here: https://github.com/rivkahcarl/peloton-practice/blob/master/analyzePeloton.py.


From what I found, the API fields are clear, data is consistent and clear. 
There are some funny quirks which seem to be a result from Peloton's growth- starting with cycling and movement to classes of all types 
1. Nesting of data within 'ride' json field even for a "running" class, or 
2. the total_output only included for cycling classes instead of creating a more standard way to calculate total output across all types of classes)
3. 'total_leaderboard' on top level of json also often empty.

Arising from the desire to not ping the API endpoints in an efficient way, I turned to use @geudrik's library to continue to explore, document more of the fields, explain what they mean and build a dashboard to better track my workouts in the form of data. 
The following script builds a dashboard with Python's Dash.

'''

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)



connection = psycopg2.connect(user = "rivkahcarl",
             password = "",
             host = "127.0.0.1",
             port = "5432",
             database = "peloton")
cursor = connection.cursor()

load_data_query = "SELECT * FROM public.workouts"

df = pd.read_sql(load_data_query, connection)

# Convert to Pandas dataframe - TODO- It might already be in a df format
# df = pd.DataFrame(finalData)  

# Create pretty Date column
df['Date'] = df.apply(lambda row: row.created_at.date(), axis=1)

# Create length of time in minutes
df['durationMinutes'] = df['durationseconds']/60


# Task 1a: Plot Calories by Day
df2 = df.groupby("Date", as_index=False).calories.sum()

df2['Date'] = pd.to_datetime(df2.Date) #, format='%Y%m%d'
df2['DateName'] = df2.Date.apply(lambda x: x.strftime('%B %d, %Y'))

df3 = df.groupby(["Date", "fitness_discipline"], as_index=False).calories.sum()

calorieGraph = px.bar(df2, x='Date', y='calories', barmode="group", labels={'calories':'Total Calories'})
# calorieGraphByFitnessType = px.bar(df2, x='Date', y='calories', barmode="group", labels={'calories':'Total Calories'})

# Task 1a: Plot Calories by Day and Fitness type
uniquefd = df3['fitness_discipline'].unique()

# calorieGraphByFitnessType = go.Figure()

trace_data = []
for fittype in uniquefd:
	subbytype = df3[df3["fitness_discipline"] == fittype]
	trace = go.Bar(name=fittype, x=subbytype['Date'], y=subbytype['calories'])
	trace_data.append(trace)

	#calorieGraphByFitnessType.add_trace(go.Bar(name=fittype, x=subbytype['Date'], y=subbytype['calories']))

ftlayout = go.Layout(title="Calories per Day by Fitness Type", barmode="stack")

calorieGraphByFitnessType = go.Figure(trace_data, ftlayout)
# Change the bar mode
#calorieGraphByFitnessType.update_layout(barmode='stack')

# Average calories by day during Corona social distancing
df2['Month'] = df2['DateName'].str.split(" ", n=1, expand=True)[0]
df2['Year'] = df2['DateName'].str.split(" ", expand=True)[2]
average_calorie_per_day = df2['calories'].mean()

df3 = df2[(df2['Year'] == '2020') & (df2['Month'].isin(['March', 'April', 'May', 'June', 'July']))] 
average_calorie_per_day_corona = df3['calories'].mean()

# Task 2: Number of classes per instructor
df4 = df.groupby("instructorname", as_index=True).count()[['workoutid']]

# Reset index so instructorName is a column in dataframe
df4 = df4.reset_index()

df4 = df4.rename(columns={'workoutid':'CountOfClasses'})
df4 = df4.sort_values(by=['CountOfClasses'], ascending=False)

instructorGraph = px.bar(df4, x='CountOfClasses', y='instructorname', barmode="group", labels={'CountOfClasses':'Number of classes', 'instructorname':'Instructor Name'})

#ax = df4.plot(x='instructorName', y='CountOfClasses', kind='barh') #, orientation='horizontal')

# plt.show()

# Task 3a: Number of classes per day 

df5 = df.groupby("Date", as_index=False).workoutid.count()

df5['Date'] = pd.to_datetime(df5.Date) #, format='%Y%m%d'
workoutsByDateGraph = px.bar(df5, x='Date', y='workoutid', barmode="group", labels={'calories':'Total Calories', 'workoutid':'Number of Classes'})


df6 = df.groupby(["Date", "fitness_discipline"], as_index=False).workoutid.count()
df6['Date'] = pd.to_datetime(df6.Date) #, format='%Y%m%d'


# Task 3b: Number of classes per day and fitness type
uniquefd = df6['fitness_discipline'].unique()

trace_data = []
for fittype in uniquefd:
	subbytype = df6[df6["fitness_discipline"] == fittype]
	trace = go.Bar(name=fittype, x=subbytype['Date'], y=subbytype['workoutid'])
	trace_data.append(trace)

ftlayout = go.Layout(title="Number of Workouts per Day by Fitness Type", barmode="stack")

numberWorkoutsByDateFitness = go.Figure(trace_data, ftlayout)

# Task 4: Counts based on Lengths of Classes

df7 = df.groupby("durationMinutes", as_index=False).workoutid.count()
df7 = df7.rename(columns={"durationMinutes": "Length of Class (Minutes)", "workoutid": "Count of Classes"})

# Number of classes per day and length
df8 = df.groupby(["Date", "durationMinutes"], as_index=False).workoutid.count()
# df8 = df8.rename(columns={"durationMinutes": "Length of Class (Minutes)", "workoutid": "Count of Classes"})

df8["durationMinutes"] = df8.durationMinutes.apply(lambda x: str(x))
uniquelth = df8['durationMinutes'].unique()


trace_data = []
for lentype in uniquelth:
	subbytype = df8[df8["durationMinutes"] == lentype]
	trace = go.Bar(name=lentype, x=subbytype['Date'], y=subbytype['workoutid'])
	trace_data.append(trace)

ftlayout = go.Layout(title="Number of Classes per Day by Length", barmode="stack")

numberClassesByLength = go.Figure(trace_data, ftlayout)


app.layout = html.Div(children=[
    html.H1(children='Peloton Workouts: Personal Dashboard'),
    html.Div(children='''
        Aggregate Data across Peloton workouts to monitor personal progress
    '''),
    html.H3(children='Total Workouts: %s' % len(df.index)),
    html.H3(children='Average Calories Per Day Overall, %s' % average_calorie_per_day),    
    html.H3(children='Average Calories Per Day during Corona Months, %s' % average_calorie_per_day_corona),
    dcc.Graph(
        id='calorie-graph',
        figure=calorieGraph
    ),
    html.Hr(),
    dcc.Graph(
    	id='calorie-graph-fitness-type',
    	figure=calorieGraphByFitnessType
    ),
    html.Hr(),
    dcc.Graph(
    	id='count-workouts-by-date',
    	figure=workoutsByDateGraph
    ),    
    html.Hr(),
    dcc.Graph(
    	id='count-workouts-by-date-fitness-type',
    	figure=numberWorkoutsByDateFitness
    ),    
    html.Hr(),
    dcc.Graph(
    	id='instructor-graph',
    	figure=instructorGraph),
    html.Hr(),
    dash_table.DataTable(
    				id='length-table',
    				columns=[{"name": i, "id": i} for i in df7.columns],
    				data=df7.to_dict('records')
    				),
    html.Hr(),
    dcc.Graph(
    	id='classes-by-length-graph',
    	figure=numberClassesByLength),
])




if __name__ == '__main__':
    app.run_server(debug=True)


'''
#########################################
#####            Profile           ######
#########################################

# meContent = s.get('https://api.onepeloton.com/api/me').json()

###### KEY NAMES 
# [u'username', u'last_name', u'is_demo', u'weight', u'is_profile_private', u'cycling_ftp_workout_id', u'created_country', u'cycling_workout_ftp', u'height', u'is_provisional', u'cycling_ftp', u'id', 
# u'total_pending_followers', u'block_explicit', u'facebook_access_token', u'customized_max_heart_rate', u'is_strava_authenticated', u'obfuscated_email', u'hardware_settings', u'is_complete_profile', u'instructor_id', u'v1_referrals_made', 
# u'last_workout_at', u'location', u'is_internal_beta_tester', u'facebook_id', u'cycling_ftp_source', u'has_active_digital_subscription', u'email', u'phone_number', u'contract_agreements', u'middle_initial', u'quick_hits', 
# u'external_music_auth_list', u'first_name', u'card_expires_at', u'birthday', u'has_signed_waiver', u'customized_heart_rate_zones', u'referrals_made', u'is_external_beta_tester', 
# u'paired_devices', u'total_pedaling_metric_workouts', u'total_workouts', u'default_max_heart_rate', u'name', u'is_fitbit_authenticated', u'has_active_device_subscription', u'gender', 
# u'created_at', u'workout_counts', u'total_non_pedaling_metric_workouts', u'member_groups', u'default_heart_rate_zones', u'image_url', u'total_following', u'estimated_cycling_ftp', u'can_charge', u'total_followers']


userid = "c3ff56ef4c834f8eb682e724494e1d27" # meContent['id']

#########################################
#####            Workouts          ######
#########################################


# The workouts endpoint truncates 20 to page however the workoutsFullEndpoint passes a parameter that allows a larger limit. 
# It was easier to hack this and set a large limit (which I knew based on my application dashboard)
workoutsPagingEndpoint = 'https://api.onepeloton.com/api/user/%s/workouts' % (userid)
workoutsFullEndpoint = 'https://api.onepeloton.com/api/user/%s/workouts?joins=ride&limit=%s' % (userid, 200) #The number should be changed - but just putting in limit that I know is past the total number of workouts

workouts = s.get(workoutsFullEndpoint).json()

###### KEY NAMES 
# [u'count', u'summary', u'page_count', u'show_next', u'sort_by', u'show_previous', u'next', u'limit', u'aggregate_stats', u'total', u'data', u'page']
# Need to find way to loop through all the page count, 'page_count' shows total number of pages and 'page' is the page that you are on...

# Data of workout is found inside 'data' key
workoutData = workouts['data']

# Sample workout
# {u'workout_type': u'class', u'total_work': 0.0, u'is_total_work_personal_record': False, u'device_type': u'iPhone', u'timezone': u'America/New_York', u'device_time_created_at': 1586800817, u'id': u'8b83bece729648e0a8dc2671c66a3b66', u'fitbit_id': None, u'peloton_id': u'84360c083b714f5d93f937d4d07d2102', u'user_id': u'c3ff56ef4c834f8eb682e724494e1d27', u'title': None, u'has_leaderboard_metrics': False, u'has_pedaling_metrics': False, u'platform': u'iOS_app', u'metrics_type': None, u'fitness_discipline': u'stretching', u'status': u'COMPLETE', u'start_time': 1586815306, u'name': u'Stretching Workout', u'strava_id': None, u'created': 1586815217, u'created_at': 1586815217, u'end_time': 1586815896}
#	print workout['total_work'] -- Only cycling classes have total_work when looping through, all other data is inside the 'ride'
#	print workout['fitness_discipline']
	workoutId = workout['id']

	# Help to find specific Id's if need to test different categories
	# workout['fitness_discipline'] in ['cycling', 'running']


#########################################
#####      Specific Workout        ######
#########################################

workoutDetailEndpoint = 'https://api.onepeloton.com/api/workout/%s'

# [u'workout_type', u'total_work', u'is_total_work_personal_record', u'device_type', u'total_leaderboard_users', u'timezone', u'leaderboard_rank', u'device_time_created_at', 
# u'id', u'fitbit_id', u'peloton_id', u'user_id', u'title', u'has_leaderboard_metrics', u'has_pedaling_metrics', u'platform', u'metrics_type', u'achievement_templates', 
# u'fitness_discipline', u'status', u'device_type_display_name', u'start_time', u'name', u'strava_id', u'created', u'created_at', u'ftp_info', u'end_time', u'ride']
## Inside ride is where the data for the workout lives - Question: the data for the class changes- so is the workoutid unique and/or does the meta class data change 


#########################################
#####     Performance Graph        ######
#########################################

## Performance Graph endpoint
workoutPerformanceEndpoint = 'https://api.onepeloton.com/api/workout/%s/performance_graph' 

###### KEY NAMES 
# [u'is_class_plan_shown', u'splits_data', u'location_data', u'average_summaries', u'metrics', u'segment_list', u'duration', u'is_location_data_accurate', u'has_apple_watch_metrics', u'summaries', u'seconds_since_pedaling_start']
# workoutPerformanceDetail['average_summaries'] Example:
# [{u'display_name': u'Avg Pace', u'slug': u'avg_pace', u'value': 16.22, u'display_unit': u'min/mi'}, {u'display_name': u'Avg Speed', u'slug': u'avg_speed', u'value': 3.7, u'display_unit': u'mph'}]
# workoutPerformanceDetail['summaries'] Example
# [{u'display_name': u'Distance', u'slug': u'distance', u'value': 1.23, u'display_unit': u'mi'}, {u'display_name': u'Elevation', u'slug': u'elevation', u'value': 74, u'display_unit': u'ft'}, {u'display_name': u'Calories', u'slug': u'calories', u'value': 146, u'display_unit': u'kcal'}]


workoutInstructorEndpoint = 'https://api.onepeloton.com/api/workout/%s?joins=ride.instructor'

# "https://api.onepeloton.com/api/workout/<workout_id>?joins=ride.instructor"
# "https://api.onepeloton.com/api/workout/<workout_id>?joins=ride,ride.instructor"
# These two endpoints are identical, perhaps once joining with the ride.instructor data, the entire ride dict is included

###### KEY NAMES 
"created_at", "device_type", "end_time", "fitbit_id", "fitness_discipline", "has_pedaling_metrics", "has_leaderboard_metrics",
"id", "is_total_work_personal_record", "metrics_type", "name", "peloton_id", "platform", "start_time", "strava_id", "status",
"timezone", "title", "total_work", "user_id", "workout_type",
"ride", 
"ride.instructor", 
"ride.instructor.id",
"ride.instructor.bio",
"ride.instructor.short_bio",
"ride.instructor.coach_type",
"ride.instructor.is_filterable",
"ride.instructor.is_visible",
"ride.instructor.list_order",
"ride.instructor.featured_profile",
"ride.instructor.film_link",
"ride.instructor.facebook_fan_page",
"ride.instructor.music_bio",
"ride.instructor.spotify_playlist_uri",
"ride.instructor.background",
"ride.instructor.ordered_q_and_as",
"ride.instructor.instagram_profile",
"ride.instructor.strava_profile",
"ride.instructor.twitter_profile",
"ride.instructor.quote",
"ride.instructor.username",
"ride.instructor.name",
"ride.instructor.first_name",
"ride.instructor.last_name",
"ride.instructor.user_id",
"ride.instructor.life_style_image_url",
"ride.instructor.bike_instructor_list_display_image_url",
"ride.instructor.web_instructor_list_display_image_url",
"ride.instructor.ios_instructor_list_display_image_url",
"ride.instructor.about_image_url",
"ride.instructor.image_url",
"ride.instructor.jumbotron_url",
"ride.instructor.jumbotron_url_dark",
"ride.instructor.jumbotron_url_ios",
"ride.instructor.web_instructor_list_gif_image_url",
"ride.instructor.instructor_hero_image_url",
"ride.instructor.fitness_disciplines",
"ride.class_type_ids",
"ride.content_provider",
"ride.content_format",
"ride.description",
"ride.difficulty_estimate",
"ride.overall_estimate",
"ride.difficulty_rating_avg",
"ride.difficulty_rating_count",
"ride.difficulty_level",
"ride.duration",
"ride.equipment_ids",
"ride.equipment_tags",
"ride.extra_images",
"ride.fitness_discipline",
"ride.fitness_discipline_display_name",
"ride.has_closed_captions",
"ride.has_pedaling_metrics",
"ride.home_peloton_id",
"ride.id",
"ride.image_url",
"ride.instructor_id",
"ride.is_archived",
"ride.is_closed_caption_shown",
"ride.is_explicit",
"ride.has_free_mode",
"ride.is_live_in_studio_only",
"ride.language",
"ride.origin_locale",
"ride.length",
"ride.live_stream_id",
"ride.live_stream_url",
"ride.location",
"ride.metrics",
"ride.original_air_time",
"ride.overall_rating_avg",
"ride.overall_rating_count",
"ride.pedaling_start_offset",
"ride.pedaling_end_offset",
"ride.pedaling_duration",
"ride.rating",
"ride.ride_type_id",
"ride.ride_type_ids",
"ride.sample_vod_stream_url",
"ride.scheduled_start_time",
"ride.series_id",
"ride.sold_out",
"ride.studio_peloton_id",
"ride.title",
"ride.total_ratings",
"ride.total_in_progress_workouts",
"ride.total_workouts",
"ride.vod_stream_url",
"ride.vod_stream_id",
"ride.captions",
"ride.excluded_platforms",
"created",
"device_time_created_at",
"achievement_templates",
"leaderboard_rank",
"total_leaderboard_users",
"ftp_info",
"ftp_info.ftp",
"ftp_info.ftp_source",
"ftp_info.ftp_workout_id",
"device_type_display_name"
'''

