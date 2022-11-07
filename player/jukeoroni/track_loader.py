import os
import time
import logging
from player.jukeoroni.settings import Settings
from player.jukeoroni.box_track import JukeboxTrack


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


def _track_loader_task(box):
    try:
        while box.on:
            try:
                LOG.debug(f'{box.box_type:<18}: {len(box.tracks)} of {Settings.MAX_CACHED_FILES} tracks cached. Queue: {box.tracks}')

                # This is to check that the source files did not disappear in the meantime
                # Remove them if they did
                box.tracks = [track for track in box.tracks if os.path.isfile(track.path)]

                if len(box.tracks) < Settings.MAX_CACHED_FILES:
                    loading_track = box.get_next_track()

                    if loading_track is None:
                        LOG.warning(f'{box.box_type:<18}: Got "None" track. Retrying...')
                        time.sleep(1.0)
                        continue
                    if not os.path.isfile(os.path.join(box.audio_dir, loading_track.audio_source)):
                        LOG.warning(
                            f'{box.box_type:<18}: Track audio_source ({os.path.join(box.audio_dir, loading_track.audio_source)}) does not exist on filesystem. Retrying...')
                        time.sleep(1.0)
                        continue

                    LOG.info(f'{box.box_type:<18}: Next track OK: {loading_track}')

                    box.loading_track = JukeboxTrack(django_track=loading_track, cached=Settings.CACHE_TRACKS)
                    box.loading_track.cache()
                    box.loading_track.cache_online_covers()

                    if box.loading_track is not None:
                        if not box.loading_track.killed:
                            loading_track_copy = box.loading_track
                            box.tracks.append(loading_track_copy)
                            # TODO: make sure not to add tracks that are
                            #  already in the queue
                            # self.tracks = list(set(self.tracks))  # buggy!! Fucks up order somehow
                        box.loading_track = None

                time.sleep(1.0)
            except Exception as e:
                LOG.exception(f'{box.box_type:<18}: {e}')
                raise e
    except Exception as e:
        LOG.exception(f'{box.box_type:<18}: {e}')
        raise e
