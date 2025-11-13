from typing import Optional, Dict, List
import json
import os
from datetime import datetime

class VaderScores:
  def __init__(self, channel_id: str, tags: Optional[List[str]] = None):
    self.channel_id = channel_id
    self.tags = tags
    self.pos_scores = []
    self.neu_scores = []
    self.neg_scores = []
    self.weights = [] # Multiplicative weight for the score
  
  def add_score(self, score: Dict, likes: int):
    self.pos_scores.append(score['pos'])
    self.neu_scores.append(score['neu'])
    self.neg_scores.append(score['neg'])
    self.weights.append(likes + 1) # Multiplicative factor (likes start at zero, so we add 1 to compensate)

  def average_scores(self):
    """Calculates the average score"""
    avg_pos = sum(self.pos_scores) / len(self.pos_scores)
    avg_neu = sum(self.neu_scores) / len(self.neu_scores)
    avg_neg = sum(self.neg_scores) / len(self.neg_scores)
    return {"avg_pos": round(avg_pos, 3), 
            "avg_neu": round(avg_neu, 3), 
            "avg_neg": round(avg_neg, 3)}
  
  def weighted_average_scores(self):
    """Calculates the weighted average score using comment likes as weights"""
    if not self.weights or sum(self.weights) == 0:
      # If weights are not defined for some reason, return an unweighted average
      print("WARNING -- weights in VaderScores were improperly initialized. \"weighted_average_scores\" is defaulting to \"average_scores\"")
      return self.average_scores()
    
    total_weight = sum(self.weights)
    weighted_pos = sum(pos * weight for pos, weight in zip(self.pos_scores, self.weights)) / total_weight
    weighted_neu = sum(neu * weight for neu, weight in zip(self.neu_scores, self.weights)) / total_weight
    weighted_neg = sum(neg * weight for neg, weight in zip(self.neg_scores, self.weights)) / total_weight
    
    return {"w_ave_pos": round(weighted_pos, 3), 
            "w_ave_neu": round(weighted_neu, 3), 
            "w_ave_neg": round(weighted_neg, 3)}

  def kindness(self, P, N):
    """
    Calculates the `kindness` metric. 
    P: weighted average for comment positivity
    N: weighted average for comment negativity
    """
    return ((P-N)/(P+N))

  def volatility(self, P, N, Z):
    """
    Calculates the `volatility metric:
    P: weighted average for comment positivity,
    N: weighted average for comment negativity,
    Z: weighted average for comment neutrality.
    """
    return 1/(Z + abs(P-N))

  def report_all(self):
    num_comments = len(self.pos_scores)
    average_scores = self.average_scores()
    weighted_average_scores = self.weighted_average_scores()
    P = weighted_average_scores['w_ave_pos']
    N = weighted_average_scores['w_ave_neg']
    Z = weighted_average_scores['w_ave_neu']
    kindness = self.kindness(P, N)
    volatility = self.volatility(P, N, Z)

    results = {
      'channel-id': self.channel_id,
      'tags': self.tags,
      'timestamp': datetime.now().isoformat(),
      'num-comments-analyzed': num_comments,
      'average-score': average_scores,
      'weighted-average-score': weighted_average_scores, 
      'kindness': kindness,
      'volatility': volatility
    }

    # Ensure the directory exists
    os.makedirs('channel-ratings', exist_ok=True)
    
    # Open file in write mode to create it if it doesn't exist
    with open(f'channel-ratings/{self.channel_id}.json', 'w') as file:
      json.dump(results, file, indent=4)

    print(f"\nChannel report for {self.channel_id}")
    print("*" * 25)
    print(f"Number of comments analyzed == {num_comments}")
    print(f"Average scores: {average_scores}")
    print(f"Weighted average scores: {weighted_average_scores}")
    print(f"Kindness rating: {kindness}")
    print(f"Volatility rating: {volatility}")
    print("*" * 25 + '\n')
    return



if __name__ == "__main__":
    print("Running unit test for vaderscores.py")
    sample_scores = [
        {'pos': 0.8, 'neu': 0.2, 'neg': 0.0},
        {'pos': 0.0, 'neu': 0.3, 'neg': 0.7}, 
        {'pos': 0.1, 'neu': 0.7, 'neg': 0.2}       
    ]
    sample_like_counts = [5, 1, 0]
    VS = VaderScores()
    for score, like_count in zip(sample_scores, sample_like_counts):
        VS.add_score(score, like_count)

    print("VaderScore object initialized without error")
    print(f"Average scores for sample data: {VS.average_scores()}")
    print(f"Weighted average scores for sample data: {VS.weighted_average_scores()}")
