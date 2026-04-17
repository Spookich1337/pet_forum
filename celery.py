from celery import Celery

BROKER_URL="amqp://guest:guest@rabbitmq:5672//"

celery_app = Celery("post_tasks",broker=BROKER_URL,backend="rpc://")

@celery_app.task
def new_post_notification():
    import time
    import random
    time.sleep(random.randint(2, 5))
    print("hello world")
    return True