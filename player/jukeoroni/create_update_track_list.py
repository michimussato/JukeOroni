import os
import logging
from django.db.models.deletion import ProtectedError
from player.jukeoroni.discogs import get_client, get_artist, get_album
from player.models import Artist, Album, Track as DjangoTrack
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    AUDIO_FILES,
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


# TODO: maybe use a better character
DELIMITER = ' - '


def create_update_track_list(box, directory, album_type):
    """

    Args:
        box: BaseBox object
        directory: full path, i. e.: /data/usb_hdd/media/audio/music. path can contain subdirectories that contain album directies
        album_type: music, audiobook or meditation
    """

    # TODO: filter image files, m3u etc.
    box.LOG.info(f'Generating updated track list for {box.box_type} ({directory})...')
    discogs_client = get_client()
    _files = []
    _albums = []
    _artists = []
    for path, dirs, files in os.walk(directory):
        # Remove part of path that can be retrieved from settings (MUSIC_DIR)
        # MUSIC_DIR:  /data/usb_hdd/media/audio/music
        # path:       /data/usb_hdd/media/audio/music/on_device/HIM - 2008 - Razorblade Romance [DSD128]/
        _path = os.path.relpath(path, directory)
        album = os.path.basename(_path)
        try:
            artist, year, title = album.split(DELIMITER)
        except ValueError:
            LOG.exception(f'Not a valid album path: {album}:')
            continue

        # COVER ARTIST
        # Artist can participate in Music and Meditation
        cover_online = None
        # TODO: if str(artist).lower() != 'soundtrack':  # Soundtracks have different artists, so no need to add artist cover
        query_artist = Artist.objects.filter(name__exact=artist)
        # TODO: maybe objects.get() is better because artist name is unique
        if bool(query_artist):
            LOG.info(f'Artist {query_artist} found in db...')
            model_artist = query_artist[0]  # name is unique, so index 0 is the correct model
            # if str(model_artist.name).lower() != 'soundtrack':
            if model_artist.cover_online is None:
                LOG.info(f'No online cover for artist {model_artist} defined. Trying to get one...')
                cover_online = get_artist(discogs_client, artist)
                if cover_online:
                    model_artist.cover_online = cover_online
                    model_artist.save()
        else:
            LOG.info(f'Artist {artist} not found in db; creating new entry...')
            cover_online = get_artist(discogs_client, artist)
            model_artist = Artist(name=artist, cover_online=cover_online)
            model_artist.save()

        if artist not in _artists:
            _artists.append(artist)
        # COVER ARTIST

        cover_root = _path
        jpg_path = os.path.join(cover_root, 'cover.jpg')
        png_path = os.path.join(cover_root, 'cover.png')
        if os.path.exists(os.path.join(directory, jpg_path)):
            img_path = jpg_path
        elif os.path.exists(os.path.join(directory, png_path)):
            img_path = png_path
        else:
            LOG.error(f'Missing cover: cover is None for album {album}')
            img_path = None

        # need to add artist too
        cover_online = None
        title_stripped = title.split(' [')[0]
        query_album = Album.objects.filter(artist=model_artist, album_title__exact=title, year__exact=year, album_type=album_type)

        # COVER ALBUM
        if bool(query_album):
            model_album = query_album[0]
            LOG.info(f'Album {model_album} found in DB.')
            model_album.cover = img_path
            if model_album.cover_online is None:
                LOG.info(f'No online cover for album {model_album} defined. Trying to get one...')
                cover_online = get_album(discogs_client, artist, title_stripped)
                if cover_online:
                    model_album.cover_online = cover_online
                else:
                    LOG.info('Could not find an online cover.')

        else:
            cover_online = get_album(discogs_client, artist, title_stripped)
            model_album = Album(artist=model_artist, album_title=title, year=year, cover=img_path, cover_online=cover_online, album_type=album_type)
            LOG.info(f'Album {model_album} not found in DB.')

        try:
            model_album.save()
            _albums.append(album)
            LOG.info(f'Album {model_album} correctly saved in DB.')
        except Exception:
            LOG.exception(f'Cannot save album model {title} by {artist}:')
        # COVER ALBUM

        for _file in files:
            if os.path.splitext(_file)[1] in AUDIO_FILES:
                file_path = os.path.join(_path, _file)
                query_track = DjangoTrack.objects.filter(audio_source__exact=file_path)
                if len(query_track) > 1:
                    LOG.warning(f'Track in DB multiple times: {file_path}')
                    for track in query_track:
                        track.delete()
                        LOG.warning(f'Track deleted: {track}')
                    query_track = []
                if len(query_track) == 1:
                    LOG.info(f'Track found in DB: {query_track}')
                    _edit = False
                    if not query_track[0].album == model_album:
                        query_track.update(album=model_album)
                        LOG.info('Track album updated in DB: {0}'.format(query_track[0]))
                    if not query_track[0].track_title == _file:
                        query_track.update(track_title=_file)
                        LOG.info('Track track_title updated in DB: {0}'.format(query_track[0]))
                else:
                    model_track = DjangoTrack.objects.create(album=model_album, audio_source=file_path, track_title=_file)
                    LOG.info('Track created in DB: {0}'.format(model_track))

                _files.append(file_path)

    # TODO:
    #  Maybe we blow the DB with the box_type check...
    #  let's see...

    # remove obsolete db objects:
    django_tracks = DjangoTrack.objects.filter(album__album_title=album_type)
    for django_track in django_tracks:
        if django_track.audio_source not in _files:  # and django_track.album.album_type == album_type:
            LOG.info(f'Removing track from DB: {django_track}')
            django_track.delete()
            LOG.info(f'Track removed from DB: {django_track}')

    django_albums = Album.objects.filter(album_type=album_type)
    for django_album in django_albums:
        if DELIMITER.join([django_album.artist.name, django_album.year, django_album.album_title]) not in _albums:
            LOG.info(f'Removing album from DB: {DELIMITER.join([django_album.artist.name, django_album.year, django_album.album_title])}')
            django_album.delete()
            LOG.info(f'Album removed from DB: {django_album}')

    # no special logic required. if artist is still connected, it
    # cannot be deleted
    django_artists = Artist.objects.all()
    for django_artist in django_artists:
        try:
            django_artist.delete()
            LOG.info(f'Artist removed from DB: {django_artist}')
        except ProtectedError:
            LOG.debug(f'Artist {django_artist} is still connected. Ignored...')

    LOG.info(f'Finished: {album_type} track list generated successfully: {len(_files)} tracks, {len(_albums)} albums and {len(_artists)} artists found')
############################################
