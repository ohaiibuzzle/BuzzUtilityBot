import pyyoutube
import spotipy
import configparser
import asyncio
from .youtube_dl_source import YouTubeDLSingleSource

config = configparser.ConfigParser()
config.read('runtime/config.cfg')

spotify_creds_manager = spotipy.SpotifyClientCredentials(config['Credentials']['spotify_web_api_cid'], 
                                                            config['Credentials']['spotify_web_api_sec'])

def spotify_to_track_name(playlist_url: str):
    """
    Convert one Spotify Playlist to individual track name for searching
    :param playlist_url: The URL to a playlist
    """
    spotify_api = spotipy.Spotify(client_credentials_manager=spotify_creds_manager)
    playlist = spotify_api.user_playlist_tracks(playlist_id=playlist_url)
    
    tracks = []
    
    for track in playlist['items']:
        search_name = track['track']['name']
        for artist in track['track']['artists']:
            search_name += f" {artist['name']}"
        
        tracks.append(search_name)

    return tracks

def track_names_to_yt_api(tracks: list):
    """
    Use the YouTube Data V3 API (via pyyoutube) to search for matching songs
    :param tracks: a list of tracks
    """
    yt_tracks = []
    youtube_api = pyyoutube.Api(api_key=config['Credentials']['youtube_data_v3_key'])
    for track in tracks:
        this_video_id = youtube_api.search_by_keywords(q=track, search_type='video').items[0].to_dict()['id']['videoId']
        yt_tracks.append('https://youtu.be/'+this_video_id)

    return yt_tracks

async def async_spotify_playlist_to_track_list(playlist_url: str, loop):
    """Convert a Spotify playlist to a list of track name, asynchronously

    Args:
        playlist_url (str): The playlist URL
        loop (asyncio.BaseEventLoop): an asyncio event loop

    Returns:
        list: A track name list
    """
    loop = loop or asyncio.get_event_loop()
    return await loop.run_in_executor(None, spotify_to_track_name, playlist_url)

async def track_names_to_yt_alt(tracks:list, loop):
    """
    Use youtube-dl to search for matching songs
    :param tracks: a list of tracks
    :param loop: an asyncio event loop
    :return: YouTube video links
    """
    yt_tracks = []
    
    for track in tracks:
        result = await YouTubeDLSingleSource.list_from_query(track, loop=loop, amount=1)
        yt_tracks.append(result['entries'][0]['webpage_url'])
    
    return yt_tracks

async def async_spotify_to_yt(playlist_url: str, loop = None):
    """
    Use youtube-dl to search for matching songs, asynchronously
    :param playlist_url: The URL to a playlist
    :param loop: an asyncio event loop
    """
    loop = loop or asyncio.get_event_loop()
    track_list = await loop.run_in_executor(None, spotify_to_track_name, playlist_url)
    return await loop.run_in_executor(None, track_names_to_yt_api, track_list)

def single_track_to_yt_url(track_name:str) -> str:
    """
    Use the YouTube Data V3 API (via pyyoutube) to search for matching song
    :param track_name: A track name
    :param loop: an asyncio event loop
    :return: A YouTube Link
    """
    youtube_api = pyyoutube.Api(api_key=config['Credentials']['youtube_data_v3_key'])
    this_video_id = youtube_api.search_by_keywords(q=track_name, search_type='video').items[0].to_dict()['id']['videoId']
    return 'https://youtu.be/'+this_video_id

async def async_single_track_to_yt(track_name:str, loop=None):
    """
    Use the YouTube Data V3 API (via pyyoutube) to search for matching song, asynchronously
    :param track_name: A track name
    :param loop: an asyncio event loop
    :return: A YouTube Link
    """
    loop = loop or asyncio.get_event_loop()
    return await loop.run_in_executor(None, single_track_to_yt_url, track_name)


async def async_single_track_to_yt_alt(track: str, loop=None):
    """
    Use youtube-dl to search for matching song, asynchronously
    :param track: A track name
    :param loop: an asyncio event loop
    :return: A YouTube Link
    """
    loop = loop or asyncio.get_event_loop()
    result = await YouTubeDLSingleSource.list_from_query(track, loop=loop, amount=1)
    return result['entries'][0]['webpage_url']

def single_spotify_track_to_track_name(spotify_track_url: str) -> str:
    """
    Extract the track info from a single Spotify track link 

    Args:
        spotify_track_url (str): Spotify URI

    Returns:
        str: Track Name + Artist
    """
    spotify_api = spotipy.Spotify(client_credentials_manager=spotify_creds_manager)
    this_track = spotify_api.track(spotify_track_url)
    name = this_track['name']
    for artist in this_track['artists']:
        name += f" {artist['name']}"
    return name

async def async_single_spotify_track_to_yt(spotify_track_url: str, loop = None) -> str:
    loop = loop or asyncio.get_event_loop()
    track_name = await loop.run_in_executor(None, single_spotify_track_to_track_name, spotify_track_url)
    return await async_single_track_to_yt(track_name=track_name, loop=loop)

def spotify_album_to_track_names(spotify_album_url: str) -> list:
    """
    Convert a Spotify Playlist to track names

    Args:
        spotify_album_url (str): Spotify Album Url

    Returns:
        list: List of track names
    """
    spotify_api = spotipy.Spotify(client_credentials_manager=spotify_creds_manager)
    album = spotify_api.album(spotify_album_url)

    tracks = []
    
    for track in album['tracks']['items']:
        search_name = track['name']
        for artist in track['artists']:
            search_name += f" {artist['name']}"

        tracks.append(search_name)

    return tracks

async def async_spotify_album_to_track_names(spotify_album_url: str, loop=None) -> list:
    loop = loop or asyncio.get_event_loop()
    return await loop.run_in_executor(None, spotify_album_to_track_names, spotify_album_url)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    ## UNIT TEST HERE