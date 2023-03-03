from app import flaskapp, db
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import login
from hashlib import md5
import jwt
from time import time

first_post_default = datetime.utcnow() - timedelta(days=15000)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    visits = db.relationship('Visits', backref='visitor', lazy='dynamic')
    flagged = db.Column(db.Integer, default=0)
    last_post_time = db.Column(db.DateTime, default=first_post_default)
    spammy = db.Column(db.Integer, default=0, nullable=False)
    admin_privilege = db.Column(db.Boolean, default=False)

    #upvoted_posts = db.relationship('Post', backref="liked", lazy='dynamic')
    #downvoted_posts = db.relationship('Post', backref="disliked", lazy='dynamic')
    #orcid_id = db.Column(db.String(16), unique=True)
    #comments = db.relationship('Comment', backref='author', lazy='dynamic')

    # For spam filtering

    def __repr__(self):
        return ('<User: {}>'.format(self.name))

    def set_password(self, passwd):
        self.password_hash = generate_password_hash(passwd)

    def check_password(self, passwd):
        return (check_password_hash(self.password_hash, passwd))

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def gravatar(self):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/{}'.format(digest)

    def reset_password_token(self, expiry=600):
        return jwt.encode({
            'reset_password': self.id,
            'exp': time() + expiry
        },
                          flaskapp.config['SECRET_KEY'],
                          algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_password_token(token):
        try:
            id = jwt.decode(token,
                            flaskapp.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), index=True, unique=True, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, unique=True)
    # Which folder in AWS it is kept
    folder = db.Column(db.String(20), unique=True)
    # File Name of paper's PDF in that AWS folder
    filename = db.Column(db.String(20))
    # File Name of paper's banner image in that AWS folder, same as paper PDF
    img_file = db.Column(db.String(20))
    journal = db.Column(db.String(120))
    fragments = db.relationship('Fragment', backref='paper', lazy=True)
    views = db.Column(db.Integer, default=0, nullable=False)
    timestamp_created = db.Column(db.DateTime,
                                  index=True,
                                  default=datetime.utcnow)
    # Link to the paper's project (arxiv or Google scholar etc)
    scholar_link = db.Column(db.String(150))
    # String capturing names of authors
    author_string = db.Column(db.String(150))
    publish_month = db.Column(db.Integer)
    publish_year = db.Column(db.Integer)
    published = db.Column(db.Boolean, default=0)

    #category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    ## Add MONTH-YYYY of original publication

    def __repr__(self):
        return ('<Paper: id: {}, title: {}, folder: {}'.format(
            self.id, self.title, self.folder))

    def img_url(self):
        return ("https://closed-papers.s3.ca-central-1.amazonaws.com/" +
                self.folder + "/" + self.img_file)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)


class Fragment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    # should location be unique?
    folder = db.Column(db.String(20))
    file_name = db.Column(db.String(8))
    posts = db.relationship('Post', backref='fragment', lazy=True)

    # How many people have asked for an explanation

    def location(self):
        return ("https://paper-fragments.s3-us-west-1.amazonaws.com/" +
                self.folder + "/" + self.file_name)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp_created = db.Column(db.DateTime,
                                  index=True,
                                  default=datetime.utcnow)
    timestamp_latest = db.Column(db.DateTime, index=True)
    helpful = db.Column(db.Integer, default=0)
    #accurate = db.Column(db.Integer, default=0)
    # Making the user_id nullable, so that anonymity choices can be enforced???
    ## The fact that 'user.id' is lowercase, is an unfortunate inconsistency
    ## in Flask. Uppercase model names are automatically converted by SQLAlchemy.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    fragment_id = db.Column(db.Integer,
                            db.ForeignKey('fragment.id'),
                            nullable=False)

    #paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'))

    def __repr__(self):
        return ('<Post: {}'.format(self.body))


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    upvotes = db.Column(db.Integer)
    downvotes = db.Column(db.Integer)
    # Making the user_id nullable, so that anonymity choices can be enforced???
    ## The fact that 'user.id' is lowercase, is an unfortunate inconsistency
    ## in Flask. Uppercase model names are automatically converted by SQLAlchemy.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)

    def __repr__(self):
        return ('<Comment: {}'.format(self.body))


class Visits(db.Model):
    # Mainly captures when the visitor logs in
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


fragment_requests = db.Table(
    'explain_requests',
    db.Column('user_id',
              db.Integer,
              db.ForeignKey('user.id'),
              primary_key=True),
    db.Column('fragment_id',
              db.Integer,
              db.ForeignKey('fragment.id'),
              primary_key=True))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
