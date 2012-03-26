import os

from flask import Flask, jsonify
from flaskext.sqlalchemy import SQLAlchemy
from werkzeug.http import http_date
from sqlalchemy.databases import postgres


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)


class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tid = db.Column(postgres.BIGINT)
    text = db.Column(db.String(250))
    created_at = db.Column(db.DateTime)
    synced = db.Column(db.Boolean)

    def __init__(self, tid, text, created_at):
        self.tid = tid
        self.text = text
        self.created_at = created_at
        self.synced = False

    def __repr__(self):
        return u'<Feed %r>' % self.text


class Bind(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(40))
    secret = db.Column(db.String(40))
    to = db.Column(db.String(10))

    def __init__(self, token, secret, to):
        self.token = token
        self.secret = secret
        self.to = to

    def __repr__(self):
        return u'<Bind %r>' % self.to


@app.route('/')
def home():
    feeds = Feed.query.order_by(Feed.id.desc()).all()
    return jsonify(
        count=len(feeds),
        feeds=[dict(id=f.id, tid=f.tid, text=f.text,
                    created_at=http_date(f.created_at), synced=f.synced)
               for f in feeds])


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
