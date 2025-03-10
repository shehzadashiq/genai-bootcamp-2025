/**
 * Extracts a YouTube video ID from a URL or returns the ID if directly provided.
 * Supports various YouTube URL formats:
 * - https://www.youtube.com/watch?v=VIDEO_ID
 * - https://youtu.be/VIDEO_ID
 * - https://youtube.com/shorts/VIDEO_ID
 * - VIDEO_ID (direct)
 */
export function extractVideoId(input: string): string | null;
