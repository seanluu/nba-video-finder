import os
import json
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2
from nba_api.stats.static import teams
import google.genai as genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import googleapiclient.discovery
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MAX_PARALLEL_WORKERS = 3
REQUEST_TIMEOUT_SECONDS = 8
REQUEST_MAX_RETRIES = 2

def get_mongo_client():
    try:
        return MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'))
    except Exception:
        return None

_CACHE_COLLECTION = None

def get_cache_collection():
    global _CACHE_COLLECTION
    if _CACHE_COLLECTION is not None:
        return _CACHE_COLLECTION

    client = get_mongo_client()
    if not client:
        return None

    db = client['nba_video_finder']
    collection = db['search_cache']
    try:
        collection.create_index("query", unique=True)
        collection.create_index("created_at", expireAfterSeconds=86400)
    finally:
        _CACHE_COLLECTION = collection
    return _CACHE_COLLECTION

TEAM_DATA = []
for team in teams.get_teams():
    # we build list of possible names for each team
    names = [team["full_name"]]
    if team.get("nickname"):
        names.append(team["nickname"])
    if team.get("city") and team.get("nickname"):
        names.append(f"{team['city']} {team['nickname']}")
    
    TEAM_DATA.append({
        "id": team["id"],
        "abbr": team["abbreviation"],
        "names": names
    })


def normalize_team_name(name):
    return name.lower().strip().replace("the ", "")

def get_team_info(team_name):
    if not team_name:
        return None
    
    for team in TEAM_DATA:
        for name in team["names"]:
            if normalize_team_name(name) == normalize_team_name(team_name):
                return {"id": team["id"], "abbr": team["abbr"]}
    return None

NBA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://stats.nba.com/'
}

def get_cached_result(query):
    cache_collection = get_cache_collection()
    if cache_collection is None:
        return None
    
    try:
        result = cache_collection.find_one({"query": query.lower().strip()})
        if result:
            return result['result']
        return None
    except Exception:
        return None

def set_cached_result(query, result):
    cache_collection = get_cache_collection()
    if cache_collection is None:
        return
    
    try:
        cache_collection.replace_one(
            {"query": query.lower().strip()},
            {
                "query": query.lower().strip(),
                "result": result,
                "created_at": datetime.utcnow()
            },
            upsert=True
        )
    except Exception:
        pass


def _get_with_retries(url, headers=None, timeout=REQUEST_TIMEOUT_SECONDS):
    last_exc = None
    for attempt in range(REQUEST_MAX_RETRIES + 1):
        try:
            return requests.get(url, headers=headers, timeout=timeout)
        except Exception as exc:
            last_exc = exc
            if attempt < REQUEST_MAX_RETRIES:
                time.sleep(0.75 * (2 ** attempt))
            else:
                break
    raise last_exc if last_exc else RuntimeError("request failed")


