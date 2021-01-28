import time
import requests
import os
from sqlalchemy.sql import func
from sqlalchemy import and_
from gevent.pywsgi import WSGIServer
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request
from threading import Thread
from gevent import monkey
from datetime import datetime, timedelta
monkey.patch_all()


URL1 = 'http://localhost:8000'
URL2 = 'http://localhost:8001'
DATABASE = 'values.db'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+DATABASE
app.config['TEMPLATES_AUTO_RELOAD'] = True
db = SQLAlchemy(app)


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True),
                          server_default=func.now())
    entity = db.Column(db.String(20), nullable=False)
    value = db.Column(db.Float, nullable=False)


if not os.path.exists(DATABASE):
    db.create_all()


def read_and_store_values():
    global URL1
    global URL2
    global db

    urls = [URL1, URL2]
    while True:
        for url in urls:
            try:
                data = requests.get(url).json()
                for k, v in data.items():
                    db.session.add(Record(entity=k, value=v))
            except KeyboardInterrupt:
                return
            except:
                pass
            db.session.commit()
        time.sleep(60.0)


@app.route('/values')
def return_values():
    timeframe = int(request.args.get('timeframe'))
    if timeframe > 20160:
        return {}
    entity1 = request.args.get('entity1', None)
    entity2 = request.args.get('entity2', None)
    since = datetime.utcnow() - timedelta(minutes=timeframe)

    ret_values = {}
    if entity1:
        ret_values[entity1] = [{'timestamp': x.timestamp.isoformat()+'Z', 'value': x.value}
                  for x in Record.query.filter(and_(Record.entity == entity1, Record.timestamp >= since)).all()]
    if entity2:
        ret_values[entity2] = [{'timestamp': x.timestamp.isoformat()+'Z', 'value': x.value}
                  for x in Record.query.filter(and_(Record.entity == entity2, Record.timestamp >= since)).all()]
    return ret_values


@app.route('/')
def index():
    entities = [x[0]
                for x in Record.query.with_entities(Record.entity).distinct()]
    return render_template('index.html', entities=entities)


if __name__ == "__main__":
    Thread(target=read_and_store_values).start()
    server = WSGIServer(('0.0.0.0', 8002), app)
    server.serve_forever()
