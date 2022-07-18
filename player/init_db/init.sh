# very first steps (no db is existing yet)
# initialize db

python manage.py migrate
python manage.py createsuperuser

#probably not necessary after adding migrations/__init__.py
#python manage.py makemigrations player
#python manage.py migrate player
#python manage.py makemigrations player
