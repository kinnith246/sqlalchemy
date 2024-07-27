# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Declare a Base using `automap_base()`
Base = automap_base()

# Use the Base class to reflect the database tables
Base.prepare(autoload_with = engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
#session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    return (
        "Welcome to the 'Home' page!<br/>"
        "Available Routes:<br/>"
        "/api/v1.0/precipitation<br/>"
        "/api/v1.0/stations<br/>"
        "/api/v1.0/tobs<br/>"
        "/api/v1.0/<start><br/>"
        "/api/v1.0/<start>/<end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipication():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).all()
    session.close()
    # Convert to dictionary
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query stations
    stations_data = session.query(Station.station).all()
    session.close()
    stations_list = list(np.ravel(stations_data))
    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # Find most recent date
    recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()

    # Starting from the most recent data point in the database.
    most_recent_date = dt.datetime.strptime(recent_date[0], '%Y-%m-%d')

    # Calculate the date one year from the last date in data set.
    prev_year = most_recent_date - dt.timedelta(days=365)
    prev_year = prev_year.strftime('%Y-%m-%d')
    
    # Query dates and temperature observations of the most-active station for the previous year of data
    print(f"Previous Year Date: {prev_year}")
    most_active_station = session.query(Measurement.station).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    print(f"Most Active Station: {most_active_station}")

    temperature_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= prev_year).all()
    print(f"Temperature Data: {temperature_data}")

    session.close()
    # Convert to list
    temperature_list = list(np.ravel(temperature_data))
    return jsonify(temperature_list)

@app.route("/api/v1.0/<start>")
def start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    try:
        # Convert start string to a date object
        start_date = dt.datetime.strptime(start, "%d-%m-%Y").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use DD-MM-YYYY format."}), 400
    print(f"Start Date: {start_date}")

    # Query for TMIN, TAVG, TMAX from the start date
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date).all()

    # Check the number of records returned by the query
    record_count = session.query(Measurement).filter(Measurement.date >= start_date).count()
    print(f"Number of records from {start_date}: {record_count}")

    session.close()
    
    temperature_data = list(np.ravel(results))
    print(f"Temperature Data: {temperature_data}")
    
    # Prepare the response with meaningful keys
    response = {
        "start_date": start,
        "min_temperature": temperature_data[0],
        "avg_temperature": temperature_data[1],
        "max_temperature": temperature_data[2]
    }

    return jsonify(response)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    try:
        # Convert start and end strings to date objects
        start_date = dt.datetime.strptime(start, "%d-%m-%Y").date()
        end_date = dt.datetime.strptime(end, "%d-%m-%Y").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD format."}), 400
    
    # Query for TMIN, TAVG, TMAX from the start date to the end date
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()
    
    session.close()
    
    temperature_data = list(np.ravel(results))

     # Prepare the response with meaningful keys
    response = {
        "start_date": start,
        "end_date": end,
        "min_temperature": temperature_data[0],
        "avg_temperature": temperature_data[1],
        "max_temperature": temperature_data[2]
    }

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
