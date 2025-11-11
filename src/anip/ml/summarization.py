"""
Text summarization model - Returns random summaries for now.
"""

import random


def summarize_text(text: str, max_length: int = 100) -> str:
    """
    Summarize text (simple extraction for prototyping).
    
    Args:
        text: Input text to summarize
        max_length: Maximum length of summary
        
    Returns:
        Summary text
    """
    # Simple approach: take first N words
    words = text.split()
    
    if len(words) <= max_length // 5:  # Rough estimate
        return text
    
    # Take first sentence(s) up to max_length
    summary_words = []
    char_count = 0
    
    for word in words:
        if char_count + len(word) + 1 > max_length:
            break
        summary_words.append(word)
        char_count += len(word) + 1
    
    summary = " ".join(summary_words)
    
    # Add random score
    confidence = round(random.uniform(0.7, 0.95), 2)
    
    return f"{summary}... (confidence: {confidence})"


if __name__ == "__main__":
    # Test
    sample_text = "Artificial intelligence continues to advance rapidly. " \
                  "New models are being developed that can understand context better. " \
                  "This has implications for many industries including healthcare and finance."
    summary = summarize_text(sample_text, max_length=80)
    print(f"Summary: {summary}")
