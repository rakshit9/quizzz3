import pyodbc
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import time
import redis
import hashlib
import os
import pickle


app = Flask(__name__)
app.config['SECRET_KEY'] = 'SecureSecretKey'
print(os.environ.get('PYTHONPATH'))



def connection():
    try:
        # Connect to your Azure SQL database
        server = 'ccdb24db.database.windows.net'
        username = 'rakshit'
        password = 'Canada@90'
        database = 'firstdatabase'
        driver = '{ODBC Driver 18 for SQL Server}'
        conn = pyodbc.connect(
            'DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
        return conn
    except Exception as e:
        print(e)

def redisconnection():
    try:
        redis_password = os.getenv('REDIS_PASSWORD')
        r = redis.StrictRedis(
            host='rakshit.redis.cache.windows.net',
            port=6380,
            password=redis_password,  # Reference the password via environment variable --
            ssl=True
        )
        return r
    except Exception as e:
        print(e)

@app.route('/', methods=['GET', 'POST'])
def main():
    try:
        conn = connection()
        cursor = conn.cursor()
        msg = "Database Connected Successfully"
        return render_template('index.html', error=msg)
    except Exception as e:
        return render_template('index.html', error=e)


class Form1(FlaskForm):
    number = StringField(label='No. of Query Execution: ', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


@app.route('/form1', methods=['GET', 'POST'])
def form1():
    try:
        form = Form1()
        if form.validate_on_submit():
            conn = connection()
            cursor = conn.cursor()
            r = redisconnection()
            number = int(form.number.data)

            if number < 1 or number > 1000:
                return render_template('form1.html', form=form, error='No. of Queries must be between 1 and 1000')

            query = 'SELECT time from EarthquakeData'
            key = hashlib.sha224(query.encode()).hexdigest()

            # Check if data is in Redis
            rows = r.get(key)

            # If not, get data from DB and store in Redis
            if not rows:
                cursor.execute(query)
                rows = cursor.fetchall()
                # Convert row objects to list of dictionaries
                rows = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                # We're storing the entire result set as a serialized string
                r.set(key, pickle.dumps(rows))

            diff1 = 0
            for i in range(number):
                # timing DB query
                start1 = time.time()
                cursor.execute(query)
                cursor.fetchall()
                diff1 += time.time() - start1

            # timing Redis query
            start2 = time.time()
            # Deserialize the string back into Python object
            rows = pickle.loads(r.get(key))
            diff2 = time.time() - start2

            return render_template('form1.html', form=form, number=number, diff1=diff1, diff2=diff2, data=1)

        return render_template('form1.html', form=form)

    except Exception as e:
        print(e)
        return render_template('form1.html', form=form, error=f'Error: {e}')




class Form2(FlaskForm):
    number = StringField(label='No. of Query Execution: ', validators=[DataRequired()])
    magnitude1 = StringField(label='Lower Magnitude Range: ', validators=[DataRequired()])
    magnitude2 = StringField(label='Upper Magnitude Range: ', validators=[DataRequired()])
    submit = SubmitField(label='Submit')


@app.route('/form2', methods=['GET', 'POST'])
def form2():
    try:
        form = Form2()
        if form.validate_on_submit():
            conn = connection()
            cursor = conn.cursor()
            r = redisconnection()
            number = int(form.number.data)
            magnitude1 = float(form.magnitude1.data)
            magnitude2 = float(form.magnitude2.data)

            if number < 1 or number > 1000:
                return render_template('form2.html', form=form, error='No. of Queries must be between 1 and 1000')

            if magnitude1 > magnitude2:
                return render_template('form2.html', form=form, error='Lower Magnitude Range must be lower than Higher Magnitude Range')

            r.flushall()
            query = f'SELECT time from EarthquakeData where mag between {magnitude1} and {magnitude2}'
            key = hashlib.sha224(query.encode()).hexdigest()

            # Check if data is in Redis
            rows = r.get(key)

            # If not, get data from DB and store in Redis
            if not rows:
                cursor.execute(query)
                rows = cursor.fetchall()
                # Convert row objects to list of dictionaries
                rows = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                # We're storing the entire result set as a serialized string
                r.set(key, pickle.dumps(rows))

            t1 = time.time()
            for i in range(number):
                cursor.execute(query)
                cursor.fetchall()
            diff1 = time.time() - t1

            t1 = time.time()
            # Deserialize the string back into Python object
            rows = pickle.loads(r.get(key))
            diff2 = time.time() - t1

            return render_template('form2.html', form=form, number=number, magnitude1=magnitude1, magnitude2=magnitude2, diff1=diff1, diff2=diff2, data=1)

        return render_template('form2.html', form=form)

    except Exception as e:
        print(e)
        return render_template('form2.html', form=form, error=f'Error: {e}')

class TimeRangeForm(FlaskForm):
    time_start = StringField('Start Time:', validators=[DataRequired()])
    time_end = StringField('End Time:', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/time_range', methods=['GET', 'POST'])
def time_range():
    form = TimeRangeForm()
    if form.validate_on_submit():
        try:
            conn = connection()
            cursor = conn.cursor()
            time_start = int(form.time_start.data)
            time_end = int(form.time_end.data)

            # Ensure start time is less than end time
            if time_start > time_end:
                return render_template('time_range.html', form=form, error='Start Time must be less than End Time')

            query = f"SELECT id, net, time, latitude, longitude FROM data_exam WHERE time BETWEEN {time_start} AND {time_end}"
            start_time = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            query_time = time.time() - start_time

            # Convert the result into a list of dictionaries for easier access in the template
            records = [dict(zip([column[0] for column in cursor.description], row)) for row in results]

            return render_template('time_range.html', form=form, records=records, query_time=query_time)

        except Exception as e:
            print(e)
            return render_template('time_range.html', form=form, error=str(e))
        finally:
            cursor.close()
            conn.close()

    return render_template('time_range.html', form=form)

class EventForm(FlaskForm):
    time = StringField('Start Time:', validators=[DataRequired()])
    net = StringField('Network Code:', validators=[DataRequired()])
    count = StringField('Number of Events:', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/events', methods=['GET', 'POST'])
def events():
    form = EventForm()
    if form.validate_on_submit():
        try:
            conn = connection()
            cursor = conn.cursor()
            start_time = int(form.time.data)
            net_value = form.net.data
            count = int(form.count.data)

            query = """
            SELECT TOP (?) id, net, time, latitude, longitude 
            FROM data_exam 
            WHERE net = ? AND time >= ? 
            ORDER BY time ASC
            """
            start_query_time = time.time()
            cursor.execute(query, (count, net_value, start_time))
            results = cursor.fetchall()
            query_time = time.time() - start_query_time

            # Convert the result into a list of dictionaries for easier access in the template
            records = [dict(zip([column[0] for column in cursor.description], row)) for row in results]

            return render_template('events.html', form=form, records=records, query_time=query_time)

        except Exception as e:
            print(e)
            return render_template('events.html', form=form, error=str(e))
        finally:
            cursor.close()
            conn.close()

    return render_template('events.html', form=form)

class CombinedQueryForm(FlaskForm):
    time = StringField('Start Time:', validators=[DataRequired()])
    net = StringField('Network Code:', validators=[DataRequired()])
    count = StringField('Number of Events:', validators=[DataRequired()])
    repeat_count = StringField('Number of Repetitions (T):', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/combined_query', methods=['GET', 'POST'])
def combined_query():
    form = CombinedQueryForm()
    if form.validate_on_submit():
        try:
            conn = connection()
            cursor = conn.cursor()
            start_time = int(form.time.data)
            net_value = form.net.data
            count = int(form.count.data)
            repeat_count = int(form.repeat_count.data)

            query = """
            SELECT TOP (?) id, net, time, latitude, longitude 
            FROM data_exam 
            WHERE net = ? AND time >= ? 
            ORDER BY time ASC
            """

            individual_times = []
            total_time_start = time.time()
            for _ in range(repeat_count):
                start_query_time = time.time()
                cursor.execute(query, (count, net_value, start_time))
                cursor.fetchall()
                individual_query_time = time.time() - start_query_time
                individual_times.append(individual_query_time)
            total_time_end = time.time() - total_time_start

            cursor.close()
            cursor = conn.cursor()
            query1 = """
            SELECT  TOP (?) id, net, time, latitude, longitude 
            FROM data_exam 
            WHERE net = ? AND time >= ? 
            ORDER BY time ASC
            """
            start_query_time = time.time()
            cursor.execute(query, (count, net_value, start_time))
            results = cursor.fetchall()
            # Convert the result into a list of dictionaries for easier access in the template
            records = [dict(zip([column[0] for column in cursor.description], row)) for row in results]

            return render_template('combined_query.html', form=form,records=records, individual_times=individual_times, total_time=total_time_end)

        except Exception as e:
            print(e)
            return render_template('combined_query.html', form=form, error=str(e))
        finally:
            cursor.close()
            conn.close()

    return render_template('combined_query.html', form=form)

class UpdateRecordForm(FlaskForm):
    time = StringField('Time:', validators=[DataRequired()])
    latitude = StringField('Latitude:')
    longitude = StringField('Longitude:')
    depth = StringField('Depth:')
    mag = StringField('Magnitude:')
    net = StringField('Network Code:')
    submit = SubmitField('Update Record')


@app.route('/update_record', methods=['GET', 'POST'])
def update_record():
    form = UpdateRecordForm()
    if form.validate_on_submit():
        try:
            conn = connection()
            cursor = conn.cursor()

            # Check if a record exists with the given time
            cursor.execute("SELECT * FROM data_exam WHERE time = ?", (int(form.time.data),))
            record = cursor.fetchone()
            if record:
                # Build the update query based on provided form data
                updates = []
                params = []
                if form.latitude.data:
                    updates.append("latitude = ?")
                    params.append(float(form.latitude.data))
                if form.longitude.data:
                    updates.append("longitude = ?")
                    params.append(float(form.longitude.data))
                if form.depth.data:
                    updates.append("depth = ?")
                    params.append(float(form.depth.data))
                if form.mag.data:
                    updates.append("mag = ?")
                    params.append(float(form.mag.data))
                if form.net.data:
                    updates.append("net = ?")
                    params.append(form.net.data)

                if updates:
                    params.append(int(form.time.data))
                    update_query = f"UPDATE data_exam SET {', '.join(updates)} WHERE time = ?"
                    cursor.execute(update_query, params)
                    conn.commit()
                    message = "Record updated successfully."
                else:
                    message = "No updates performed."
            else:
                message = "No record found for the given time."

            return render_template('update_record.html', form=form, message=message)

        except Exception as e:
            return render_template('update_record.html', form=form, error=str(e))
        finally:
            cursor.close()
            conn.close()

    return render_template('update_record.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)