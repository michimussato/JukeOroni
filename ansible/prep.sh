sudo apt install libpq-dev
pip install python3-psycopg2

# Activate venv and chdir
source /data/venv/bin/activate
cd /data/django/jukeoroni

python manage.py makemigrations
python manage.py makemigrations player
python manage.py migrate
python manage.py createsuperuser

# write initial radio channels
python manage.py shell
# >>> from player.init_db.manual_db_routines import remove_channels
# >>> remove_channels()
# >>> from player.init_db.manual_db_routines import channels_write_table
# >>> channels_write_table()