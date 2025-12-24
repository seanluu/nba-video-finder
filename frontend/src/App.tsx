import React, { useState, useEffect } from 'react';
import { Clip, SearchHistoryItem } from './types';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5001';
const HISTORY_KEY = 'nba_search_history';

function App() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [query, setQuery] = useState('');

  // localStorage for search history
  useEffect(() => {
    const savedHistory = localStorage.getItem(HISTORY_KEY);
    if (savedHistory) {
      try {
        setSearchHistory(JSON.parse(savedHistory));
      } catch (error) {
      }
    }
  }, []);

  useEffect(() => {
    if (searchHistory.length > 0) {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(searchHistory));
    }
  }, [searchHistory]);

  const addToHistory = (query: string) => {
    const trimmedQuery = query.trim();
    setSearchHistory(prev => [
      { 
        id: Date.now().toString(), 
        query: trimmedQuery, 
        timestamp: Date.now(), 
        resultCount: 0 
      },
      ...prev.filter(item => item.query !== trimmedQuery)
    ].slice(0, 20));
  };

  const handleSearch = async (searchQuery: string) => {
    setLoading(true);
    setError(null);
    setClips([]);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 second timeout

      const response = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.detail || errorData.error || `Server error: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setClips(data.clips);
        addToHistory(searchQuery);
      } else {
        setError(data.error || 'Something went wrong');
        addToHistory(searchQuery);
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setError('Request timed out. The search is taking too long. Please try again or use a more specific query.');
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Failed to connect to server. Make sure the backend is running.');
      }
      addToHistory(searchQuery);
    } finally {
      setLoading(false);
    }
  };

  const handleHistorySearch = (searchQuery: string) => {
    handleSearch(searchQuery);
    setShowHistory(false);
  };

  const clearHistory = () => {
    setSearchHistory([]);
    localStorage.removeItem(HISTORY_KEY);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedQuery = query.trim();
    if (trimmedQuery) handleSearch(trimmedQuery);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>🏀 NBA Clip Finder</h1>
        <p style={styles.subtitle}>Find amazing NBA moments using natural language search</p>
      </div>

      <div style={styles.searchCard}>
        <div style={styles.searchHeader}>
          <h2 style={styles.searchTitle}>Find NBA Clips</h2>
          <button style={styles.historyBtn} onClick={() => setShowHistory(!showHistory)}>
            History ({searchHistory.length})
          </button>
        </div>
        
        <form style={styles.searchForm} onSubmit={handleSubmit}>
          <input
            type="text"
            style={styles.searchInput}
            placeholder="Try: 'LeBron dunks' or 'Steph Curry game winner'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
          />
          <button type="submit" style={styles.searchBtn} disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
        
        {showHistory && searchHistory.length > 0 && (
          <div style={styles.historyDropdown}>
            <div style={styles.historyHeader}>
              <span>Recent Searches</span>
              <button onClick={clearHistory}>Clear</button>
            </div>
            {searchHistory.map((item) => (
              <div 
                key={item.id} 
                style={styles.historyItem}
                onClick={() => handleHistorySearch(item.query)}
              >
                {item.query}
              </div>
            ))}
          </div>
        )}
        
        {loading && (
          <div style={{ textAlign: 'center', color: '#666', margin: '20px 0' }}>
            Searching for clips...
          </div>
        )}
      </div>

      {error && (
        <div style={styles.error}>
          {error}
        </div>
      )}

      <div style={styles.results}>
        {clips.length === 0 ? (
          <p style={styles.noResults}>
            No clips found. Try a different search!
          </p>
        ) : (
          clips.map((clip, index) => (
            <div key={index} style={styles.clipCard}>
              <div style={styles.clipThumbnail}>
                {clip.thumbnail_url ? (
                  <img
                    src={clip.thumbnail_url}
                    alt={clip.title}
                    style={styles.thumbnailImg}
                  />
                ) : (
                  <div>🏀</div>
                )}
              </div>
              <div style={styles.clipInfo}>
                <div style={styles.clipTitle}>{clip.title}</div>
                <div style={styles.clipDescription}>
                  Period {clip.period} • {clip.time_remaining}
                </div>
                <div style={styles.clipMeta}>
                  <span>{clip.matchup || 'NBA Video'} • {clip.game_date || 'Unknown Date'}</span>
                  <a 
                    href={clip.video_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={styles.watchBtn}
                  >
                    Watch
                  </a>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

  const styles = {
    container: {
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '20px'
    },
    header: {
      textAlign: 'center' as const,
      marginBottom: '40px'
    },
    title: {
      fontSize: '2.5rem',
      fontWeight: 'bold',
      marginBottom: '10px'
    },
    subtitle: {
      fontSize: '1.1rem',
      color: '#666'
    },
    searchCard: {
      background: 'white',
      borderRadius: '12px',
      padding: '30px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      border: '1px solid #ddd',
      marginBottom: '30px'
    },
    searchHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '20px'
    },
    searchTitle: {
      fontSize: '24px',
      fontWeight: 'bold',
      margin: 0
    },
    historyBtn: {
      background: '#f5f5f5',
      border: '1px solid #ddd',
      borderRadius: '4px',
      padding: '8px 16px',
      fontSize: '14px',
      cursor: 'pointer'
    },
    searchForm: {
      display: 'flex',
      gap: '10px',
      marginBottom: '20px'
    },
    searchInput: {
      flex: 1,
      padding: '12px 16px',
      border: '1px solid #ddd',
      borderRadius: '8px',
      fontSize: '16px'
    },
    searchBtn: {
      padding: '12px 24px',
      background: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      fontSize: '16px',
      cursor: 'pointer'
    },
    historyDropdown: {
      background: 'white',
      borderRadius: '8px',
      marginTop: '10px',
      border: '1px solid #ddd',
      maxHeight: '200px',
      overflowY: 'auto' as const
    },
    historyHeader: {
      padding: '10px',
      borderBottom: '1px solid #eee',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      background: '#f9f9f9'
    },
    historyItem: {
      padding: '10px',
      cursor: 'pointer',
      borderBottom: '1px solid #f0f0f0'
    },
    error: {
      color: 'red',
      textAlign: 'center' as const,
      margin: '20px 0'
    },
    results: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
      gap: '20px'
    },
    noResults: {
      textAlign: 'center' as const,
      color: '#666',
      gridColumn: '1 / -1',
      fontSize: '16px'
    },
    clipCard: {
      background: 'white',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      border: '1px solid #ddd',
      overflow: 'hidden' as const
    },
    clipThumbnail: {
      width: '100%',
      height: '200px',
      background: '#f5f5f5',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '3rem'
    },
    thumbnailImg: {
      width: '100%',
      height: '100%',
      objectFit: 'cover' as const
    },
    clipInfo: {
      padding: '20px'
    },
    clipTitle: {
      fontSize: '18px',
      fontWeight: 'bold',
      marginBottom: '10px'
    },
    clipDescription: {
      color: '#666',
      marginBottom: '15px',
      fontSize: '14px'
    },
    clipMeta: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      fontSize: '14px',
      color: '#666'
    },
    watchBtn: {
      background: '#007bff',
      color: 'white',
      padding: '8px 16px',
      borderRadius: '6px',
      textDecoration: 'none',
      fontSize: '14px'
    }
  };

export default App;