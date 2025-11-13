import logging
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
# from typing import Dict

# Graceful download check for vader_lexicon (nltk data file needed for sentiment analysis)
try:
  nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
  print("comment_analysis.py: vader_lexicon not found -- installing now")
  nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

def get_polarity_scores(comment):
  scores = sia.polarity_scores(comment)
  # print(f"Comment: \"{comment}\" has polarity score of: {scores} ")
  return scores

if __name__ == '__main__':
  comment = "Bro this sucks."
  scores = get_polarity_scores(comment)
  print(f"comment: {comment} -- polarity scores: {scores}")
