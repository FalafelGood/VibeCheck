"""
For a given YouTube channel, get the videos, get the comments for each video, 
run Vader analysis on the comments and then calculate some stats
"""

import logging
import sys
import os
from typing import Optional, List
from datetime import datetime
from channel_videos import get_channel_videos
from youtube_comments import get_video_comments
from comment_analysis import get_polarity_scores
from vaderscores import VaderScores
from setup_logging import setup_logging

def rate_channel_by_comments(channel_id: str, max_comments_per_vid: int, max_videos: int, tags: Optional[List[str]] = None):
  logger = logging.getLogger(__name__)
  logger.info(f"Starting analysis for channel: {channel_id}")
  videos = get_channel_videos(channel_id, max_videos=max_videos)
  logger.info(f"Found {len(videos)} videos for channel {channel_id}")

  scores = VaderScores(channel_id, tags)

  # Limit to max_vids videos
  for video_id in videos[:max_videos]:
    comments = get_video_comments(video_id, max_comments = max_comments_per_vid)
    if comments:
      for comment in comments:
      # for comment in comments[:max_comments_per_vid]:
        score = get_polarity_scores(comment['text'])
        like_count = comment['like_count']
        scores.add_score(score, like_count)


  scores.report_all()
  # return scores.weighted_average_scores(), scores.kindness(), scores.volatility()

def save_data(channel_id, data):
  pass


if __name__ == '__main__':
  logger = setup_logging()
  for channel_id in ["@SkyDoesShorts", "@PhilosophyTube", "@DaveyWaveyRaw", "@TylerOakley"]:
    rate_channel_by_comments(channel_id, max_comments_per_vid=1000, max_videos=50, tags=["queer"])
  