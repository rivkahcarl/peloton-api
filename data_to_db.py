import psycopg2
from psycopg2 import Error

from peloton import PelotonWorkout
import ipdb

try:
    connection = psycopg2.connect(user = "rivkahcarl",
                 password = "",
                 host = "127.0.0.1",
                 port = "5432",
                 database = "peloton")
    cursor = connection.cursor()

    create_basic_workout_table_query = '''
                                        CREATE TABLE IF NOT EXISTS workouts 
                                        (workoutId varchar PRIMARY KEY      NOT NULL
                                         , fitness_discipline varchar       NOT NULL
                                         , created_at   timestamp           NOT NULL
                                         , calories decimal                 
                                         , instructorName varchar
                                         , durationSeconds decimal          NOT NULL
                                         , distance_miles  decimal 
                                        )
                                        '''

    cursor.execute(create_basic_workout_table_query)
    connection.commit()
    print("Peloton table created if not exists successfully")

except(Exception, psycopg2.Error) as error:
    print("Error while connecting to Postgresql", error)
finally:
    # closing database connection
        if(connection):
            cursor.close()
            connection.close()
            print("Postgresql connection is closed")


try:
    connection = psycopg2.connect(user = "rivkahcarl",
                                    password = "",
                                    host = "127.0.0.1",
                                    port = "5432",
                                    database = "peloton")
    cursor = connection.cursor()

    insert_workout_data_query = '''
                                    INSERT INTO workouts (workoutId, fitness_discipline, created_at, calories, instructorName, durationSeconds, distance_miles)
                                    VALUES
                                    ( %s, %s, %s, %s, %s, %s, %s) 
                                    ON CONFLICT (workoutId) 
                                    DO NOTHING;
                                    '''


    workouts = PelotonWorkout.list()


    # Pull out subset of relevant data for dashboard
    for workout in workouts:

        if workout.fitness_discipline != 'meditation':

            # Gather Calories
            # In this library calories are found in the PelotonWorkoutMetrics object
            # Not all workouts have associated calorie measures
            if hasattr(workout.metrics, 'calories_summary'): 
                calories = workout.metrics.calories_summary.value if workout.metrics.calories_summary.slug == 'calories' else 0
            else:
                print("The following class does not have Calorie object: %s" % workout.id, workout.fitness_discipline)
                calories = 0 ## TODO - Figure out why and which class is missing calories

            # Gather distance in miles
            if hasattr(workout.metrics, 'distance_summary'):
                distance_miles = workout.metrics.distance_summary.value if workout.metrics.distance_summary.unit == 'mi' else 0
            else:
                print("The following class does not have distance in miles %s" % workout.id, workout.fitness_discipline)
                distance_miles = 0 

            # Gather Instructors names
            # Instructor name are found within 'ride.instructor.name' - not all workouts have an associated instructor
            if hasattr(workout.ride, 'instructor'):
                instructorName = workout.ride.instructor.name
            else: 
                print("Workout is missing Instructor information, Id= %s" % workout.id) 
                instructorName = None

            # Gather Duration
            if hasattr(workout.ride, 'duration'):
                durationSeconds = workout.ride.duration
            else: 
                print("Workout is missing duration information, Id= %s" % workout.id)
                durationSeconds = None
            
            record_to_insert = (workout.id, workout.fitness_discipline, workout.created_at, calories, instructorName, durationSeconds, distance_miles)
            cursor.execute(insert_workout_data_query, record_to_insert)

            connection.commit()
            count = cursor.rowcount
            print (count, "Record inserted successfully into peloton table")

        else:
            pass #Dont care for meditation classes at this point in time- mostly concerned about active fitness
            

except (Exception, psycopg2.Error) as error :
    if(connection):
        print("Failed to insert record into peloton table", error)

finally:
    #closing database connection.
    if(connection):
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")
