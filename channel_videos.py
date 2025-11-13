#!/usr/bin/env python3
"""
YouTube Channel Video Fetcher

A Python script that uses the official YouTube Data API v3 to fetch all video IDs
associated with a particular YouTube channel.

Requirements:
- Google API key
- google-api-python-client library

Usage:
    python channel_videos.py --channel-id CHANNEL_ID --api-key YOUR_API_KEY
    python channel_videos.py --channel-url https://www.youtube.com/@channelname
"""

import json
import sys
import time
import re
import logging
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

MAX_QUERY_SIZE = 50

# Module-level logger
logger = logging.getLogger(__name__)


class YouTubeChannelVideoFetcher:
    """Fetches video IDs from YouTube channels using the YouTube Data API v3."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the YouTubeChannelVideoFetcher.
        
        Args:
            api_key: YouTube Data API key
        """
        self.api_key = api_key
        self.youtube = None
        self._initialize_api()
    
    def _initialize_api(self):
        """Initialize the YouTube API client."""
        try:
            if self.api_key:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            else:
                raise ValueError("api_key must be provided")
                
        except Exception as e:
            logger.error(f"  Error initializing YouTube API: {e}")
            sys.exit(1)
    
    def get_channel_id_from_username(self, username: str) -> Optional[str]:
        """
        Get channel ID from username or channel URL.
        
        Args:
            username: YouTube username, channel URL, or handle
            
        Returns:
            Channel ID if found, None otherwise
        """
        logger.info(f"  Getting channel ID for username \"{username}\"")
        try:
            # Handle different URL formats
            if username.startswith('@'):
                # Handle new @username format
                handle = username[1:]  # Remove @ symbol
                request = self.youtube.channels().list(
                    part='id',
                    forHandle=handle
                )
                response = request.execute()
                
                if response['items']:
                    return response['items'][0]['id']
                    
            elif 'youtube.com' in username:
                # Extract username/handle from URL
                if '/@' in username:
                    handle = username.split('/@')[-1].split('/')[0].split('?')[0]
                    request = self.youtube.channels().list(
                        part='id',
                        forHandle=handle
                    )
                    response = request.execute()
                    
                    if response['items']:
                        return response['items'][0]['id']
                elif '/channel/' in username:
                    # Direct channel ID in URL
                    return username.split('/channel/')[-1].split('/')[0].split('?')[0]
                elif '/c/' in username or '/user/' in username:
                    # Legacy username format
                    username_part = username.split('/')[-1].split('?')[0]
                    request = self.youtube.channels().list(
                        part='id',
                        forUsername=username_part
                    )
                    response = request.execute()
                    
                    if response['items']:
                        return response['items'][0]['id']
            else:
                # Assume it's already a channel ID or username
                if len(username) == 24 and username.isalnum():  # Channel ID format
                    return username
                else:
                    # Try as username
                    request = self.youtube.channels().list(
                        part='id',
                        forUsername=username
                    )
                    response = request.execute()
                    
                    if response['items']:
                        return response['items'][0]['id']
                        
        except HttpError as e:
            logger.error(f"  Error fetching channel ID: {e}")
            
        return None
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict]:
        """
        Get basic information about the channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Dictionary containing channel information
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                return None
            
            channel = response['items'][0]
            return {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'custom_url': channel['snippet'].get('customUrl'),
                'published_at': channel['snippet']['publishedAt'],
                'subscriber_count': channel['statistics'].get('subscriberCount', 0),
                'video_count': channel['statistics'].get('videoCount', 0),
                'view_count': channel['statistics'].get('viewCount', 0)
            }
        except HttpError as e:
            logger.error(f"  Error fetching channel info: {e}")
            return None
    
    def get_video_ids(self, channel_id: str, max_videos: int = 100) -> List[str]:
        """
        Fetch video IDs from a YouTube channel up to a specified maximum.
        
        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum number of videos to fetch (default: 100)
            
        Returns:
            List of video IDs (up to max_videos)
        """
        video_ids = []
        next_page_token = None
        
        logger.info(f"  Fetching up to {max_videos} videos for channel ID: {channel_id}")
        
        try:
            while len(video_ids) < max_videos:
                # Calculate how many videos to request in this batch
                remaining_videos = max_videos - len(video_ids)
                batch_size = min(MAX_QUERY_SIZE, remaining_videos)
                
                # Get videos from the channel
                request = self.youtube.search().list(
                    part='id',
                    channelId=channel_id,
                    type='video',
                    maxResults=batch_size,
                    pageToken=next_page_token,
                    order='date'  # Order by upload date (newest first)
                )
                
                response = request.execute()
                
                # Extract video IDs
                for item in response['items']:
                    if item['id']['kind'] == 'youtube#video':
                        video_ids.append(item['id']['videoId'])
                        
                        # Stop if we've reached the maximum
                        if len(video_ids) >= max_videos:
                            break
                
                # Check if there are more pages and we haven't reached the limit
                next_page_token = response.get('nextPageToken')
                if not next_page_token or len(video_ids) >= max_videos:
                    break
                
                # Rate limiting - YouTube API has quotas
                time.sleep(0.1)
                
                # Progress indicator
                if len(video_ids) % 50 == 0:
                    logger.info(f"  Fetched {len(video_ids)} video IDs so far...")
                
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("  Error: API quota exceeded or access denied. Please check your API key and quota.")
            elif e.resp.status == 404:
                logger.error("  Error: Channel not found.")
            else:
                logger.error(f"  Error fetching videos: {e}")
        
        logger.info(f"  Successfully fetched {len(video_ids)} video IDs")
        return video_ids

    def get_all_video_ids(self, channel_id: str) -> List[str]:
        """
        Fetch all video IDs from a YouTube channel.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            List of video IDs
        """
        all_video_ids = []
        next_page_token = None
        
        logger.info(f"  Fetching videos for channel ID: {channel_id}")
        
        try:
            while True:
                # Get videos from the channel
                request = self.youtube.search().list(
                    part='id',
                    channelId=channel_id,
                    type='video',
                    maxResults=MAX_QUERY_SIZE,
                    pageToken=next_page_token,
                    order='date'  # Order by upload date (newest first)
                )
                
                response = request.execute()
                
                # Extract video IDs
                for item in response['items']:
                    if item['id']['kind'] == 'youtube#video':
                        all_video_ids.append(item['id']['videoId'])
                
                # Check if there are more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                
                # Rate limiting - YouTube API has quotas
                time.sleep(0.1)
                
                # Progress indicator
                if len(all_video_ids) % 100 == 0:
                    logger.info(f"  Fetched {len(all_video_ids)} video IDs so far...")
                
        except HttpError as e:
            if e.resp.status == 403:
                logger.error("  Error: API quota exceeded or access denied. Please check your API key and quota.")
            elif e.resp.status == 404:
                logger.error("  Error: Channel not found.")
            else:
                logger.error(f"  Error fetching videos: {e}")
        
        logger.info(f"  Successfully fetched {len(all_video_ids)} video IDs")
        return all_video_ids
    
    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Get detailed information for a list of video IDs.
        
        Args:
            video_ids: List of YouTube video IDs
            
        Returns:
            List of video detail dictionaries
        """
        video_details = []
        
        # YouTube API allows up to 50 video IDs per request
        batch_size = 50
        
        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            
            try:
                request = self.youtube.videos().list(
                    part='snippet,statistics',
                    id=','.join(batch)
                )
                response = request.execute()
                
                for video in response['items']:
                    video_details.append({
                        'id': video['id'],
                        'title': video['snippet']['title'],
                        'description': video['snippet']['description'],
                        'published_at': video['snippet']['publishedAt'],
                        'view_count': video['statistics'].get('viewCount', 0),
                        'like_count': video['statistics'].get('likeCount', 0),
                        'comment_count': video['statistics'].get('commentCount', 0),
                        'duration': video['snippet'].get('duration', ''),
                        'thumbnail_url': video['snippet']['thumbnails'].get('default', {}).get('url', '')
                    })
                
                # Rate limiting
                time.sleep(0.1)
                
            except HttpError as e:
                logger.error(f"  Error fetching video details for batch: {e}")
                continue
        
        return video_details
    
    def save_video_ids_to_file(self, video_ids: List[str], filename: str):
        """
        Save video IDs to a text file.
        
        Args:
            video_ids: List of video IDs
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for video_id in video_ids:
                    f.write(f"{video_id}\n")
            logger.info(f"  Video IDs saved to {filename}")
        except Exception as e:
            logger.error(f"  Error saving video IDs: {e}")
    
    def save_video_details_to_file(self, video_details: List[Dict], filename: str):
        """
        Save video details to a JSON file.
        
        Args:
            video_details: List of video detail dictionaries
            filename: Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(video_details, f, indent=2, ensure_ascii=False)
            logger.info(f"  Video details saved to {filename}")
        except Exception as e:
            logger.error(f"  Error saving video details: {e}")


