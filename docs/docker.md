## Using Docker

To use the Django Base Site with Docker you first need to [install docker](https://docs.docker.com/engine/installation/)
and then follow the Quickstart guide in the project [README](https://github.com/epicserve/django-base-site).

## Debugging

### PyCharm

- Follow [Jetbrain's guide](https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html).
- Make sure you pull up the site using http://localhost:8000/ instead of http://127.0.0.1:8000/.

### Running Webpack

- When you run `docker-compose up` it starts the node service which should run webpack --watch.
- If you want to run webpack by itself, you can run it with a command like, `docker-compose run --rm node npm run (build|watch)`.


## Common Gotchas

- You need to start your runserver using `docker-compose up` instead of
  `docker-compose run web python manage.py runserver 0.0.0.0:8000` or you
  won't be able to access your site from your browser.
- Installing `django-debug-toolbar` can ignore the Django version you've
  specified in your `Pipfile` and instead Django 2 because django-debug-toolbar
  uses "Django" with a capital D in it's requirements when other packages use
  "django" in lowercase. To work around this install everything except
  `django-debug-toolbar` and then added it last to your `Pipfile`.


## Common Commands

| Command               | Description                                                                                        |
|-----------------------| -------------------------------------------------------------------------------------------------- |
| `docker-compose up`   | Starts up all of your services according to how they were defined in your docker-compose.yml file. |
| `docker-compose down` | Stops containers and removes containers, networks, volumes, and images created by `up`.            |
| `docker volume ls`    | List the volumes that have been created                                                            |


## References
- [A Brief Intro to Docker for Djangonauts](https://www.revsys.com/tidbits/brief-intro-docker-djangonauts/)
