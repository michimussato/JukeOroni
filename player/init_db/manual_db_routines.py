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
import player.models

channel_list = [
    ("BOBs 100", "100", "radio_bob", True, "http://bob.hoerradar.de/radiobob-100-mp3-hq", "None", False, True),
    ("BOBs 101", "101", "radio_bob", True, "http://bob.hoerradar.de/radiobob-101-mp3-hq", "None", False, True),
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
    ("BOBs National", "bob-national", "radio_bob", True, "http://bob.hoerradar.de/radiobob-national-mp3-hq", "None", False, True),
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
    ("Live National-Mitte", "live-national-mitte", "None", True, "http://bob.hoerradar.de/radiobob-live-national-mitte-mp3-hq", "None", False, True),
    ("live-sh-nordwest", "live-sh-nordwest", "None", True, "http://bob.hoerradar.de/radiobob-live-sh-nordwest-mp3-hq", "None", False, True),
    ("live-sh-ost", "live-sh-ost", "None", True, "http://bob.hoerradar.de/radiobob-live-sh-ost-mp3-hq", "None", False, True),
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
    ("SRF 4 News", "srf_4", "srf", True, "http://stream.srg-ssr.ch/m/drs4news/aacp_96", "https://seeklogo.com/images/R/radio-srf-4-news-logo-D17966CFE5-seeklogo.com.png", False, True),
    ("SRF Virus", "srf_virus", "srf", True, "http://stream.srg-ssr.ch/m/drsvirus/aacp_96", "https://i1.sndcdn.com/avatars-000028958863-4mhkle-t500x500.jpg", False, True),
    ("SRF Swiss Classic", "srf_swiss_classic", "srf", True, "http://stream.srg-ssr.ch/m/rsc_de/aacp_96", "https://i1.sndcdn.com/artworks-000575528372-2khk7a-t500x500.jpg", False, True),
    ("SRF Swiss Jazz", "srf_swiss_jazz", "srf", True, "http://stream.srg-ssr.ch/m/rsj/aacp_96", "https://upload.wikimedia.org/wikipedia/commons/9/9e/Radio_Swiss_Jazz_logo.png", False, True),
    ("SRF Swiss Pop", "srf_swiss_pop", "srf", True, "http://stream.srg-ssr.ch/m/rsp/aacp_96", "https://mx3.ch/pictures/mx3/file/0033/0569/original/radioswisspop_1_rgb.jpg?1429621701", False, True),
    ("SRF Couleur 3", "couleur_3", "srf", True, "http://stream.srg-ssr.ch/m/couleur3/aacp_96", "https://d3kle7qwymxpcy.cloudfront.net/images/broadcasts/1b/af/1489/5/c175.png", False, True),
    ("Radio Morcote International (Ticino)", "morcote", "None", True, "http://streaming.radiomorcoteinternational.com:8000/;?type=http", "https://i1.wp.com/www.fm-world.it/wp-content/uploads/2020/05/Logo-Radio-Morcote-Intenational.jpg", False, True),
    ("Rock Antenne Hamburg", "rock_antenne_hamburg", "rock_antenne", True, "http://stream.rockantenne.hamburg/rockantenne-hamburg", "None", False, True),
    ("Rock Antenne Heavy Metal", "rock_antenne_heavy_metal", "rock_antenne", True, "http://stream.rockantenne.de/heavy-metal", "None", False, True),
    ("Rock Antenne Hair Metal", "rock_antenne_hair_metal", "rock_antenne", True, "http://stream.rockantenne.de/hair-metal", "None", False, True),
    ("Rock Antenne Blues Rock", "rock_antenne_blues_rock", "rock_antenne", True, "http://stream.rockantenne.de/blues-rock", "None", False, True),
    ("Rock Antenne Live Rock", "rock_antenne_live_rock", "rock_antenne", True, "http://stream.rockantenne.de/live-rock", "None", False, True),
    ("Rock Antenne 80er Rock", "rock_antenne_80er_rock", "rock_antenne", True, "http://stream.rockantenne.de/80er-rock", "None", False, True),
    ("Rock Antenne Alternative", "rock_antenne_alternative", "rock_antenne", True, "http://stream.rockantenne.de/alternative", "None", False, True),
    ("Rock Antenne Classic Perlen", "rock_antenne_classic_perlen", "rock_antenne", True, "http://stream.rockantenne.de/classic-perlen", "None", False, True),
    ("Rock Antenne Melodic Rock", "rock_antenne_melodic_rock", "rock_antenne", True, "http://stream.rockantenne.de/melodic-rock", "None", False, True),
    ("Rock Antenne Punk Rock", "rock_antenne_punk_rock", "rock_antenne", True, "http://stream.rockantenne.de/punkrock", "None", False, True),
    ("Rock Antenne Deutschrock", "rock_antenne_deutschrock", "rock_antenne", True, "http://stream.rockantenne.de/deutschrock", "None", False, True),
    ("Rock Antenne Rock 'n Roll", "rock_antenne_rock_and_roll", "rock_antenne", True, "http://stream.rockantenne.de/rockandroll", "None", False, True),
    ("Rock Antenne Soft Rock", "rock_antenne_soft_rock", "rock_antenne", True, "http://stream.rockantenne.de/soft-rock", "None", False, True),
    ("Rock Antenne Young Stars", "rock_antenne_young_stars", "rock_antenne", True, "http://stream.rockantenne.de/young-stars", "None", False, True),
    ("Rock Antenne Cover Songs", "rock_antenne_cover_songs", "rock_antenne", True, "http://stream.rockantenne.de/coversongs", "None", False, True),
    ("Rock Antenne Munich City Nights", "rock_antenne_munich_city_nights", "rock_antenne", True, "http://stream.rockantenne.de/munich-city-nights", "None", False, True),
    ("Rock Antenne Xmas Rock", "rock_antenne_xmas_rock", "rock_antenne", True, "http://stream.rockantenne.de/xmas-rock", "None", False, True),

    # ("BOBs 100", "100", True, "http://bob.hoerradar.de/radiobob-100-mp3-hq", None, False),
    # ("BOBs 101", "101", True, "http://bob.hoerradar.de/radiobob-101-mp3-hq", None, False),
    # # ("BOBs 2000er", "2000er", True, "http://bob.hoerradar.de/radiobob-2000er-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/03/bob_2000er-rock_600x600.png", False),
    # ("BOBs Blues", "blues", True, "http://bob.hoerradar.de/radiobob-blues-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/03/bob_2000er-rock_600x600.png", False),
    # ("BOBs 80s Rock", "bob-80srock", True, "http://bob.hoerradar.de/radiobob-80srock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_80er-rock_600x600.png", False),
    # ("BOBs 90s Rock", "bob-90srock", True, "http://bob.hoerradar.de/radiobob-90srock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_90er-rock_600x600.png", False),
    # ("BOBs AC/DC", "bob-acdc", True, "http://bob.hoerradar.de/radiobob-acdc-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_acdc_600x600.png", False),
    # ("BOBs Alternative", "bob-alternative", True, "http://bob.hoerradar.de/radiobob-alternative-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2018/07/radiobob-streamicon_alternative-rock-1.png", False),
    # ("BOBs Best of Rock", "bob-bestofrock", True, "http://bob.hoerradar.de/radiobob-bestofrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_best-of-rock_600x600.png", False),
    # ("BOBs Unplugged (Chillout)", "bob-unplugged-chillout", True, "http://bob.hoerradar.de/radiobob-chillout-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_unplugged_600x600.png", False),
    # # ("BOBs Christmas", "bob-christmas", False, "http://bob.hoerradar.de/radiobob-christmas-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_christmas-rock_600x600.png", False),
    # ("BOBS Classic Rock", "bob-classicrock", True, "http://bob.hoerradar.de/radiobob-classicrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_classic-rock_600x600.png", False),
    # ("BOBs Deutsch Rock", "bob-deutsch", True, "http://bob.hoerradar.de/radiobob-deutsch-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_deutschrock_600x600.png", False),
    # ("BOBs Festival", "bob-festival", True, "http://bob.hoerradar.de/radiobob-festival-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_festival_600x600.png", False),
    # ("BOBs Grunge", "bob-grunge", True, "http://bob.hoerradar.de/radiobob-grunge-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_grunge_600x600.png", False),
    # ("BOBs Hard Rock", "bob-hardrock", True, "http://bob.hoerradar.de/radiobob-hardrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_hardrock_600x600.png", False),
    # ("BOBs Harte Saite", "bob-hartesaite", True, "http://bob.hoerradar.de/radiobob-hartesaite-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_harte-saite_600x600.png", True),
    # # ("BOBs Kuschel Rock", "bob-kuschelrock", False, "http://bob.hoerradar.de/radiobob-kuschelrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_kuschelrock_600x600.png", False),
    # ("BOBs Live", "bob-live", True, "http://bob.hoerradar.de/radiobob-live-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_livestream-rock-n-pop_600x600.png", False),
    # ("BOBs Metal", "bob-metal", True, "http://bob.hoerradar.de/radiobob-metal-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metal_600x600.png", False),
    # ("BOBs National", "bob-national", True, "http://bob.hoerradar.de/radiobob-national-mp3-hq", None, False),
    # ("BOBs Punk", "bob-punk", True, "http://bob.hoerradar.de/radiobob-punk-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_punk_600x600.png", False),
    # # ("BOBs Queen", "bob-queen", False, "http://bob.hoerradar.de/radiobob-queen-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_queen_600x600.png", False),
    # ("BOBs Rockabilly", "bob-rockabilly", True, "http://bob.hoerradar.de/radiobob-rockabilly-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_rockabilly_600x600.png", False),
    # ("BOBs Rock Hits", "bob-rockhits", True, "http://bob.hoerradar.de/radiobob-rockhits-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_rock-hits_600x600.png", False),
    # ("bob-shlive", "bob-shlive", True, "http://bob.hoerradar.de/radiobob-shlive-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2018/07/radiobob-streamicon_bobs-livestream-bob-rockt-sh-1.png", False),
    # ("BOBs Singer-Songwriter", "bob-singersong", True, "http://bob.hoerradar.de/radiobob-singersong-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_singer-songwriter_600x600.png", False),
    # ("BOBs Wacken", "bob-wacken", True, "http://bob.hoerradar.de/radiobob-wacken-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_wacken_600x600.png", False),
    # ("BOBs Boss Hoss", "bosshoss", True, "http://bob.hoerradar.de/radiobob-bosshoss-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/06/bob_bosshoss-rockshow_600x600.png", False),
    # ("BOBs Country", "country", True, "http://bob.hoerradar.de/radiobob-country-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/04/bob_country_600x600.png", False),
    # ("BOBs Death Metal", "deathmetal", True, "http://bob.hoerradar.de/radiobob-deathmetal-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/07/bob_death-metal_600x600.png", False),
    # ("BOBs Fury In The Slaughterhouse", "fury", True, "http://bob.hoerradar.de/radiobob-fury-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/06/bob_furyintheslaughterhouse_600x600.png", False),
    # ("BOBs Gothic Metal", "gothic", True, "http://bob.hoerradar.de/radiobob-gothic-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_gothic_600x600.png", False),
    # # ("Live Hessen-Mitte", "live-hessen-mitte", False, "http://bob.hoerradar.de/radiobob-live-hessen-mitte-mp3-hq", None, False),
    # ("Live National-Mitte", "live-national-mitte", True, "http://bob.hoerradar.de/radiobob-live-national-mitte-mp3-hq", None, False),
    # # ("Live NRM-Mitte", "live-nrw-mitte", False, "http://bob.hoerradar.de/radiobob-live-nrw-mitte-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/06/bob_livestream-rock-n-pop_600x600.png", False),
    # # ("live-sh-mitte", "live-sh-mitte", False, "http://bob.hoerradar.de/radiobob-live-sh-mitte-mp3-hq", None, False),
    # ("live-sh-nordwest", "live-sh-nordwest", True, "http://bob.hoerradar.de/radiobob-live-sh-nordwest-mp3-hq", None, False),
    # ("live-sh-ost", "live-sh-ost", True, "http://bob.hoerradar.de/radiobob-live-sh-ost-mp3-hq", None, False),
    # # ("live-sh-sued", "live-sh-sued", False, "http://bob.hoerradar.de/radiobob-live-sh-sued-mp3-hq", None, False),
    # ("BOBs Metal Core", "metalcore", True, "http://bob.hoerradar.de/radiobob-metalcore-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metalcore_600x600-1.png", False),
    # ("BOBs Metallica", "metallica", True, "http://bob.hoerradar.de/radiobob-metallica-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metallica_600x600.png", False),
    # ("BOBs Mittelalter", "mittelalter", True, "http://bob.hoerradar.de/radiobob-mittelalter-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_mittelalter-rock_600x600.png", False),
    # ("BOBs Newcomer", "newcomer", True, "http://bob.hoerradar.de/radiobob-newcomer-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_newcomer_600x600.png", False),
    # ("BOBs Progressive Rock", "progrock", True, "http://bob.hoerradar.de/radiobob-progrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/04/bob_prog-rock_600x600.png", False),
    # ("BOBs Der Dunkle Parabelritter", "ritter", True, "https://bob.hoerradar.de/radiobob-dunklepritter-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_parabelritter_600x600.png", False),
    # ("BOBs Rock Party", "rockparty", True, "http://bob.hoerradar.de/radiobob-rockparty-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_rockparty_600x600.png", False),
    # ("BOBs Sammet Rockshow", "sammet", True, "http://bob.hoerradar.de/radiobob-sammet-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_tobias-sammet-rockshow_600x600.png", False),
    # ("BOBs Southern Rock", "southernrock", True, "http://bob.hoerradar.de/radiobob-southernrock-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_southern-rock_600x600.png", False),
    # ("BOBs Symphonic Metal", "symphmetal", True, "http://bob.hoerradar.de/radiobob-symphmetal-mp3-hq", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/07/bob_symphonic-metal_600x600.jpg", False),
    # ("SRF 3", "srf_3", True, "http://stream.srg-ssr.ch/m/drs3/aacp_96", "https://mytuner.global.ssl.fastly.net/media/tvos_radios/8S4qGytr8f.png", False),
    # ("SRF 2 Kultur", "srf_2", True, "http://stream.srg-ssr.ch/m/drs2/aacp_96", "https://mytuner.global.ssl.fastly.net/media/tvos_radios/XphWMbkRsU.png", False),
    # ("SRF 1", "srf_1", True, "http://stream.srg-ssr.ch/m/drs1/aacp_96", "https://www.liveradio.ie/files/images/105819/resized/180x172c/radioooo.png", False),
    # ("SRF 4 News", "srf_4", True, "http://stream.srg-ssr.ch/m/drs4news/aacp_96", "https://seeklogo.com/images/R/radio-srf-4-news-logo-D17966CFE5-seeklogo.com.png", False),
    # ("SRF Virus", "srf_virus", True, "http://stream.srg-ssr.ch/m/drsvirus/aacp_96", "https://i1.sndcdn.com/avatars-000028958863-4mhkle-t500x500.jpg", False),
    # ("SRF Swiss Classic", "srf_swiss_classic", True, "http://stream.srg-ssr.ch/m/rsc_de/aacp_96", "https://i1.sndcdn.com/artworks-000575528372-2khk7a-t500x500.jpg", False),
    # ("SRF Swiss Jazz", "srf_swiss_jazz", True, "http://stream.srg-ssr.ch/m/rsj/aacp_96", "https://upload.wikimedia.org/wikipedia/commons/9/9e/Radio_Swiss_Jazz_logo.png", False),
    # ("SRF Swiss Pop", "srf_swiss_pop", True, "http://stream.srg-ssr.ch/m/rsp/aacp_96", "https://mx3.ch/pictures/mx3/file/0033/0569/original/radioswisspop_1_rgb.jpg?1429621701", False),
    # ("SRF Couleur 3", "couleur_3", True, "http://stream.srg-ssr.ch/m/couleur3/aacp_96", "https://d3kle7qwymxpcy.cloudfront.net/images/broadcasts/1b/af/1489/5/c175.png", False),
    # ("Radio Morcote International (Ticino)", "morcote", True, "http://streaming.radiomorcoteinternational.com:8000/;?type=http", "https://i1.wp.com/www.fm-world.it/wp-content/uploads/2020/05/Logo-Radio-Morcote-Intenational.jpg", False),
    # ("Rock Antenne Hamburg", "rock_antenne_hamburg", True, "http://stream.rockantenne.hamburg/rockantenne-hamburg", None, False),
    # ("Rock Antenne Heavy Metal", "rock_antenne_heavy_metal", True, "http://stream.rockantenne.de/heavy-metal", None, False),
    # ("Rock Antenne Hair Metal", "rock_antenne_hair_metal", True, "http://stream.rockantenne.de/hair-metal", None, False),
    # ("Rock Antenne Blues Rock", "rock_antenne_blues_rock", True, "http://stream.rockantenne.de/blues-rock", None, False),
    # ("Rock Antenne Live Rock", "rock_antenne_live_rock", True, "http://stream.rockantenne.de/live-rock", None, False),
    # ("Rock Antenne 80er Rock", "rock_antenne_80er_rock", True, "http://stream.rockantenne.de/80er-rock", None, False),
    # ("Rock Antenne Alternative", "rock_antenne_alternative", True, "http://stream.rockantenne.de/alternative", None, False),
    # ("Rock Antenne Classic Perlen", "rock_antenne_classic_perlen", True, "http://stream.rockantenne.de/classic-perlen", None, False),
    # ("Rock Antenne Melodic Rock", "rock_antenne_melodic_rock", True, "http://stream.rockantenne.de/melodic-rock", None, False),
    # ("Rock Antenne Punk Rock", "rock_antenne_punk_rock", True, "http://stream.rockantenne.de/punkrock", None, False),
    # ("Rock Antenne Deutschrock", "rock_antenne_deutschrock", True, "http://stream.rockantenne.de/deutschrock", None,False),
    # ("Rock Antenne Rock 'n Roll", "rock_antenne_rock_and_roll", True, "http://stream.rockantenne.de/rockandroll", None, False),
    # ("Rock Antenne Soft Rock", "rock_antenne_soft_rock", True, "http://stream.rockantenne.de/soft-rock", None, False),
    # ("Rock Antenne Young Stars", "rock_antenne_young_stars", True, "http://stream.rockantenne.de/young-stars", None, False),
    # ("Rock Antenne Cover Songs", "rock_antenne_cover_songs", True, "http://stream.rockantenne.de/coversongs", None, False),
    # ("Rock Antenne Munich City Nights", "rock_antenne_munich_city_nights", True, "http://stream.rockantenne.de/munich-city-nights", None, False),
    # ("Rock Antenne Xmas Rock", "rock_antenne_xmas_rock", True, "http://stream.rockantenne.de/xmas-rock", None, False),
    # # ("Long", "short", True, "m3u", None),
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

        print(_station)

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


def channels_dump_table():
    """usage
from player.init_db.manual_db_routines import channels_dump_table
channels_dump_table()
"""

    from player.models import Channel
    _channels = Channel.objects.all()
    for _channel in _channels:
        print(f'(\"{_channel.display_name}\", \"{_channel.display_name_short}\", \"{_channel.station}\", {_channel.is_enabled}, \"{_channel.url}\", \"{_channel.url_logo}\", {_channel.last_played}, {_channel.show_rds}),')


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
