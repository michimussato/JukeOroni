# very first steps (no db is existing yet)
# initialize db

python manage.py migrate
python manage.py createsuperuser
python manage.py makemigrations player
python manage.py migrate player
