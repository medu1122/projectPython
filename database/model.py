from database.config import db
from datetime import datetime
class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(255),nullable=False)
    email=db.Column(db.String(255),nullable=False,unique=True)
    password=db.Column(db.String(255),nullable=False)
    avatar=db.Column(db.String(255),nullable=True)
    role=db.Column(db.String(255),nullable=False)
    create_at=db.Column(db.DateTime,default=datetime.now)
    is_active=db.Column(db.Boolean,default=True)