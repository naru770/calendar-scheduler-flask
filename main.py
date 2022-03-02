from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from datetime import datetime, timedelta, timezone
import os

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///scs.db'

if not 'postgresql' in db_uri:
    db_uri = db_uri.replace('postgres', 'postgresql', 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
db = SQLAlchemy(app)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False)
    person_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String(128), nullable=False)

JST = timezone(timedelta(hours=+9), 'JST')


def get_first_square_of_calendar(cal_date: datetime) -> datetime:
    first = datetime(cal_date.year, cal_date.month, 1)
    return first - timedelta(days=(first.weekday() + 1) % 7)


@app.route("/", methods=["GET"])
def home():
    ret_url = datetime.now(JST).strftime("/%Y/%m")
    return redirect(ret_url)


@app.route("/<year>/<month>", methods=["GET"])
def calendar(year, month):

    if request.method == "GET":

        this_month = datetime(int(year), int(month), 1)
        fisrt_day = get_first_square_of_calendar(this_month)
        cal_date = fisrt_day

        CALENDAR_HEIGHT = 6
        CALENDAR_WIDTH = 7

        calendar_rows = []

        for _ in range(CALENDAR_HEIGHT):

            calendar_row = []

            for _ in range(CALENDAR_WIDTH):
                
                events = db.session\
                    .query(Event.id, Event.person_id, Event.content)\
                    .filter(Event.date==cal_date)\
                    .all()

                calendar_row.append({"date": cal_date, "events": events})
                cal_date += timedelta(days=1)

            calendar_rows.append(calendar_row)

        week = ["日","月","火","水","木","金","土"]

        return render_template(
            "home.html",
            title = "カレンダー",
            calendar_rows = calendar_rows,
            prev_month = this_month - timedelta(days=2),
            this_month = this_month,
            next_month = this_month + timedelta(days=32),
            today = datetime.now(JST),
            week = week
        )


@app.route("/add_event/<year>/<month>/<day>", methods=["GET", "POST"])
def add_event(year, month, day):

    if request.method == "GET":

        return render_template(
            "event_add_form.html",
            title = "予定入力フォーム",
            date = datetime(int(year), int(month), int(day))
        )

    elif request.method == "POST":
        event = Event()
        event.date = datetime.strptime(request.form["date"], '%Y-%m-%d')
        event.person_id = request.form["person_id"]
        event.content = request.form["content"]
        db.session.add(event)
        db.session.commit()

        return redirect(f"/{event.date.year}/{event.date.month}")


@app.route("/update_event/<id>", methods=["GET", "POST"])
def update_event(id):

    if request.method == "GET":
        event = db.session\
            .query(Event)\
            .filter(Event.id==id)\
            .one()
            
        return render_template(
            "event_update_form.html",
            title = "予定変更フォーム",
            id = event.id,
            date = event.date,
            person_id = event.person_id,
            content = event.content
        )

    elif request.method == "POST":
        event = db.session\
            .query(Event)\
            .filter(Event.id==id)\
            .one()
        event.date = datetime.strptime(request.form["date"], '%Y-%m-%d')
        event.person_id = request.form["person_id"]
        event.content = request.form["content"]
        db.session.commit()

        return redirect(f"/{event.date.year}/{event.date.month}")

@app.route("/delete/<id>", methods=["GET"])
def delete_event(id):
    if request.method == "GET":
        
        # for redirect
        event = db.session\
            .query(Event)\
            .filter(Event.id==id)\
            .one()
        year = event.date.year
        month = event.date.month

        db.session\
            .query(Event)\
            .filter(Event.id==id)\
            .delete()
        db.session.commit()

        return redirect(f"/{year}/{month}")

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)