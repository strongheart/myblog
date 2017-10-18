#coding:utf8

from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app, request
from . import login_manager
from . import db
import hashlib
from datetime import datetime

class Permission:
	FOLLOW = 0x01
	COMMENT = 0x02
	WRITE_ARTICLE = 0x04
	MODERATE_COMMENTS = 0x08
	ADMINISTRATOR = 0x80
class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(64), unique = True)
	default = db.Column(db.Boolean, default = False, index = True)
	permission = db.Column(db.Integer)
	users = db.relationship('User', backref = 'role', lazy = 'dynamic')

	def __repr__(self):
		return '<Role %r>' % self.name

	@staticmethod
	def insert_roles():
		roles = {
			'User':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLE, True),
			'Moderator':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLE | Permission.MODERATE_COMMENTS, False),
			'Administrator':(0xff, False),
		}
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.permission = roles[r][0]
			role.default = roles[r][1]
			db.session.add(role)
		db.session.commit()

class User(UserMixin, db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(64), unique = True, index = True)
	email = db.Column(db.String(64), unique = True, index = True)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default = False)
	name = db.Column(db.String(64))
	about_me = db.Column(db.Text())
	location = db.Column(db.String(64))
	member_since = db.Column(db.DateTime(), default = datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default = datetime.utcnow)
	avatar_hash = db.Column(db.String(32))

	def __repr__(self):
		return '<User %r>' % self.username

	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		if self.role is None:
			if self.email == current_app.config['FLASKY_ADMIN']:
				self.role = Role.query.filter_by(permission=0xff).first()
			if self.role is None:
				self.role = Role.query.filter_by(default=True).first()
		if self.email is not None and self.avatar_hash is None:
			self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

	def change_email(self, email):
		if email is None:
			return False
		self.email = email
		self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
		db.session.add(self)
		return True
	@property
	def password(self):
		raise AttributeError('password is not readable!')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	# 生成token
	def generate_confirmation_token(self, expiration = 3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm':self.id})

	# 验证token
	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		return True

	def can(self, permission):
		return self.role is not None \
			and (self.role.permission & permission) == permission

	def is_administrator(self):
		return self.can(Permission.ADMINISTRATOR)

	#刷新用户最后访问时间
	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)

	# 生成头像
	def gravatar(self, size = 100, default = 'identicon', rating = 'g'):
		if request.is_secure:
			url = 'http://secure.gravatar.com/avatar'
		else:
			url = 'http://www.gravatar.com/avatar'
		hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
		return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(url = url, hash = hash, size = size, default =
			default, rating = rating)
class AnonymousUser(AnonymousUserMixin):
	def can(self, permission):
		return False

	def is_administrator(self):
		return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))