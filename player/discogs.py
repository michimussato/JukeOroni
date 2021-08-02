import discogs_client
import jukeoroni.secrets as secrets


# https://github.com/joalla/discogs_client
# https://python3-discogs-client.readthedocs.io


def get_client():
    d = discogs_client.Client('JukeOroni/0.0.1', user_token=secrets.DISCOGS_USER_TOKEN)
    return d
    # results = d.search('The Violin Player', type='release', artist='Vanessa Mae')
    # cover = results[0].images[0]['uri']
    # cover_square = results[0].images[0]['uri150']
    # print(cover)
    # print(cover_square)


def get_artist(client, artist):
    results = client.search(artist, type='artist')
    try:
        cover_square = results[0].images[0]['uri150']
        return cover_square
    except Exception as err:
        print(err)
        return None


def get_album(client, artist, album):
    results = client.search(album, type='release', artist=artist)
    try:
        cover_square = results[0].images[0]['uri150']
        return cover_square
    except Exception as err:
        print(err)
        return None
