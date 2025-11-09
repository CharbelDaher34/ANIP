# ML Models

Simple ML models for news analysis (currently using random predictions for prototyping).

## Models

- `sentiment.py`: Sentiment analysis (positive/neutral/negative)
- `classification.py`: Topic classification
- `embedding.py`: Text embeddings
- `summarization.py`: Text summarization

## Usage

```python
from ml.sentiment import predict_sentiment

result = predict_sentiment("This is a great article!")
print(result)  # {'positive': 0.65, 'neutral': 0.20, 'negative': 0.15}
```

## Next Steps

Replace random predictions with actual trained models from MLflow.
