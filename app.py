import os
import requests
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2
from nba_api.stats.static import teams
from dotenv import load_dotenv

load_dotenv()

# Load team data from NBA API static data
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

# NBA API headers, keep minimal so it treats us like a user
NBA_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://stats.nba.com/'
}

def search_games_by_date(team1, team2, game_date):
    try:
        team1_data = get_team_info(team1)
        team2_data = get_team_info(team2)
        
        if not team1_data or not team2_data:
            return []
        
        games_df = leaguegamefinder.LeagueGameFinder(team_id_nullable=team1_data['id'].get_data_frames()[0])
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
            
        # Filter by player name
        player_events = events_df[
            events_df['PLAYER1_NAME'].str.contains(player_name, case=False, na=False)
        ]
        
        if len(player_events) == 0:
            return None
            
        # Combine descriptions for easier matching
        home_desc = player_events['HOMEDESCRIPTION'].fillna('')
        visitor_desc = player_events['VISITORDESCRIPTION'].fillna('')
        combined_desc = home_desc + ' ' + visitor_desc
        
        # Match event type
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
            # Game winners: made shots in 4th quarter or overtime
            events = player_events[
                (player_events['EVENTMSGTYPE'] == 1) & 
                (player_events['PERIOD'] >= 4)
            ]
        else:
            # Default to any made shot
            events = player_events[player_events['EVENTMSGTYPE'] == 1]
            
        # Return the last matching event
        return events.iloc[-1] if len(events) > 0 else None
        
    except Exception:
        return None
    
if __name__ == "__main__":
    print("running")