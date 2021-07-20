# definitions
# tuple[0]: display_name
# tuple[1]: display_name_short
# tuple[2]: is_enabled
# tuple[3]: url
# tuple[4]: url_logo


channel_list = [
    ("BOBs 100", "100", True, "http://streams.radiobob.de/100/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs 101", "101", True, "http://streams.radiobob.de/101/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs 2000er", "2000er", True, "http://streams.radiobob.de/2000er/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Blues", "blues", True, "http://streams.radiobob.de/blues/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs 80s Rock", "bob-80srock", True, "http://streams.radiobob.de/bob-80srock/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs 90s Rock", "bob-90srock", True, "http://streams.radiobob.de/bob-90srock/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs AC/DC", "bob-acdc", True, "http://streams.radiobob.de/bob-acdc/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Alternative", "bob-alternative", True, "http://streams.radiobob.de/bob-alternative/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Best of Rock", "bob-bestofrock", True, "http://streams.radiobob.de/bob-bestofrock/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Chillout", "bob-chillout", True, "http://streams.radiobob.de/bob-chillout/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Christmas", "bob-christmas", False, "http://streams.radiobob.de/bob-christmas/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBS Classic Rock", "bob-classicrock", True, "http://streams.radiobob.de/bob-classicrock/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Deutsch Rock", "bob-deutsch", True, "http://streams.radiobob.de/bob-deutsch/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Festival", "bob-festival", True, "http://streams.radiobob.de/bob-festival/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Grunge", "bob-grunge", True, "http://streams.radiobob.de/bob-grunge/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Hard Rock", "bob-hardrock", True, "http://streams.radiobob.de/bob-hardrock/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Harte Saite", "bob-hartesaite", True, "http://streams.radiobob.de/bob-hartesaite/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Kuschel Rock", "bob-kuschelrock", False, "http://streams.radiobob.de/bob-kuschelrock/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Live", "bob-live", True, "http://streams.radiobob.de/bob-live/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Metal", "bob-metal", True, "http://streams.radiobob.de/bob-metal/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs National", "bob-national", True, "http://streams.radiobob.de/bob-national/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Punk", "bob-punk", True, "http://streams.radiobob.de/bob-punk/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Queen", "bob-queen", False, "http://streams.radiobob.de/bob-queen/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Rockabilly", "bob-rockabilly", True, "http://streams.radiobob.de/bob-rockabilly/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Rock Hits", "bob-rockhits", True, "http://streams.radiobob.de/bob-rockhits/mp3-192/streams.radiobob.de/play.m3u", None),
    ("bob-shlive", "bob-shlive", True, "http://streams.radiobob.de/bob-shlive/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Singer-Songwriter", "bob-singersong", True, "http://streams.radiobob.de/bob-singersong/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Wacken", "bob-wacken", True, "http://streams.radiobob.de/bob-wacken/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Boss Hoss", "bosshoss", True, "http://streams.radiobob.de/bosshoss/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Country", "country", True, "http://streams.radiobob.de/country/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Death Metal", "deathmetal", True, "http://streams.radiobob.de/deathmetal/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Fury In The Slaughterhouse", "fury", True, "http://streams.radiobob.de/fury/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Gothic Metal", "gothic", True, "http://streams.radiobob.de/gothic/mp3-192/streams.radiobob.de/play.m3u", None),
    ("Live Hessen-Mitte", "live-hessen-mitte", True, "http://streams.radiobob.de/live-hessen-mitte/mp3-192/streams.radiobob.de/play.m3u", None),
    ("Live National-Mitte", "live-national-mitte", True, "http://streams.radiobob.de/live-national-mitte/mp3-192/streams.radiobob.de/play.m3u", None),
    ("Live NRM-Mitte", "live-nrw-mitte", True, "http://streams.radiobob.de/live-nrw-mitte/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/06/bob_livestream-rock-n-pop_600x600.png"),
    ("live-sh-mitte", "live-sh-mitte", True, "http://streams.radiobob.de/live-sh-mitte/mp3-192/streams.radiobob.de/play.m3u", None),
    ("live-sh-nordwest", "live-sh-nordwest", True, "http://streams.radiobob.de/live-sh-nordwest/mp3-192/streams.radiobob.de/play.m3u", None),
    ("live-sh-ost", "live-sh-ost", True, "http://streams.radiobob.de/live-sh-ost/mp3-192/streams.radiobob.de/play.m3u", None),
    ("live-sh-sued", "live-sh-sued", True, "http://streams.radiobob.de/live-sh-sued/mp3-192/streams.radiobob.de/play.m3u", None),
    ("BOBs Metal Core", "metalcore", True, "http://streams.radiobob.de/metalcore/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metalcore_600x600-1.png"),
    ("BOBs Metallica", "metallica", True, "http://streams.radiobob.de/metallica/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_metallica_600x600.png"),
    ("BOBs Mittelalter", "mittelalter", True, "http://streams.radiobob.de/mittelalter/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_mittelalter-rock_600x600.png"),
    ("BOBs Newcomer", "newcomer", True, "http://streams.radiobob.de/newcomer/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_newcomer_600x600.png"),
    ("BOBs Progressive Rock", "progrock", True, "http://streams.radiobob.de/progrock/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/04/bob_prog-rock_600x600.png"),
    ("BOBs Der Dunkle Parabelritter", "ritter", True, "http://streams.radiobob.de/ritter/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_parabelritter_600x600.png"),
    ("BOBs Rock Party", "rockparty", True, "http://streams.radiobob.de/rockparty/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_rockparty_600x600.png"),
    ("BOBs Sammet Rockshow", "sammet", True, "http://streams.radiobob.de/sammet/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_tobias-sammet-rockshow_600x600.png"),
    ("BOBs Southern Rock", "southernrock", True, "http://streams.radiobob.de/southernrock/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2021/01/bob_southern-rock_600x600.png"),
    ("BOBs Symphonic Metal", "symphmetal", True, "http://streams.radiobob.de/symphmetal/mp3-192/streams.radiobob.de/play.m3u", "http://aggregatorservice.loverad.io/wp-content/uploads/2020/07/bob_symphonic-metal_600x600.jpg"),
    ("SRF 3", "srf_3", True, "http://stream.srg-ssr.ch/drs3/aacp_96.m3u", None),
    ("SRF 2 Kultur", "srf_2", True, "http://stream.srg-ssr.ch/drs2/aacp_96.m3u", None),
    ("SRF 1", "srf_1", True, "http://stream.srg-ssr.ch/drs1/aacp_96.m3u", None),
    ("SRF 4 News", "srf_4", True, "http://stream.srg-ssr.ch/drs4news/aacp_96.m3u", None),
    ("SRF Virus", "srf_virus", True, "http://stream.srg-ssr.ch/drsvirus/aacp_96.m3u", None),
    ("SRF Swiss Classic", "srf_swiss_classic", True, "http://stream.srg-ssr.ch/rsc_de/aacp_96.m3u", None),
    ("SRF Swiss Jazz", "srf_swiss_jazz", True, "http://stream.srg-ssr.ch/rsj/aacp_96.m3u", None),
    ("SRF Swiss Pop", "srf_swiss_pop", True, "http://stream.srg-ssr.ch/rsp/aacp_96.m3u", None),
    ("SRF Couleur 3", "couleur_3", True, "http://stream.srg-ssr.ch/couleur3/aacp_96.m3u", None),
]


def main():
    from radio.models import Channel
    for channel in channel_list:
        c = Channel(display_name=channel[0], display_name_short=channel[1], is_enabled=channel[2], url=channel[3], url_logo=channel[4])
        c.save()
