from jukeoroni._secrets import GENIUS_TOKEN
import logging
import os
import re
from player.jukeoroni.settings import Settings
from jukeoroni._secrets import GENIUS_TOKEN
import lyricsgenius


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


def get_lyrics(artist, track):
    try:
        track = os.path.splitext(track)[0]
        track = re.sub('^\d+', '', track)

        genius = lyricsgenius.Genius(GENIUS_TOKEN)
        _artist = genius.search_artist(artist.name, max_songs=0)
        song = genius.search_song(title=track, artist=_artist.songs)

        lyrics = genius.lyrics(song_id=song.id)
        # lyrics = lyrics.replace('\n', '&#013;')
        lyrics = lyrics.replace('\n', '<br>')
        lyrics = lyrics.replace('Lyrics[', '<br>Lyrics<br>[')
        lyrics = lyrics.replace('[', '<b>[')
        lyrics = lyrics.replace(']', ']</b>')
        # lyrics = lyrics.replace('You might also like', '')
        # lyrics = lyrics.replace('Embed', '')

        LOG.debug(f'LyricsGenius search result: {artist.name} ({_artist.id}) - {track} - {song.id} - {lyrics}')

    except Exception as error:
        LOG.exception(f'LyricsGenius error {artist.name} ({_artist.id}) {track}: {error}')

        lyrics = error

    return lyrics
