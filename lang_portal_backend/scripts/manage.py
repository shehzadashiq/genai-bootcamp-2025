from invoke import task

@task
def runserver(ctx):
    """Run the development server"""
    ctx.run("python manage.py runserver 8080")

@task
def migrate(ctx):
    """Run database migrations"""
    ctx.run("python manage.py makemigrations")
    ctx.run("python manage.py migrate")

@task
def shell(ctx):
    """Open Django shell"""
    ctx.run("python manage.py shell")
