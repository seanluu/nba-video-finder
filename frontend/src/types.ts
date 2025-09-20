export interface Clip {
    title: string,
    game_date: string,
    matchup: string,
    period: number,
    time_remaining: string,
    video_url: string,
    thumbnail_url?: string,
    source: string
}

export interface SearchResult {
    success: boolean,
    clips: Clip[],
    error?: string
}

export interface SearchHistoryItem {
    id: string;
    query: string;
    timestamp: number;
    resultCount: number;
}