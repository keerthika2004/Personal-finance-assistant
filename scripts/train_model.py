import pandas as pd
import pickle
import os
import time
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

def train():
    print("Loading data...")
    df = pd.read_csv('data/training.csv')
    
    X = df['description']
    y = df['category']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training TF-IDF + Logistic Regression...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000))
    ])
    
    start = time.time()
    pipeline.fit(X_train, y_train)
    train_time = time.time() - start
    
    print(f"Training complete in {train_time:.2f}s")
    
    # Predict and evaluate
    start = time.time()
    y_pred = pipeline.predict(X_test)
    pred_time = time.time() - start
    avg_latency = pred_time / len(y_test)
    
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro')
    
    print(f"Accuracy: {acc:.4f}")
    print(f"Macro F1: {f1:.4f}")
    print(f"Avg Latency per tx: {avg_latency*1000:.2f} ms")
    
    # Save model
    models_dir = Path('backend/app/models')
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / 'categorizer.pkl'
    
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)
        
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train()
