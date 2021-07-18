"""
(venv) pi@jukeoroni:/data/django/jukeoroni $ python manage.py shell
"""
from radio.models import Channel


radios = [
('http://streams.radiobob.de/100/mp3-192/streams.radiobob.de/play.m3u', '100', '100'),
('http://streams.radiobob.de/101/mp3-192/streams.radiobob.de/play.m3u', '101', '101'),
('http://streams.radiobob.de/2000er/mp3-192/streams.radiobob.de/play.m3u', '2000er', '2000er'),
('http://streams.radiobob.de/blues/mp3-192/streams.radiobob.de/play.m3u', 'blues', 'blues'),
('http://streams.radiobob.de/bob-80srock/mp3-192/streams.radiobob.de/play.m3u', 'bob-80srock', 'bob-80srock'),
('http://streams.radiobob.de/bob-90srock/mp3-192/streams.radiobob.de/play.m3u', 'bob-90srock', 'bob-90srock'),
('http://streams.radiobob.de/bob-acdc/mp3-192/streams.radiobob.de/play.m3u', 'bob-acdc', 'bob-acdc'),
('http://streams.radiobob.de/bob-alternative/mp3-192/streams.radiobob.de/play.m3u', 'bob-alternative', 'bob-alternative'),
('http://streams.radiobob.de/bob-bestofrock/mp3-192/streams.radiobob.de/play.m3u', 'bob-bestofrock', 'bob-bestofrock'),
('http://streams.radiobob.de/bob-chillout/mp3-192/streams.radiobob.de/play.m3u', 'bob-chillout', 'bob-chillout'),
('http://streams.radiobob.de/bob-christmas/mp3-192/streams.radiobob.de/play.m3u', 'bob-christmas', 'bob-christmas'),
('http://streams.radiobob.de/bob-classicrock/mp3-192/streams.radiobob.de/play.m3u', 'bob-classicrock', 'bob-classicrock'),
('http://streams.radiobob.de/bob-deutsch/mp3-192/streams.radiobob.de/play.m3u', 'bob-deutsch', 'bob-deutsch'),
('http://streams.radiobob.de/bob-festival/mp3-192/streams.radiobob.de/play.m3u', 'bob-festival', 'bob-festival'),
('http://streams.radiobob.de/bob-grunge/mp3-192/streams.radiobob.de/play.m3u', 'bob-grunge', 'bob-grunge'),
('http://streams.radiobob.de/bob-hardrock/mp3-192/streams.radiobob.de/play.m3u', 'bob-hardrock', 'bob-hardrock'),
('http://streams.radiobob.de/bob-hartesaite/mp3-192/streams.radiobob.de/play.m3u', 'bob-hartesaite', 'bob-hartesaite'),
('http://streams.radiobob.de/bob-kuschelrock/mp3-192/streams.radiobob.de/play.m3u', 'bob-kuschelrock', 'bob-kuschelrock'),
('http://streams.radiobob.de/bob-live/mp3-192/streams.radiobob.de/play.m3u', 'bob-live', 'bob-live'),
('http://streams.radiobob.de/bob-metal/mp3-192/streams.radiobob.de/play.m3u', 'bob-metal', 'bob-metal'),
('http://streams.radiobob.de/bob-national/mp3-192/streams.radiobob.de/play.m3u', 'bob-national', 'bob-national'),
('http://streams.radiobob.de/bob-punk/mp3-192/streams.radiobob.de/play.m3u', 'bob-punk', 'bob-punk'),
('http://streams.radiobob.de/bob-queen/mp3-192/streams.radiobob.de/play.m3u', 'bob-queen', 'bob-queen'),
('http://streams.radiobob.de/bob-rockabilly/mp3-192/streams.radiobob.de/play.m3u', 'bob-rockabilly', 'bob-rockabilly'),
('http://streams.radiobob.de/bob-rockhits/mp3-192/streams.radiobob.de/play.m3u', 'bob-rockhits', 'bob-rockhits'),
('http://streams.radiobob.de/bob-shlive/mp3-192/streams.radiobob.de/play.m3u', 'bob-shlive', 'bob-shlive'),
('http://streams.radiobob.de/bob-singersong/mp3-192/streams.radiobob.de/play.m3u', 'bob-singersong', 'bob-singersong'),
('http://streams.radiobob.de/bob-wacken/mp3-192/streams.radiobob.de/play.m3u', 'bob-wacken', 'bob-wacken'),
('http://streams.radiobob.de/bosshoss/mp3-192/streams.radiobob.de/play.m3u', 'bosshoss', 'bosshoss'),
('http://streams.radiobob.de/country/mp3-192/streams.radiobob.de/play.m3u', 'country', 'country'),
('http://streams.radiobob.de/deathmetal/mp3-192/streams.radiobob.de/play.m3u', 'deathmetal', 'deathmetal'),
('http://streams.radiobob.de/fury/mp3-192/streams.radiobob.de/play.m3u', 'fury', 'fury'),
('http://streams.radiobob.de/gothic/mp3-192/streams.radiobob.de/play.m3u', 'gothic', 'gothic'),
('http://streams.radiobob.de/live-hessen-mitte/mp3-192/streams.radiobob.de/play.m3u', 'live-hessen-mitte', 'live-hessen-mitte'),
('http://streams.radiobob.de/live-national-mitte/mp3-192/streams.radiobob.de/play.m3u', 'live-national-mitte', 'live-national-mitte'),
('http://streams.radiobob.de/live-nrw-mitte/mp3-192/streams.radiobob.de/play.m3u', 'live-nrw-mitte', 'live-nrw-mitte'),
('http://streams.radiobob.de/live-sh-mitte/mp3-192/streams.radiobob.de/play.m3u', 'live-sh-mitte', 'live-sh-mitte'),
('http://streams.radiobob.de/live-sh-nordwest/mp3-192/streams.radiobob.de/play.m3u', 'live-sh-nordwest', 'live-sh-nordwest'),
('http://streams.radiobob.de/live-sh-ost/mp3-192/streams.radiobob.de/play.m3u', 'live-sh-ost', 'live-sh-ost'),
('http://streams.radiobob.de/live-sh-sued/mp3-192/streams.radiobob.de/play.m3u', 'live-sh-sued', 'live-sh-sued'),
('http://streams.radiobob.de/metalcore/mp3-192/streams.radiobob.de/play.m3u', 'metalcore', 'metalcore'),
('http://streams.radiobob.de/metallica/mp3-192/streams.radiobob.de/play.m3u', 'metallica', 'metallica'),
('http://streams.radiobob.de/mittelalter/mp3-192/streams.radiobob.de/play.m3u', 'mittelalter', 'mittelalter'),
('http://streams.radiobob.de/newcomer/mp3-192/streams.radiobob.de/play.m3u', 'newcomer', 'newcomer'),
('http://streams.radiobob.de/progrock/mp3-192/streams.radiobob.de/play.m3u', 'progrock', 'progrock'),
('http://streams.radiobob.de/ritter/mp3-192/streams.radiobob.de/play.m3u', 'ritter', 'ritter'),
('http://streams.radiobob.de/rockparty/mp3-192/streams.radiobob.de/play.m3u', 'rockparty', 'rockparty'),
('http://streams.radiobob.de/sammet/mp3-192/streams.radiobob.de/play.m3u', 'sammet', 'sammet'),
('http://streams.radiobob.de/southernrock/mp3-192/streams.radiobob.de/play.m3u', 'southernrock', 'southernrock'),
('http://streams.radiobob.de/symphmetal/mp3-192/streams.radiobob.de/play.m3u', 'symphmetal', 'Symphonic Metal'),
]


for i in radios:
    print(i)
    c = Channel(display_name=i[2], display_name_short=i[1], url=i[0])
    c.save()
