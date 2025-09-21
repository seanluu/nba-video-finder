import React, { useState, useEffect } from 'react';
import { Clip, SearchHistoryItem } from './types';

// Simple NBA clip finder app - All components in one file
const API_BASE = 'http://localhost:5001';
const HISTORY_KEY = 'nba_search_history';

function App() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  const handleSearch = async (searchQuery: string) => {
    setLoading(true);
    setError(null);
    setClips([]);

    try {
      const response = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });

      const data = await response.json();

      if (data.success) {
        setClips(data.clips);

      } else {
        setError(data.error || 'Something went wrong');
      }
    } catch (err) {
      setError('Failed to connect to server. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
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
        <h2 style={styles.searchTitle}>Find NBA Clips</h2>
        
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
              <div style={styles.clipInfo}>
                <div style={styles.clipTitle}>{clip.title}</div>
                <div style={styles.clipDescription}>
                  Period {clip.period} • {clip.time_remaining}
                </div>
                <a 
                  href={clip.video_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  Watch Video
                </a>
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
  searchTitle: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '20px'
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
    padding: '20px'
  },
  clipInfo: {

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
  }
};

export default App;