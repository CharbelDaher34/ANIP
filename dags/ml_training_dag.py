"""
Airflow DAG for ML Model Training and Retraining.

This DAG orchestrates:
1. Training classification model
2. Training sentiment model
3. Evaluating models
4. Promoting best models to production
"""

import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Add project root to path (redundant if PYTHONPATH is set, but safe)
if '/opt/anip' not in sys.path:
    sys.path.insert(0, '/opt/anip')


# ==================== Default Args ====================

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


# ==================== Training Tasks ====================

def train_classification_model(**context):
    """Train topic classification model with custom dataset."""
    from ml.classification.train import train_and_evaluate, generate_mock_dataset
    
    print("🚀 Starting classification model training...")
    
    # Option 1: Use mock dataset
    dataset = generate_mock_dataset(n_samples=2000)
    
    # Option 2: Load from database/file (uncomment to use)
    # from shared.utils.db_utils import fetch_training_data
    # texts, labels = fetch_training_data(task='classification')
    # dataset = (texts, labels)
    
    # Train and evaluate
    results = train_and_evaluate(
        dataset=dataset,
        test_size=0.2,
        random_state=42,
        mlflow_tracking_uri="http://mlflow:5000",
        experiment_name="topic-classification"
    )
    
    print(f"✅ Training complete. Accuracy: {results['accuracy']:.4f}")
    
    # Push results to XCom for downstream tasks
    context['task_instance'].xcom_push(key='classification_results', value=results)
    
    return results


def train_sentiment_model(**context):
    """Train sentiment analysis model with custom dataset."""
    from ml.sentiment.train import train_and_evaluate, generate_mock_dataset
    
    print("🚀 Starting sentiment model training...")
    
    # Option 1: Use mock dataset
    dataset = generate_mock_dataset(n_samples=2000)
    
    # Option 2: Load from database/file (uncomment to use)
    # from shared.utils.db_utils import fetch_training_data
    # texts, labels = fetch_training_data(task='sentiment')
    # dataset = (texts, labels)
    
    # Train and evaluate
    results = train_and_evaluate(
        dataset=dataset,
        test_size=0.2,
        random_state=42,
        mlflow_tracking_uri="http://mlflow:5000",
        experiment_name="sentiment-analysis"
    )
    
    print(f"✅ Training complete. Accuracy: {results['accuracy']:.4f}")
    
    # Push results to XCom for downstream tasks
    context['task_instance'].xcom_push(key='sentiment_results', value=results)
    
    return results


def promote_best_models(**context):
    """
    Promote models to production if they meet quality threshold.
    Compares new models with current production models.
    """
    import mlflow
    from mlflow.tracking import MlflowClient
    
    mlflow.set_tracking_uri("http://mlflow:5000")
    client = MlflowClient()
    
    # Get training results from XCom
    ti = context['task_instance']
    classification_results = ti.xcom_pull(key='classification_results', task_ids='train_classification')
    sentiment_results = ti.xcom_pull(key='sentiment_results', task_ids='train_sentiment')
    
    # Minimum accuracy threshold for promotion
    ACCURACY_THRESHOLD = 0.70
    
    promoted_models = []
    
    # Promote classification model
    if classification_results and classification_results['accuracy'] >= ACCURACY_THRESHOLD:
        try:
            run_id = classification_results['run_id']
            model_uri = f"runs:/{run_id}/model"
            
            # Register or update model version
            model_name = "topic-classification"
            
            # Get latest version
            try:
                latest_versions = client.get_latest_versions(model_name, stages=["Production"])
                if latest_versions:
                    current_version = latest_versions[0].version
                    print(f"📊 Current production version: {current_version}")
            except Exception:
                print("📊 No production model found")
            
            # Transition new model to production
            model_version = client.search_model_versions(f"run_id='{run_id}'")[0]
            client.transition_model_version_stage(
                name=model_name,
                version=model_version.version,
                stage="Production",
                archive_existing_versions=True
            )
            
            promoted_models.append(f"classification v{model_version.version}")
            print(f"✅ Promoted classification model v{model_version.version} to Production")
            
        except Exception as e:
            print(f"⚠️ Could not promote classification model: {e}")
    else:
        print(f"⚠️ Classification model accuracy {classification_results['accuracy']:.4f} below threshold")
    
    # Promote sentiment model
    if sentiment_results and sentiment_results['accuracy'] >= ACCURACY_THRESHOLD:
        try:
            run_id = sentiment_results['run_id']
            model_uri = f"runs:/{run_id}/model"
            
            model_name = "sentiment-analysis"
            
            # Get latest version
            try:
                latest_versions = client.get_latest_versions(model_name, stages=["Production"])
                if latest_versions:
                    current_version = latest_versions[0].version
                    print(f"📊 Current production version: {current_version}")
            except Exception:
                print("📊 No production model found")
            
            # Transition new model to production
            model_version = client.search_model_versions(f"run_id='{run_id}'")[0]
            client.transition_model_version_stage(
                name=model_name,
                version=model_version.version,
                stage="Production",
                archive_existing_versions=True
            )
            
            promoted_models.append(f"sentiment v{model_version.version}")
            print(f"✅ Promoted sentiment model v{model_version.version} to Production")
            
        except Exception as e:
            print(f"⚠️ Could not promote sentiment model: {e}")
    else:
        print(f"⚠️ Sentiment model accuracy {sentiment_results['accuracy']:.4f} below threshold")
    
    if promoted_models:
        print(f"\n🎉 Promoted models: {', '.join(promoted_models)}")
    else:
        print("\n⚠️ No models promoted to production")
    
    return promoted_models


def reload_models_in_inference():
    """
    Reload models in inference services to use newly promoted models.
    """
    from ml.classification.inference import reload_model as reload_classification
    from ml.sentiment.inference import reload_model as reload_sentiment
    
    print("🔄 Reloading classification model...")
    reload_classification()
    
    print("🔄 Reloading sentiment model...")
    reload_sentiment()
    
    print("✅ Models reloaded in inference services")


# ==================== DAG Definition ====================

with DAG(
    'ml_model_training',
    default_args=default_args,
    description='Train and deploy ML models for news classification and sentiment analysis',
    schedule_interval='@weekly',  # Run weekly, adjust as needed
    catchup=False,
    tags=['ml', 'training', 'mlflow'],
) as dag:
    
    # Task 1: Train classification model
    train_classification_task = PythonOperator(
        task_id='train_classification',
        python_callable=train_classification_model,
        provide_context=True,
    )
    
    # Task 2: Train sentiment model
    train_sentiment_task = PythonOperator(
        task_id='train_sentiment',
        python_callable=train_sentiment_model,
        provide_context=True,
    )
    
    # Task 3: Promote best models
    promote_models_task = PythonOperator(
        task_id='promote_models',
        python_callable=promote_best_models,
        provide_context=True,
    )
    
    # Task 4: Reload models in inference
    reload_models_task = PythonOperator(
        task_id='reload_models',
        python_callable=reload_models_in_inference,
    )
    
    # Define task dependencies
    [train_classification_task, train_sentiment_task] >> promote_models_task >> reload_models_task


