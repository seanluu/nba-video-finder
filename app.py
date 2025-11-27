import os
import json
import requests
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2
from nba_api.stats.static import teams
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import googleapiclient.discovery
from dotenv import load_dotenv

load_dotenv()

TEAM_DATA = []
for team in teams.get_teams():
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

def parse_nba_highlight(query):
    try:
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not api_key:
            print("ERROR: GOOGLE_GEMINI_API_KEY not set in environment")
            return {}
        client = genai.Client(api_key=api_key)
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
            model="gemini-2.0-flash",
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
        
    except Exception as e:
        print(f"ERROR in parse_nba_highlight: {type(e).__name__}: {str(e)}")
        return {}
    
def get_video_url(game_id, event_id):
    """get the video URL for a specific event from NBA API"""
    try:
        response = requests.get(
            f'https://stats.nba.com/stats/videoeventsasset?GameEventID={event_id}&GameID={game_id}',
            headers=NBA_HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            video_urls = data.get('resultSets', {}).get('Meta', {}).get('videoUrls', [])
            if video_urls and video_urls[0].get('lurl'):
                return video_urls[0]['lurl']
        
        return None
    except Exception:
        return None

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
        
        return [{ 'game_id': row['GAME_ID'], 'game_date': row['GAME_DATE'], 'matchup': row['MATCHUP']}
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
    """Find a specific type of event for a player in the play-by-play data"""
    try:
        if events_df is None or len(events_df) == 0:
            return None
            
        player_events = events_df[
            events_df['PLAYER1_NAME'].str.contains(player_name, case=False, na=False)
        ]
        
        if len(player_events) == 0:
            return None
            
        home_desc = player_events['HOMEDESCRIPTION'].fillna('')
        visitor_desc = player_events['VISITORDESCRIPTION'].fillna('')
        combined_desc = home_desc + ' ' + visitor_desc
        
        event_type_lower = event_type.lower() if event_type else ''
        
        if 'block' in event_type_lower:
            events = player_events[combined_desc.str.contains('BLOCK', case=False, na=False)]
        elif '3' in event_type_lower or 'three' in event_type_lower:
            events = player_events[combined_desc.str.contains('3PT', case=False, na=False)]
        elif 'dunk' in event_type_lower:
            events = player_events[combined_desc.str.contains('DUNK', case=False, na=False)]
        elif 'free throw' in event_type_lower:
            events = player_events[combined_desc.str.contains('FREE THROW', case=False, na=False)]
        elif 'game winner' in event_type_lower:
            events = player_events[
                (player_events['EVENTMSGTYPE'] == 1) & 
                (player_events['PERIOD'] >= 4)
            ]
        else:
            # default to any made shot
            events = player_events[player_events['EVENTMSGTYPE'] == 1]
            
        # return the last matching event
        return events.iloc[-1] if len(events) > 0 else None
        
    except Exception:
        return None
    
def find_nba_video_clip(query):
    """Main function that orchestrates the entire video finding process"""
    try:
        parsed_query = parse_nba_highlight(query)
        if not parsed_query:
            return {"success": False, "error": "Failed to parse query"}
        
        player_name = parsed_query.get('player')
        player_team = parsed_query.get('player_team')
        opponent_team = parsed_query.get('opponent')
        game_date = parsed_query.get('game_date')
        event_type = parsed_query.get('event_type', 'highlight')
        
        if not player_name or not player_team or not opponent_team:
            return {"success": False, "error": "Missing required information"}
        
        games = search_games_by_date(player_team, opponent_team, game_date)
        if not games:
            return {"success": False, "error": f"No games found"}
        
        for game in games:
            events = get_game_events(game['game_id'])
            if events is None:
                continue
            
            event = find_event_by_type(events, player_name, event_type)
            if event is None:
                continue
            
            video_url = get_video_url(game['game_id'], event['EVENTNUM'])
            if video_url:
                clip = {
                    "title": f"{player_name} - {event_type}",
                    "game_date": game['game_date'],
                    "matchup": game['matchup'],
                    "period": int(event.get('PERIOD', 1)),
                    "time_remaining": event.get('PCTIMESTRING', ''),
                    "video_url": video_url,
                    "source": "nba"
                }
                return {
                    "success": True,
                    "clips": [clip]
                }
        
        return {"success": False, "error": "No video found"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    
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
    
def search_youtube(query):
    """Search YouTube as fallback when NBA video isn't available"""
    try:
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        if not youtube_api_key:
            return None
        
        youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=youtube_api_key)
        
        search_response = youtube.search().list(
            part='snippet',
            q=query,
            type='video',
            maxResults=1,
            order='relevance'
        ).execute()
        
        if search_response.get('items'):
            video_id = search_response['items'][0]['id']['videoId']
            return f"https://youtu.be/{video_id}"
        
        return None
    except Exception:
        return None
    
if __name__ == "__main__":
    pass