# NBA Video Finder

NBA Video Finder is a web app that lets you search for NBA video clips using natural language queries; just describe the moment you're looking for specifically like "steph curry game winner against the suns", and the app will find the relevant video clips from official NBA sources or YouTube.

## Installation

**Prerequisites:** Python 3.8+, Node.js 20+, MongoDB (optional, for caching)

```bash
# Clone the repository
git clone https://github.com/seanluu/nba-video-finder.git
cd nba-video-finder

# Set up backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install fastapi uvicorn

# Set up frontend
cd frontend
npm install
cd ..
```

Open http://localhost:3000

### Set up API Keys

1. **Google Gemini API Key:**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add `GOOGLE_GEMINI_API_KEY=your_key_here` to `.env` file

2. **YouTube API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Enable YouTube Data API v3
   - Create credentials (API Key)
   - Add `YOUTUBE_API_KEY=your_key_here` to `.env` file

3. **MongoDB (Optional):**
   - Add `MONGODB_URI=mongodb://localhost:27017/` to `.env` file for caching

## Usage

1. Start the backend server: `python api.py` (runs on http://localhost:5001)
2. Start the frontend: `cd frontend && npm start` (runs on http://localhost:3000)
3. Open http://localhost:3000 in your browser
4. Enter a natural language query like "steph curry game winner"
5. View the matching video clips with game details and direct links

## Features

- **Natural Language Search**: Describe NBA moments in plain English
- **AI-Powered Parsing**: Uses Google Gemini AI to understand search intent
- **Multiple Video Sources**: Searches official NBA archives and YouTube
- **Search History**: View and reuse recent searches (stored locally)
- **Game Details**: Period, time remaining, matchup, and game date for each clip
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: React 19, TypeScript, React Scripts
- **Backend**: FastAPI, Python 3.8+
- **APIs**: NBA API, Google Gemini AI, YouTube Data API v3
- **Database**: MongoDB
