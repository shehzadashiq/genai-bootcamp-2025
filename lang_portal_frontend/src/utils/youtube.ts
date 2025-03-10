/**
 * Extracts a YouTube video ID from a URL or returns the ID if directly provided.
 * Supports various YouTube URL formats:
 * - https://www.youtube.com/watch?v=VIDEO_ID
 * - https://youtu.be/VIDEO_ID
 * - https://youtube.com/shorts/VIDEO_ID
 * - VIDEO_ID (direct)
 */
export function extractVideoId(input: string): string | null {
  if (!input) return null;

  // Try to parse as URL first
  try {
    const url = new URL(input);
    
    // Handle youtube.com/watch?v= format
    if (url.hostname.includes('youtube.com') && url.pathname === '/watch') {
      return url.searchParams.get('v');
    }
    
    // Handle youtu.be/ format
    if (url.hostname === 'youtu.be') {
      return url.pathname.slice(1);
    }
    
    // Handle youtube.com/shorts/ format
    if (url.hostname.includes('youtube.com') && url.pathname.startsWith('/shorts/')) {
      return url.pathname.slice(8);
    }
    
    return null;
  } catch (e) {
    // Not a URL, check if it's a direct video ID
    const videoIdPattern = /^[a-zA-Z0-9_-]{11}$/;
    if (videoIdPattern.test(input)) {
      return input;
    }
    return null;
  }
}