def get_channel_videos(channel_identifier: str, max_videos: int, output_ids_file: Optional[str] = None, 
                      output_details_file: Optional[str] = None, 
                      include_details: bool = False):
    """
    Main function to get all videos from a YouTube channel.
    
    Args:
        channel_identifier: Channel ID, username, or URL
        output_ids_file: File to save video IDs (optional)
        output_details_file: File to save video details (optional)
        include_details: Whether to fetch detailed video information
    """
    try:
        from config import YOUTUBE_API_KEY
    except ImportError:
        logger.error("  Error: YOUTUBE_API_KEY not found in config.py")
        sys.exit(1)
    
    # Initialize the fetcher
    fetcher = YouTubeChannelVideoFetcher(api_key=YOUTUBE_API_KEY)
    
    # Get channel ID
    logger.info("  Resolving channel identifier...")
    channel_id = fetcher.get_channel_id_from_username(channel_identifier)
    
    if not channel_id:
        logger.error(f"  Error: Could not find channel with identifier: {channel_identifier}")
        sys.exit(1)
    
    logger.info(f"  Found channel ID: {channel_id}")
    
    # Fetch all video IDs
    video_ids = fetcher.get_video_ids(channel_id, max_videos=50)
    
    if not video_ids:
        logger.warning("  No videos found or error occurred.")
        return
    
    # Save video IDs if requested
    if output_ids_file:
        fetcher.save_video_ids_to_file(video_ids, output_ids_file)
    
    # Get video details if requested
    if include_details:
        logger.info("  Fetching video details...")
        video_details = fetcher.get_video_details(video_ids)
        
        if output_details_file:
            fetcher.save_video_details_to_file(video_details, output_details_file)
    
    if include_details:
        logger.info(f"  Video details fetched: {len(video_details)}")
    
    return video_ids



if __name__ == '__main__':
    """Unit test: Get all the video ids from my channel"""

    from setup_logging import setup_logging
    logger = setup_logging()
    logger.info(" Running unit test for youtube_comments.py")

    channel_identifier = "@TheCounselofTrent"
    
    video_ids = get_channel_videos(
        channel_identifier=channel_identifier,
        max_videos=50
    )
    
    if video_ids:
        logger.info(f"\nFirst 10 video IDs:")
        for i, video_id in enumerate(video_ids[:10]):
            logger.info(f"{i+1}. {video_id}")