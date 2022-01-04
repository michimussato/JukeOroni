import os
import logging
from player.jukeoroni.discogs import get_client, get_artist, get_album
from player.models import Artist, Album, Track as DjangoTrack
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    # MUSIC_DIR,
    AUDIO_FILES,
    # ALBUM_TYPE_MUSIC,
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


def create_update_track_list(box, directory, album_type):
    # TODO: filter image files, m3u etc.
    box.LOG.info('Generating updated track list for {0} ({1})...'.format(box.box_type, directory))
    discogs_client = get_client()
    _files = []
    _albums = []
    _artists = []
    for path, dirs, files in os.walk(directory):
        # if not self.on:
        #     LOG.warning('JukeBox is turned off.')
        #     return

        # Remove part of path that can be retrieved from settings (MUSIC_DIR)
        # MUSIC_DIR:  /data/usb_hdd/media/audio/music
        # path:       /data/usb_hdd/media/audio/music/on_device/HIM - 2008 - Razorblade Romance [DSD128]/
        _path = os.path.relpath(path, directory)
        # _path =
        album = os.path.basename(_path)
        try:
            # TODO: maybe use a better character
            artist, year, title = album.split(' - ')
        except ValueError:
            # with open(FAULTY_ALBUMS, 'a+') as f:
            #     f.write(album + '\n')
            # TODO: store this somewhere to fix it
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
            # with open(MISSING_COVERS_FILE, 'a+') as f:
            #     f.write(cover_root + '\n')
            LOG.info(f'cover is None: {album}')
            img_path = None

        # need to add artist too
        cover_online = None
        title_stripped = title.split(' [')[0]
        query_album = Album.objects.filter(artist=model_artist, album_title__exact=title, year__exact=year)


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

            if not query_album[0].album_type == album_type:
                query_album.update(album_type=album_type)

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
        if django_track.audio_source not in _files \
                and django_track.album.album_type == album_type:
            LOG.info(f'Removing track from DB: {django_track}')
            django_track.delete()
            LOG.info(f'Track removed from DB: {django_track}')

    django_albums = Album.objects.filter(album_type=album_type)
    for django_album in django_albums:
        occurrences = [i for i in _albums if str(django_album.album_title).lower() in i.lower()]
        if len(occurrences) == 0:
            LOG.info(f'Removing album from DB: {django_album}')
            django_album.delete()
            LOG.info(f'Album removed from DB: {django_album}')

    django_artists = Artist.objects.all()
    for django_artist in django_artists:
        if django_artist.name not in _artists:
            LOG.info(f'Removing artist from DB: {django_artist}')
            try:
                django_artist.delete()
                LOG.info(f'Artist removed from DB: {django_artist}')
            except Exception:
                LOG.exception('Could not delete Artist from DB:')

    LOG.info(f'Finished: {album_type} track list generated successfully: {len(_files)} tracks, {len(_albums)} albums and {len(_artists)} artists found')
############################################
