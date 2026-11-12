from django.core.wsgi import get_wsgi_application

from garimpei.config.env import configure_django

configure_django()
application = get_wsgi_application()
