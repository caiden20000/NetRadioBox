"""Player class using VLC. Passing in a list of stations is required to start playback."""
import vlc

class Player:
    """Class for interacting with VLC. Passing in a list of stations is required to start playback."""
    def __init__(self, station_list: list[str] = None):
        station_list = station_list or [] # Default
        self.station_list = station_list
        self.current_station_number = 0
        self.is_playing = False
        # VLC related attributes
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media = None

    def _init_media(self, url: str) -> None:
        self.media = self.instance.media_new(url)
        self.player.set_media(self.media)

    def _get_meta(self, e_meta: vlc.Meta) -> str:
        if self.media is None or self.media.get_meta(e_meta) is None:
            return 'unknown'
        else:
            return self.media.get_meta(e_meta)

    def set_station_list(self, station_list: list[str]) -> None:
        self.station_list = station_list

    def play(self) -> None:
        print("Player starting playback")
        if self.media is None:
            self._init_media(self.station_list[self.current_station_number])
        self.player.play()
        self.is_playing = True

    def stop(self) -> None:
        print("Player stopping playback")
        self.player.stop()
        self.media = None
        self.is_playing = False

    def set_station(self, new_station_number: int) -> bool:
        if new_station_number < 0 or new_station_number >= len(self.station_list):
            return False
        if self.is_playing: self.player.stop()
        self.current_station_number = new_station_number
        self._init_media(self.station_list[new_station_number])
        if self.is_playing: self.player.play()
        print("Now playing station ", self.current_station_number)
        return True

    def scrub_station(self, distance: int) -> None:
        wrapped_station_number = (self.current_station_number + distance) % len(self.station_list)
        self.set_station(wrapped_station_number)

    def get_station_number(self) -> int:
        return self.current_station_number
    def get_station_title(self) -> str:
        return self._get_meta(vlc.Meta.Title)
    def get_station_track(self) -> str:
        return self._get_meta(vlc.Meta.NowPlaying)
    def get_station_count(self) -> int:
        return len(self.station_list)