def parse_nba_highlight(query):
    try:
        client = genai.Client(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
        google_search_tool = Tool(google_search=GoogleSearch())
        
        prompt = """Find this NBA game and return JSON:

{{
  "player": "full player name (resolve nicknames like KD to Kevin Durant, Steph to Stephen Curry)",
  "player_team": "player's team at the time of the game",
  "opponent": "opponent team name", 
  "event_type": "one of: block, 3-pointer, dunk, free throw, game winner, highlight",
  "game_date": "YYYY-MM-DD"
}}

Search for the most relevant information about this game; infer the correct event type from the query.
"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt + f"\n\nQuery: {query}",
            config=GenerateContentConfig(tools=[google_search_tool]),
        )
        
        response_text = "".join(part.text for part in response.candidates[0].content.parts).strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        start = response_text.find('{')
        end = response_text.rfind('}')
        if start != -1 and end > start:
            json_text = response_text[start:end + 1]
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                pass
        return {}
        
    except Exception:
        return {}


def _handle_fallback(query, youtube_result, error_msg="Search failed"):
    if youtube_result:
        clip = {
            "title": youtube_result["title"],
            "game_date": youtube_result.get("publish_date", "Unknown"),
            "matchup": "YouTube Video",
            "video_url": youtube_result["url"],
            "thumbnail_url": youtube_result.get("thumbnail_url"),
            "source": "youtube"
        }
        return {"success": True, "clips": [clip]}
    return {"success": False, "error": error_msg, "clips": []}

def _process_game_for_clip(game, player_name, opponent_team, game_date, event_type):
    try:
        events = get_game_events(game['game_id'])
        if events is None or len(events) == 0:
            return None
        
        shot = find_event_by_type(events, player_name, event_type)
        if shot is None:
            return None
        
        nba_result = get_video_url(game['game_id'], shot['EVENTNUM'])
        if nba_result:
            video_url = nba_result["url"]
            thumbnail_url = nba_result.get("thumbnail_url")
            source = "nba"
        else:
            youtube_result = search_youtube(f"{player_name} {event_type} {opponent_team} {game_date}")
            if youtube_result:
                video_url = youtube_result["url"]
                thumbnail_url = youtube_result.get("thumbnail_url")
                source = "youtube"
            else:
                return None
        
        # Create title
        home_desc = str(shot.get('HOMEDESCRIPTION') or '').strip()
        visit_desc = str(shot.get('VISITORDESCRIPTION') or '').strip()
        title = home_desc or visit_desc or f"{player_name} {event_type}"
        
        return {
            "title": title,
            "game_date": game['game_date'],
            "matchup": game['matchup'],
            "period": int(shot.get('PERIOD', 0)),
            "time_remaining": str(shot.get('PCTIMESTRING', 'Unknown')),
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "source": source
        }
    except Exception:
        return None

def _process_games_parallel(games, player_name, opponent_team, game_date, event_type):
    if not games:
        return None
    
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as executor:
        futures = [
            executor.submit(_process_game_for_clip, game, player_name, opponent_team, game_date, event_type)
            for game in games
        ]

        for future in as_completed(futures, timeout=15):
            try:
                result = future.result()
                if result:
                    return result
            except Exception:
                continue
    return None

def find_nba_video_clip(query):
    try:
        cached_result = get_cached_result(query)
        if cached_result:
            return cached_result
        
        parsed_query = parse_nba_highlight(query)
        if not parsed_query:
            return _handle_fallback(query, search_youtube(query), "Failed to parse query")
        
        player_name = parsed_query.get('player')
        player_team = parsed_query.get('player_team')
        opponent_team = parsed_query.get('opponent')
        game_date = parsed_query.get('game_date')
        
        if not player_name or not player_team or not opponent_team:
            return _handle_fallback(query, search_youtube(query), "Missing required information")
        
        games = search_games_by_date(player_team, opponent_team, game_date)
        if not games:
            return _handle_fallback(query, search_youtube(query), f"No games found between {player_team} and {opponent_team} on {game_date}")
        
        clip = _process_games_parallel(games, player_name, opponent_team, game_date, parsed_query.get('event_type', 'highlight'))
        if clip:
            result = {"success": True, "clips": [clip]}
            set_cached_result(query, result)
            return result
        
        return {"success": False, "error": f"No matching video clips found for query: '{query}'", "clips": []}
        
    except Exception as e:
        return {"success": False, "error": str(e), "clips": []}

def search_games_by_date(team1, team2, game_date):
    try:
        team1_data = get_team_info(team1)
        team2_data = get_team_info(team2)
        
        if not team1_data or not team2_data:
            return []
        
        games_df = leaguegamefinder.LeagueGameFinder(team_id_nullable=team1_data['id']).get_data_frames()[0]
        matching_games = games_df[
            (games_df['GAME_DATE'] == game_date) & 
            (games_df['MATCHUP'].str.contains(team2_data['abbr'], case=False, na=False))
        ]
        
        return [{'game_id': row['GAME_ID'], 'game_date': row['GAME_DATE'], 'matchup': row['MATCHUP']} 
                for _, row in matching_games.iterrows()]
        
    except Exception:
        return []

def get_game_events(game_id):
    try:
        events_df = playbyplayv2.PlayByPlayV2(game_id=game_id).get_data_frames()[0]
        return events_df
    except Exception:
        return None

def find_event_by_type(events_df, player_name, event_type):
    try:
        et = (event_type or '').lower()
        df = events_df.copy()

        # filter by player
        if 'PLAYER1_NAME' not in df.columns:
            return None
        df = df[df['PLAYER1_NAME'].str.contains(player_name or '', case=False, na=False)]
        if len(df) == 0:
            return None

        # combine home/visitor descriptions
        home_desc = df['HOMEDESCRIPTION'].fillna('') if 'HOMEDESCRIPTION' in df.columns else ''
        visit_desc = df['VISITORDESCRIPTION'].fillna('') if 'VISITORDESCRIPTION' in df.columns else ''
        combined = (home_desc + ' ' + visit_desc)
        df = df.assign(_COMBINED_DESC=combined)

        # event type matching
        if 'game winner' in et or 'winner' in et:
            # game winner: made shots in 4th quarter or overtime
            events = df[(df.get('EVENTMSGTYPE') == 1) & (df.get('PERIOD') >= 4)]
        elif 'free throw' in et or 'freethrow' in et:
            events = df[df['_COMBINED_DESC'].str.contains('FREE THROW', case=False, na=False)]
        elif '3' in et:
            events = df[df['_COMBINED_DESC'].str.contains('3PT', case=False, na=False)]
        elif 'dunk' in et:
            events = df[df['_COMBINED_DESC'].str.contains('DUNK', case=False, na=False)]
        elif 'block' in et:
            events = df[df['_COMBINED_DESC'].str.contains('BLOCK', case=False, na=False)]
        else:
            made_shots = df[df.get('EVENTMSGTYPE') == 1]
            if len(made_shots) == 0:
                return None
            late_shots = made_shots[made_shots.get('PERIOD') >= 4]
            events = late_shots if len(late_shots) > 0 else made_shots

        return events.iloc[-1] if len(events) > 0 else None
    except Exception:
        return None

def get_video_url(game_id, event_id):
    try:
        response = _get_with_retries(
            f'https://stats.nba.com/stats/videoeventsasset?GameEventID={event_id}&GameID={game_id}',
            headers=NBA_HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            data = response.json()
            video_urls = data.get('resultSets', {}).get('Meta', {}).get('videoUrls', [])
            if video_urls and video_urls[0].get('lurl'):
                video_data = video_urls[0]
                video_url = video_data['lurl']
                thumbnail_url = video_data.get('lth')
                return {"url": video_url, "thumbnail_url": thumbnail_url}
        
        return None
    except Exception:
        return None

def search_youtube(query=""):
    try:
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        if not youtube_api_key:
            return None
        
        youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=youtube_api_key)
        
        search_query = query.strip()
        
        search_response = youtube.search().list(
            part='snippet', q=search_query, type='video', maxResults=1, order='relevance'
        ).execute()
        
        if search_response.get('items'):
            item = search_response['items'][0]
            video_id = item['id']['videoId']
            youtube_url = f"https://youtu.be/{video_id}"
            video_title = item['snippet']['title']
            thumbnail_url = item['snippet']['thumbnails'].get('high', {}).get('url')
            publish_date = item['snippet']['publishedAt'][:10]
            return {"url": youtube_url, "title": video_title, "thumbnail_url": thumbnail_url, "publish_date": publish_date}
        
        return None
        
    except Exception:
        return None
