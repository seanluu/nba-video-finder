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

if __name__ == "__main__":
    print("running")