"""
Topic Classification Model Definition.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


TOPICS = [
    "politics",
    "technology",
    "sports",
    "business",
    "entertainment",
    "health",
    "science",
    "world"
]


def create_classification_model():
    """
    Create a topic classification pipeline.
    
    Returns:
        sklearn Pipeline with TF-IDF vectorizer and Naive Bayes classifier
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english',
            min_df=2
        )),
        ('classifier', MultinomialNB(alpha=0.1))
    ])
    
    return pipeline


def get_topics():
    """Return list of available topics."""
    return TOPICS


