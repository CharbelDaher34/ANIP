"""
Sentiment Analysis Model Definition.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


SENTIMENT_LABELS = ["positive", "neutral", "negative"]


def create_sentiment_model():
    """
    Create a sentiment analysis pipeline.
    
    Returns:
        sklearn Pipeline with TF-IDF vectorizer and Logistic Regression
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            stop_words='english',
            min_df=2
        )),
        ('classifier', LogisticRegression(
            max_iter=1000,
            C=1.0,
            class_weight='balanced'
        ))
    ])
    
    return pipeline


def get_sentiment_labels():
    """Return list of sentiment labels."""
    return SENTIMENT_LABELS


