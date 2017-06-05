from functools import wraps
from django.shortcuts import redirect
from custom_auth.models import TipoutUser

def demo_expire(session_key):
	def decorator(func):
		@wraps(func)
		def inner(request, *args, **kwargs):
			demo_alive = request.session.get(session_key)
			if not demo_alive:
				u = TipoutUser.objects.get(email=request.user)
				u.delete()
				return redirect('/demo/expired/')
			return func(request, *args, **kwargs)
		return inner
	return decorator