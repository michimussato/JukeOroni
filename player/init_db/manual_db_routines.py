# definitions
# tuple[0]: display_name
# tuple[1]: display_name_short
# tuple[2]: station
# tuple[3]: is_enabled
# tuple[4]: url
# tuple[5]: url_logo
# tuple[6]: last_played
# tuple[7]: show_rds


# radio bob streams:
# https://bob.hoerradar.de/radiobob-80srock-aac-mq

# radio srf
# https://www.broadcast.ch/fileadmin/kundendaten/Dokumente/Internet_Streaming/2021_01_links_for_streaming_internet_radio_de_fr_it_V006.pdf

# swiss streams
# https://www.linker.ch/eigenlink/radiosender.htm

# get stream url
# https://addons.mozilla.org/en-US/firefox/addon/video-downloadhelper/

import player.models

channel_list = [
    ("BOBs 100", "100", "radio_bob", False, "http://bob.hoerradar.de/radiobob-100-mp3-hq", None, False, True),
    ("BOBs 101", "101", "radio_bob", False, "http://bob.hoerradar.de/radiobob-101-mp3-hq", None, False, True),
    ("BOBs Blues", "blues", "radio_bob", True, "http://bob.hoerradar.de/radiobob-blues-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/03/bob_2000er-rock_600x600.png", False, True),
    ("BOBs 80s Rock", "bob-80srock", "radio_bob", True, "http://bob.hoerradar.de/radiobob-80srock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_80er-rock_600x600.png", False, True),
    ("BOBs 90s Rock", "bob-90srock", "radio_bob", True, "http://bob.hoerradar.de/radiobob-90srock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_90er-rock_600x600.png", False, True),
    ("BOBs AC/DC", "bob-acdc", "radio_bob", True, "http://bob.hoerradar.de/radiobob-acdc-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_acdc_600x600.png", False, True),
    ("BOBs Alternative", "bob-alternative", "radio_bob", True, "http://bob.hoerradar.de/radiobob-alternative-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2018/07/radiobob-streamicon_alternative-rock-1.png", False, True),
    ("BOBs Best of Rock", "bob-bestofrock", "radio_bob", True, "http://bob.hoerradar.de/radiobob-bestofrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_best-of-rock_600x600.png", False, True),
    ("BOBs Unplugged (Chillout)", "bob-unplugged-chillout", "radio_bob", True, "http://bob.hoerradar.de/radiobob-chillout-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_unplugged_600x600.png", False, True),
    ("BOBS Classic Rock", "bob-classicrock", "radio_bob", True, "http://bob.hoerradar.de/radiobob-classicrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_classic-rock_600x600.png", False, True),
    ("BOBs Deutsch Rock", "bob-deutsch", "radio_bob", True, "http://bob.hoerradar.de/radiobob-deutsch-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_deutschrock_600x600.png", False, True),
    ("BOBs Festival", "bob-festival", "radio_bob", True, "http://bob.hoerradar.de/radiobob-festival-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_festival_600x600.png", False, True),
    ("BOBs Grunge", "bob-grunge", "radio_bob", True, "http://bob.hoerradar.de/radiobob-grunge-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_grunge_600x600.png", False, True),
    ("BOBs Hard Rock", "bob-hardrock", "radio_bob", True, "http://bob.hoerradar.de/radiobob-hardrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_hardrock_600x600.png", False, True),
    ("BOBs Harte Saite", "bob-hartesaite", "radio_bob", True, "http://bob.hoerradar.de/radiobob-hartesaite-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_harte-saite_600x600.png", False, True),
    ("BOBs Live", "bob-live", "radio_bob", True, "http://bob.hoerradar.de/radiobob-live-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_livestream-rock-n-pop_600x600.png", False, True),
    ("BOBs Metal", "bob-metal", "radio_bob", True, "http://bob.hoerradar.de/radiobob-metal-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metal_600x600.png", False, True),
    ("BOBs National", "bob-national", "radio_bob", True, "http://bob.hoerradar.de/radiobob-national-mp3-hq", "https://images.radiobob.de/files/streams/bob_stream-tile_livestream-rock-n-pop.jpg", False, True),
    ("BOBs Punk", "bob-punk", "radio_bob", True, "http://bob.hoerradar.de/radiobob-punk-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_punk_600x600.png", False, True),
    ("BOBs Rockabilly", "bob-rockabilly", "radio_bob", True, "http://bob.hoerradar.de/radiobob-rockabilly-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_rockabilly_600x600.png", False, True),
    ("BOBs Rock Hits", "bob-rockhits", "radio_bob", True, "http://bob.hoerradar.de/radiobob-rockhits-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_rock-hits_600x600.png", False, True),
    ("bob-shlive", "bob-shlive", "radio_bob", True, "http://bob.hoerradar.de/radiobob-shlive-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2018/07/radiobob-streamicon_bobs-livestream-bob-rockt-sh-1.png", False, True),
    ("BOBs Singer-Songwriter", "bob-singersong", "radio_bob", True, "http://bob.hoerradar.de/radiobob-singersong-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_singer-songwriter_600x600.png", False, True),
    ("BOBs Wacken", "bob-wacken", "radio_bob", True, "http://bob.hoerradar.de/radiobob-wacken-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_wacken_600x600.png", False, True),
    ("BOBs Boss Hoss", "bosshoss", "radio_bob", True, "http://bob.hoerradar.de/radiobob-bosshoss-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/06/bob_bosshoss-rockshow_600x600.png", False, True),
    ("BOBs Country", "country", "radio_bob", True, "http://bob.hoerradar.de/radiobob-country-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/04/bob_country_600x600.png", False, True),
    ("BOBs Death Metal", "deathmetal", "radio_bob", True, "http://bob.hoerradar.de/radiobob-deathmetal-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/07/bob_death-metal_600x600.png", False, True),
    ("BOBs Fury In The Slaughterhouse", "fury", "radio_bob", True, "http://bob.hoerradar.de/radiobob-fury-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/06/bob_furyintheslaughterhouse_600x600.png", False, True),
    ("BOBs Gothic Metal", "gothic", "radio_bob", True, "http://bob.hoerradar.de/radiobob-gothic-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_gothic_600x600.png", False, True),
    ("Live National Mitte", "live-national-mitte", "radio_bob", True, "http://bob.hoerradar.de/radiobob-live-national-mitte-mp3-hq", "https://images.radiobob.de/files/streams/bob_stream-tile_livestream-rock-n-pop.jpg", False, True),
    ("live-sh-nordwest", "live-sh-nordwest", "radio_bob", False, "http://bob.hoerradar.de/radiobob-live-sh-nordwest-mp3-hq", None, False, True),
    ("live-sh-ost", "live-sh-ost", "radio_bob", False, "http://bob.hoerradar.de/radiobob-live-sh-ost-mp3-hq", None, False, True),
    ("BOBs Metal Core", "metalcore", "radio_bob", True, "http://bob.hoerradar.de/radiobob-metalcore-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metalcore_600x600-1.png", False, True),
    ("BOBs Metallica", "metallica", "radio_bob", True, "http://bob.hoerradar.de/radiobob-metallica-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metallica_600x600.png", False, True),
    ("BOBs Mittelalter", "mittelalter", "radio_bob", True, "http://bob.hoerradar.de/radiobob-mittelalter-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_mittelalter-rock_600x600.png", False, True),
    ("BOBs Newcomer", "newcomer", "radio_bob", True, "http://bob.hoerradar.de/radiobob-newcomer-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_newcomer_600x600.png", False, True),
    ("BOBs Progressive Rock", "progrock", "radio_bob", True, "http://bob.hoerradar.de/radiobob-progrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/04/bob_prog-rock_600x600.png", False, True),
    ("BOBs Der Dunkle Parabelritter", "ritter", "radio_bob", True, "https://bob.hoerradar.de/radiobob-dunklepritter-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_parabelritter_600x600.png", False, True),
    ("BOBs Rock Party", "rockparty", "radio_bob", True, "http://bob.hoerradar.de/radiobob-rockparty-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_rockparty_600x600.png", False, True),
    ("BOBs Sammet Rockshow", "sammet", "radio_bob", True, "http://bob.hoerradar.de/radiobob-sammet-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_tobias-sammet-rockshow_600x600.png", False, True),
    ("BOBs Southern Rock", "southernrock", "radio_bob", True, "http://bob.hoerradar.de/radiobob-southernrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_southern-rock_600x600.png", False, True),
    ("BOBs Symphonic Metal", "symphmetal", "radio_bob", True, "http://bob.hoerradar.de/radiobob-symphmetal-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/07/bob_symphonic-metal_600x600.jpg", False, True),
    ("SRF 3", "srf_3", "srf", True, "http://stream.srg-ssr.ch/m/drs3/aacp_96", "https://mytuner.global.ssl.fastly.net/media/tvos_radios/8S4qGytr8f.png", False, True),
    ("SRF 2 Kultur", "srf_2", "srf", True, "http://stream.srg-ssr.ch/m/drs2/aacp_96", "https://mytuner.global.ssl.fastly.net/media/tvos_radios/XphWMbkRsU.png", False, True),
    ("SRF 1", "srf_1", "srf", True, "http://stream.srg-ssr.ch/m/drs1/aacp_96", "https://www.liveradio.ie/files/images/105819/resized/180x172c/radioooo.png", False, True),
    ("SRF 4 News", "srf_4", "srf", True, "http://stream.srg-ssr.ch/m/drs4news/aacp_96", "https://seeklogo.com/images/R/radio-srf-4-news-logo-D17966CFE5-seeklogo.com.png", False, False),
    ("SRF Virus", "srf_virus", "srf", True, "http://stream.srg-ssr.ch/m/drsvirus/aacp_96", "https://static.mytuner.mobi/media/tvos_radios/3dEg2QhxNP.png", False, True),
    ("SRF Swiss Classic", "srf_swiss_classic", "srf", True, "http://stream.srg-ssr.ch/m/rsc_de/aacp_96", "https://upload.wikimedia.org/wikipedia/commons/a/a4/Radio_Swiss_Classic_Logo_2018.svg", False, True),
    ("SRF Swiss Jazz", "srf_swiss_jazz", "srf", True, "http://stream.srg-ssr.ch/m/rsj/aacp_96", "https://upload.wikimedia.org/wikipedia/commons/9/9e/Radio_Swiss_Jazz_logo.png", False, True),
    ("SRF Swiss Pop", "srf_swiss_pop", "srf", True, "http://stream.srg-ssr.ch/m/rsp/aacp_96", "https://mx3.ch/pictures/mx3/file/0033/0569/original/radioswisspop_1_rgb.jpg?1429621701", False, True),
    ("SRF Couleur 3", "couleur_3", "srf", True, "http://stream.srg-ssr.ch/m/couleur3/aacp_96", "https://d3kle7qwymxpcy.cloudfront.net/images/broadcasts/1b/af/1489/5/c175.png", False, True),
    ("Radio Morcote International (Ticino)", "morcote", "None", True, "http://streaming.radiomorcoteinternational.com:8000/;?type=http", "https://i1.wp.com/www.fm-world.it/wp-content/uploads/2020/05/Logo-Radio-Morcote-Intenational.jpg", False, True),
    ("Rock Antenne Hamburg", "rock_antenne_hamburg", "rock_antenne", True, "http://stream.rockantenne.hamburg/rockantenne-hamburg", "https://www.rockantenne.de/assets/templates/rockantenne-de//img/logo-rockantenne-de-header-2.svg", False, True),
    ("Rock Antenne Heavy Metal", "rock_antenne_heavy_metal", "rock_antenne", True, "http://stream.rockantenne.de/heavy-metal", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_heavy_480.jpg", False, True),
    ("Rock Antenne Hair Metal", "rock_antenne_hair_metal", "rock_antenne", True, "http://stream.rockantenne.de/hair-metal", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_hair_480.jpg", False, True),
    ("Rock Antenne Blues Rock", "rock_antenne_blues_rock", "rock_antenne", True, "http://stream.rockantenne.de/blues-rock", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_blues_480.jpg", False, True),
    ("Rock Antenne Live Rock", "rock_antenne_live_rock", "rock_antenne", True, "http://stream.rockantenne.de/live-rock", "https://cdn.antenne.de/antenne-de/uploads/images/ra_stream_live_480.jpg", False, True),
    ("Rock Antenne 80er Rock", "rock_antenne_80er_rock", "rock_antenne", True, "http://stream.rockantenne.de/80er-rock", "https://cdn.antenne.de/antenne-de/uploads/images/ra_stream_80er_480.jpg", False, True),
    ("Rock Antenne Alternative", "rock_antenne_alternative", "rock_antenne", True, "http://stream.rockantenne.de/alternative", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_alternative_480.jpg", False, True),
    ("Rock Antenne Classic Perlen", "rock_antenne_classic_perlen", "rock_antenne", True, "http://stream.rockantenne.de/classic-perlen", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_classic_480.jpg", False, True),
    ("Rock Antenne Melodic Rock", "rock_antenne_melodic_rock", "rock_antenne", True, "http://stream.rockantenne.de/melodic-rock", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_melodic_480.jpg", False, True),
    ("Rock Antenne Punk Rock", "rock_antenne_punk_rock", "rock_antenne", True, "http://stream.rockantenne.de/punkrock", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_punk_480.jpg", False, True),
    ("Rock Antenne Deutschrock", "rock_antenne_deutschrock", "rock_antenne", True, "http://stream.rockantenne.de/deutschrock", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_deutsch_480.jpg", False, True),
    ("Rock Antenne Rock 'n Roll", "rock_antenne_rock_and_roll", "rock_antenne", True, "http://stream.rockantenne.de/rockandroll", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_rocknroll_480.jpg", False, True),
    ("Rock Antenne Soft Rock", "rock_antenne_soft_rock", "rock_antenne", True, "http://stream.rockantenne.de/soft-rock", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_soft_480.jpg", False, True),
    ("Rock Antenne Young Stars", "rock_antenne_young_stars", "rock_antenne", True, "http://stream.rockantenne.de/young-stars", "https://cdn.antenne.de/antenne-de/uploads/images/ra_stream_young-and-home_480.jpg", False, True),
    ("Rock Antenne Cover Songs", "rock_antenne_cover_songs", "rock_antenne", True, "http://stream.rockantenne.de/coversongs", "https://cdn.antenne.de/antenne-de/uploads/images/ra_stream_coversongs_480.jpg", False, True),
    ("Rock Antenne Munich City Nights", "rock_antenne_munich_city_nights", "rock_antenne", True, "http://stream.rockantenne.de/munich-city-nights", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_munich_480.jpg", False, True),
    ("Rock Antenne Xmas Rock", "rock_antenne_xmas_rock", "rock_antenne", True, "http://stream.rockantenne.de/xmas-rock", "https://cdn.antenne.de/rockantenne-de/uploads/images/music/ra_stream_xmas_480.jpg", False, True),
    ("Positively Ocean", "positively_ocean", "positivity_radio", True, "https://streaming.positivity.radio/pr/posiocean/icecast.audio", "https://manager.uber.radio/static/uploads/station/04a24bc1-60d9-4ed3-8d65-c079c0513804.png", False, True),
    ("Positively Cascade", "positively_cascade", "positivity_radio", True, "https://streaming.positivity.radio/pr/posicascade/icecast.audio", "https://manager.uber.radio/static/uploads/station/55b5f14f-50b3-459d-ad68-0e7f936c7c57.png", False, True),
    ("Positively Bowls", "positively_bowls", "positivity_radio", True, "https://streaming.positivity.radio/pr/bowls/icecast.audio", "https://manager.uber.radio/static/uploads/station/8ed36a81-2af4-40d8-910e-bc7d8b4f29f6.png", False, True),
    ("Positively Chants", "positively_chants", "positivity_radio", True, "https://streaming.positivity.radio/pr/chants/icecast.audio", "https://manager.uber.radio/static/uploads/station/ae5dc21d-62d3-43f9-b172-b3cb9ea9d3e4.png", False, True),
    ("Positively Classical", "positively_classical", "positivity_radio", True, "https://streaming.positivity.radio/pr/posiclassical/icecast.audio", "https://manager.uber.radio/static/uploads/station/8c38964f-93ad-42e1-aca9-fb3f47c72b5a.png", False, True),
    ("Positively Energy", "positively_energy", "positivity_radio", True, "https://streaming.positivity.radio/pr/energy/icecast.audio", "https://manager.uber.radio/static/uploads/station/15980f15-72e1-404f-9d8e-00b9958fe090.png", False, True),
    ("Positively Instrumental", "positively_instrumental", "positivity_radio", True, "https://streaming.positivity.radio/pr/soothinginstrumental/icecast.audio", "https://manager.uber.radio/static/uploads/station/22ec010b-ecbd-469f-aa21-4b678bce7dbc.png", False, True),
    ("Positively Jazz", "positively_jazz", "positivity_radio", True, "https://streaming.positivity.radio/pr/jazz/icecast.audio", "https://manager.uber.radio/static/uploads/station/79e27798-d2f6-47db-ad46-f727a2405229.png", False, True),
    ("Positively Meditation", "positively_meditation", "positivity_radio", True, "https://streaming.positivity.radio/pr/posimeditation/icecast.audio", "https://manager.uber.radio/static/uploads/station/061eccde-746b-49d4-aad5-dc636e8ea3fb.png", False, True),
    ("Positively Piano", "positively_piano", "positivity_radio", True, "https://streaming.positivity.radio/pr/piano/icecast.audio", "https://manager.uber.radio/static/uploads/station/eeb48846-f78d-4ba7-9f5f-4f08f1ca32ea.png", False, True),
    ("Positively Relaxation", "positively_relaxation", "positivity_radio", True, "https://streaming.positivity.radio/pr/relaxation/icecast.audio", "https://manager.uber.radio/static/uploads/station/534c865c-0c2e-4b93-87b9-1ec54e445739.png", True, False),
    ("Positively Relaxing Workout", "positively_relaxing_workout", "positivity_radio", True, "https://streaming.positivity.radio/pr/workoutrelax/icecast.audio", "https://manager.uber.radio/static/uploads/station/d349ba0c-d80b-48fb-ba6b-9b1f52bbae55.png", False, True),
    ("Positively Sleep Classical", "positively_sleep_classical", "positivity_radio", True, "https://streaming.positivity.radio/pr/sleepclassical/icecast.audio", "https://manager.uber.radio/static/uploads/station/ab52c7d3-5a7a-4478-979b-f2086cc06e16.png", False, True),
    ("Positively Sleep Tones", "positively_sleep_tones", "positivity_radio", True, "https://streaming.positivity.radio/pr/sleeptones/icecast.audio", "https://manager.uber.radio/static/uploads/station/7aeae7c1-85ea-4350-b2fb-402a71d300b1.png", False, True),
    ("Positively Sleepy", "positively_sleepy", "positivity_radio", True, "https://streaming.positivity.radio/pr/posisleepy/icecast.audio", "https://manager.uber.radio/static/uploads/station/ac2cc0dd-5e8e-46d2-b60f-f15492b42971.png", False, True),
    ("Positively Soundscapes", "positively_soundscapes", "positivity_radio", True, "https://streaming.positivity.radio/pr/soundscapes/icecast.audio", "https://manager.uber.radio/static/uploads/station/b092eae9-a104-4495-bd94-b227bd9a7a87.png", False, True),
    ("Positively Tranquil", "positively_tranquil", "positivity_radio", True, "https://streaming.positivity.radio/pr/positranquil/icecast.audio", "https://manager.uber.radio/static/uploads/station/765078fd-51fa-4374-9791-8ff439ed38c0.png", False, True),
    ("Positively Zen", "positively_zen", "positivity_radio", True, "https://streaming.positivity.radio/pr/zen/icecast.audio", "https://manager.uber.radio/static/uploads/station/bab48d63-35cf-40ea-8d67-73a5b240619b.png", False, True),
    ("Positively Spa", "positively_spa", "positivity_radio", True, "https://streaming.positivity.radio/pr/spa/icecast.audio", "https://manager.uber.radio/static/uploads/station/ee834240-15b7-441f-9036-1fdad871aa3b.png", False, True),
    ("Positively Stress Relief", "positively_stress_relief", "positivity_radio", True, "https://streaming.positivity.radio/pr/stressrelief/icecast.audio", "https://manager.uber.radio/static/uploads/station/46e28c0d-4d0c-49d0-93b0-7742548d67ec.png", False, True),
    ("Positively Tai Chi", "positively_tai_chi", "positivity_radio", True, "https://streaming.positivity.radio/pr/taichi/icecast.audio", "https://manager.uber.radio/static/uploads/station/6f72f6c0-0d4f-4b1e-b737-98f3758cffa0.png", False, True),
    ("Drift.FM", "drift-fm", "None", True, "https://s4.radio.co/s5729f2e59/listen?=&&___cb=292499116560050", "https://www.drift.fm/hintergrund.jpg", False, False),
]


def channels_write_table():
    """usage
from player.init_db.manual_db_routines import channels_write_table
channels_write_table()
"""

    from player.models import Channel, Station
    for channel in channel_list:
        display_name = channel[0]
        display_name_short = channel[1]
        station = channel[2]
        is_enabled = channel[3]
        url = channel[4]
        url_logo = channel[5]
        last_played = channel[6]
        show_rds = channel[7]

        if station == 'None':
            _station = None
        else:
            try:
                _station = Station.objects.get(display_name_short=station)
            except player.models.Station.DoesNotExist:
                _station = Station(
                    display_name=station.title().replace('_', ' '),
                    display_name_short=station,
                )
                _station.save()

        c = Channel(
            display_name=display_name,
            display_name_short=display_name_short,
            station=_station,
            is_enabled=is_enabled,
            url=url,
            url_logo=url_logo,
            last_played=last_played,
            show_rds=show_rds,
        )
        c.save()

        print(f'{_station}:{c} added')


def channels_dump_table():
    """usage
from player.init_db.manual_db_routines import channels_dump_table
channels_dump_table()
"""

    from player.models import Channel
    _channels = Channel.objects.all()
    for _channel in _channels:
        if _channel.url_logo is None:
            _url_logo = None
        else:
            _url_logo = f'\"{_channel.url_logo}\"'
        print(f'(\"{_channel.display_name}\", \"{_channel.display_name_short}\", \"{_channel.station}\", {_channel.is_enabled}, \"{_channel.url}\", {_url_logo}, {_channel.last_played}, {_channel.show_rds}),')


def remove_tracks_albums_artists():
    """usage
from player.init_db.manual_db_routines import remove_tracks_albums_artists
remove_tracks_albums_artists()
"""

    from player.models import Track, Album, Artist
    Track.objects.all().delete()
    Album.objects.all().delete()
    Artist.objects.all().delete()


def remove_channels(remove_stations=True):
    """usage
from player.init_db.manual_db_routines import remove_channels
remove_channels()
"""

    from player.models import Channel, Station
    Channel.objects.all().delete()
    if remove_stations:
        Station.objects.all().delete()
