#coding:utf8

from ..models import Permission
from .errors import forbidden
from functools import wraps
def permission_required(permission):
	def decorator(f):
		@wraps(f)
		def decorated_function(*args, **kwargs):
			if not g.current_user.can(permission):
				return  forbidden('没有足够的权限')
			return f(*args, **kwargs)
		return decorated_function
	return decorator