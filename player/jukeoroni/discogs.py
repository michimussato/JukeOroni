import logging
import discogs_client
import jukeoroni._secrets as secrets
from unidecode import unidecode


LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


# https://github.com/joalla/discogs_client
# https://python3-discogs-client.readthedocs.io


def get_client():
    d = discogs_client.Client('JukeOroni/0.0.1', user_token=secrets.DISCOGS_USER_TOKEN)
    return d


def get_artist(client, artist):
    results = client.search(artist, type='artist')
    if not results:
        results = client.search(unidecode(artist), type='artist')
    try:
        cover_square = results[0].images[0]['uri150']
        return cover_square
    except Exception as err:
        LOG.info(f'discogs could not look up artist: {err}')
        return None


def get_album(client, artist, album):
    results = client.search(album, type='release', artist=artist)
    if not results:
        results = client.search(album, type='release', artist=unidecode(artist))
    try:
        cover_square = results[0].images[0]['uri150']
        return cover_square
    except Exception as err:
        LOG.info(f'discogs could not look up album {album} (by {artist}): {err}')
        return None
