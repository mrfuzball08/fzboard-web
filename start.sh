#!/bin/bash

# tailwind watch in background
npm run watch &

# django server in foreground
python manage.py runserver 0.0.0.0:8000