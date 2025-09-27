import json
from youtube_search import YoutubeSearch
import logging
from urllib.parse import urlparse, parse_qs

from pytubefix import YouTube
from urllib.error import HTTPError

logger = logging.getLogger("fetching-service")

def extract_video_id(url: str) -> str | None:

    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if 'v' in parse_qs(parsed_url.query):
                return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.hostname in ('youtu.be'):
            return parsed_url.path[1:]
        return None
    except Exception:
        return None
    
def get_video_details_from_url(url: str) -> dict[str, str]:
    video_id = extract_video_id(url)

    if not video_id:
        print(f"Invalid or unsupported YouTube URL: {url}")
        return None

    full_url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        yt = YouTube(full_url)
        
        video_title = yt.title
        video_length_seconds = yt.length

        minutes = video_length_seconds // 60
        seconds = video_length_seconds % 60
        video_duration = f"{minutes:01d}:{seconds:02d}"

        return {
            'url': full_url,
            'title': video_title,
            'duration': video_duration
        }
    
    except HTTPError as e:
        logger.error(f"HTTP Error: An HTTP error occurred while fetching video details ({e.code} - {e.reason}).")
        return None
    
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing URL: {e}")
        return None

def fetch_youtube_by_query(query: str):
    logger.info(f"Searching YouTube with query: {query}")
    try:
        results_json = YoutubeSearch(query, max_results=1).to_json()
        results_data = json.loads(results_json)
        videos = results_data.get('videos', [])

        if videos:
            first_video = videos[0]
            video_id = first_video.get('id')
            video_title = str(first_video.get('title'))
            video_duration = str(first_video.get('duration'))

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            return {
                'url': video_url,
                'title': video_title,
                'duration': video_duration
            }
        else:
            logger.error(f"No video results found for the query: '{query}'")
            return None

    except Exception as e: 
        logger.error(f"An unexpected error occured during the YouTube search: {e}")
        return None

