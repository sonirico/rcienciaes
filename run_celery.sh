#!/bin/bash
( python manage.py celeryd -B -l info >> logs/celery.log ) &
# Arrancamos el programama que twittea y suma reproducciones
( python episode_checker.py >> logs/tweets.log ) &

