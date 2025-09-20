// src/App.tsx - Everything in one file first
import React, { useState } from 'react';
import { Clip } from './types';
import { colors } from './colors';

function App() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock data for testing
  const mockClips: Clip[] = [
    {
      title: "LeBron James Amazing Dunk",
      game_date: "2016-06-08",
      matchup: "Lakers vs Warriors",
      period: 3,
      time_remaining: "2:45",
      video_url: "https://youtube.com/watch?v=0bXg9nofz4I",
      thumbnail_url: "https://img.youtube.com/vi/0bXg9nofz4I/maxresdefault.jpg",
      source: "YouTube"
    }
  ];

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1>NBA Clip Finder</h1>
      </div>

      {/* Search Form */}
      <div style={styles.searchForm}>
        <input 
          type="text" 
          placeholder="Search for NBA clips..."
          style={styles.searchInput}
        />
        <button style={styles.searchBtn}>Search</button>
      </div>

      {/* Results */}
      <div style={styles.results}>
        {mockClips.map((clip, index) => (
          <div key={index} style={styles.clipCard}>
            <div style={styles.clipThumbnail}>
              <img src={clip.thumbnail_url} alt={clip.title} style={styles.thumbnailImg} />
            </div>
            <div style={styles.clipInfo}>
              <h3 style={styles.clipTitle}>{clip.title}</h3>
              <p style={styles.clipDescription}>
                Period {clip.period} • {clip.time_remaining}
              </p>
              <div style={styles.clipMeta}>
                <span>{clip.matchup} • {clip.game_date}</span>
                <a href={clip.video_url} target="_blank" style={styles.watchBtn}>
                  Watch
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={styles.footer}>
        <p>NBA Clip Finder - Find your favorite moments</p>
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
    marginBottom: '30px'
    // literally centers "NBA Clip Finder" towards the center
  },
  searchForm: {
    display: 'flex', // moves search button all the way to the right of the search query box
    marginBottom: '30px',
    gap: '10px'
    // give space between the search box and clip thumbnail
  },
  searchInput: { 
    flex: 1, // extend search box all the way to right of container
    padding: '12px',
    border: '1px solid #ddd', 
    borderRadius: '6px' 
  },
  searchBtn: {
    padding: '12px 24px', // give it a rectangular button look
    background: colors.primary, // use blue look
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer'
  },
  results: {
    display: 'grid', // would make clip take up full width of container
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', // makes clip container even smaller (sort of 1/3 of container)
    gap: '20px',
    marginBottom: '30px',
  },
  clipCard: {
    background: colors.background,
    borderRadius: '12px', // rounded corners
    overflow: 'hidden' as const, // clips thumbnail corners
    border: `1px solid ${colors.border}` // slight gray border around clip card
  },
  clipThumbnail: {
    width: '100%', // fit the whole width
    height: '200px', // less of the thumbnail height
    background: '#f5f5f5' // fallback background if thumbnail fails
  },
  thumbnailImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const // cover the whole thumbnail area
  },
  clipInfo: {
    padding: '20px' // space between thumbnail and text info
  },
  clipTitle: {
    fontSize: '18px',
    fontWeight: 'bold',
    marginBottom: '10px',
    color: colors.text
  },
  clipDescription: {
    color: colors.textLight,
    marginBottom: '15px',
    fontSize: '14px'
  },
  clipMeta: {
    display: 'flex', // flexbox to space out the text and watch button
    justifyContent: 'space-between',
    alignItems: 'center',
    fontSize: '14px',
    color: colors.textLight
  },
  watchBtn: {
    background: colors.primary, // blue color for button
    color: 'white',
    padding: '8px 16px', // top-right-bottom-left padding
    border: 'none',
    borderRadius: '6px', // rounds the button corners
    textDecoration: 'none',
    fontSize: '14px'
  },
  footer: {
    textAlign: 'center' as const,
    color: colors.textLight,
    marginTop: '50px' // push footer down
  }
};

export default App;