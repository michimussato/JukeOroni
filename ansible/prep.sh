sudo apt install libpq-dev
pip install python3-psycopg2

# Activate venv and chdir
source /data/venv/bin/activate
cd /data/django/jukeoroni

# create super user for admin site
python manage.py createsuperuser

# set up db schema
python manage.py migrate

# write initial radio channels
python manage.py shell
# >>> from player.init_db.manual_db_routines import channels_write_table
# >>> channels_write_table()