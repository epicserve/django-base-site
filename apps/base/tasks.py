from celery import shared_task


@shared_task
def add(x, y):
    # Example task that can be removed
    print(x + y)
