#! /bin/bash
cd web
export FLASK_APP=potagist.py
flask --debug run
read -s -n 1 -p