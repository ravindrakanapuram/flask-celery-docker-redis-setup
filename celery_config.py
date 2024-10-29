# celery_config.py
from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['result_backend']
    )
    celery.conf.update(app.config)
    celery.Task = type('FlaskTask', (celery.Task,), {
        '__call__': lambda self, *args, **kwargs: self.run(*args, **kwargs)
    })
    return celery
