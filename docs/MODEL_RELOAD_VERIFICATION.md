# Model Reload Verification Guide

This guide explains how to verify that models are actually being reloaded when the training DAG completes.

## 📊 Quick Verification Methods

### Method 1: Check Model Info Endpoint (Recommended)

The `/info` endpoint shows detailed metadata about the currently loaded model:

```bash
# Classification model
curl http://localhost:5001/info | jq .

# Sentiment model
curl http://localhost:5002/info | jq .
```

**Response includes:**
- `version`: Model version number in MLflow registry
- `run_id`: Unique MLflow run ID
- `stage`: Model stage (Production, Staging, etc.)
- `loaded_at`: Timestamp when model was loaded
- `status`: READY, PENDING, etc.

### Method 2: Check Reload Response

When you call the `/reload` endpoint, it now shows if the version changed:

```bash
curl -X POST http://localhost:5001/reload | jq .
```

**Response includes:**
```json
{
  "status": "success",
  "message": "Model 'topic-classification' reloaded successfully - version changed!",
  "old_version": "v8",
  "new_version": "9",
  "version_changed": true
}
```

### Method 3: Check Container Logs

View the container logs to see reload events:

```bash
# Classification model logs
docker logs anip-model-serving-classification --tail 50

# Sentiment model logs  
docker logs anip-model-serving-sentiment --tail 50
```

**Look for log lines like:**
```
🔄 Loading model from: models:/topic-classification/Production
✅ Model 'topic-classification' loaded successfully
   Version: 9
   Run ID: 037fc025...
```

When a reload happens with a version change:
```
✅ Model 'topic-classification' reloaded - Version changed!
   Old: v8 (run: 1a93f214...)
   New: v9 (run: 037fc025...)
```

## 🧪 Complete Verification Workflow

Here's a complete test script that verifies model reload functionality:

```bash
#!/bin/bash
# Save as test_model_reload.sh and make executable

MODEL_URL="http://localhost:5001"  # Change to 5002 for sentiment model

echo "=== STEP 1: Check current model version ==="
BEFORE_VERSION=$(curl -s $MODEL_URL/info | jq -r '.metadata.version')
BEFORE_RUN_ID=$(curl -s $MODEL_URL/info | jq -r '.metadata.run_id')
echo "Current Version: $BEFORE_VERSION"
echo "Current Run ID: $BEFORE_RUN_ID"
echo ""

echo "=== STEP 2: Make prediction with current model ==="
curl -s -X POST $MODEL_URL/invocations \
  -H "Content-Type: application/json" \
  -d '{"instances": ["test prediction"]}' | jq .
echo ""

echo "=== STEP 3: Trigger model reload ==="
curl -s -X POST $MODEL_URL/reload | jq .
echo ""

echo "=== STEP 4: Check model version after reload ==="
AFTER_VERSION=$(curl -s $MODEL_URL/info | jq -r '.metadata.version')
AFTER_RUN_ID=$(curl -s $MODEL_URL/info | jq -r '.metadata.run_id')
echo "New Version: $AFTER_VERSION"
echo "New Run ID: $AFTER_RUN_ID"
echo ""

if [ "$BEFORE_RUN_ID" != "$AFTER_RUN_ID" ]; then
    echo "✅ MODEL WAS RELOADED - Run ID changed!"
else
    echo "ℹ️  Same model version (no new Production model available)"
fi
```

## 🔍 Verification Endpoints Reference

### 1. Health Check
```bash
curl http://localhost:5001/health
```
Returns: Basic health status

### 2. Model Info (Detailed)
```bash
curl http://localhost:5001/info
```
Returns: Full model metadata including version, run_id, load time

### 3. Reload Model
```bash
curl -X POST http://localhost:5001/reload
```
Returns: Reload status with version change information

### 4. Make Prediction
```bash
curl -X POST http://localhost:5001/invocations \
  -H "Content-Type: application/json" \
  -d '{"instances": ["your text here"]}'
```
Returns: Model predictions

## 📋 What to Check After Training DAG Completes

After the `ml_model_training` DAG completes and promotes new models:

### Step 1: Check DAG Logs
```bash
# View the reload task logs
cat volumes/airflow/logs/dag_id=ml_model_training/run_id=*/task_id=reload_models/attempt=1.log
```

Look for:
```
🔄 Triggering model reload in serving containers...
   Reloading classification model...
   ✅ classification model reloaded: Model 'topic-classification' reloaded successfully - version changed!
```

### Step 2: Verify Model Versions Changed
```bash
# Check classification model
curl -s http://localhost:5001/info | jq '.metadata | {version, run_id: .run_id[0:8], loaded_at}'

# Check sentiment model
curl -s http://localhost:5002/info | jq '.metadata | {version, run_id: .run_id[0:8], loaded_at}'
```

The `loaded_at` timestamp should be recent (within minutes of DAG completion).

### Step 3: Compare with MLflow UI
1. Open MLflow UI: http://localhost:5000
2. Navigate to Models → topic-classification (or sentiment-analysis)
3. Check the Production stage version number
4. Compare with the version shown in `/info` endpoint

**They should match!**

## 🎯 Key Indicators Model Was Actually Reloaded

| Indicator | Where to Check | What to Look For |
|-----------|----------------|------------------|
| **Version Changed** | `/info` endpoint | Version number increased |
| **Run ID Changed** | `/info` endpoint | Different run_id |
| **Load Time Recent** | `/info` endpoint | `loaded_at` timestamp is recent |
| **Log Messages** | Container logs | "Version changed!" message |
| **Reload Response** | `/reload` endpoint | `version_changed: true` |

## 🚨 Troubleshooting

### Model Version Didn't Change?

**Possible reasons:**
1. No new model was promoted to Production
2. New model didn't meet accuracy threshold (< 70%)
3. Reload endpoint wasn't called

**Check:**
```bash
# Check if DAG promoted new models
grep "Promoted" volumes/airflow/logs/dag_id=ml_model_training/*/task_id=promote_models/*.log

# Check if reload was called
grep "Reloading" volumes/airflow/logs/dag_id=ml_model_training/*/task_id=reload_models/*.log
```

### Container Not Responding?

```bash
# Check container status
docker ps | grep model-serving

# Check container logs for errors
docker logs anip-model-serving-classification --tail 100
docker logs anip-model-serving-sentiment --tail 100

# Restart containers if needed
docker restart anip-model-serving-classification anip-model-serving-sentiment
```

## 📝 Example: Full Verification After Training

```bash
# 1. Check current state
echo "=== Before Training ==="
curl -s http://localhost:5001/info | jq -r '.metadata.version'

# 2. Trigger training DAG manually (via Airflow UI)
# Or wait for scheduled run

# 3. After DAG completes, check new state
echo "=== After Training ==="
curl -s http://localhost:5001/info | jq -r '.metadata | {version, loaded_at}'

# 4. Verify predictions work
curl -s -X POST http://localhost:5001/invocations \
  -H "Content-Type: application/json" \
  -d '{"instances": ["test"]}' | jq .predictions
```

## 🔗 Related Endpoints

- **MLflow UI**: http://localhost:5000
- **Airflow UI**: http://localhost:8080
- **Classification Model**: http://localhost:5001
- **Sentiment Model**: http://localhost:5002
- **API Docs (Classification)**: http://localhost:5001/docs
- **API Docs (Sentiment)**: http://localhost:5002/docs

---

## Quick Commands Cheat Sheet

```bash
# Check both model versions
curl -s http://localhost:5001/info | jq '.metadata.version'  # Classification
curl -s http://localhost:5002/info | jq '.metadata.version'  # Sentiment

# Manually reload both models
curl -X POST http://localhost:5001/reload | jq .version_changed
curl -X POST http://localhost:5002/reload | jq .version_changed

# Check container logs for reload events
docker logs anip-model-serving-classification 2>&1 | grep "reloaded"
docker logs anip-model-serving-sentiment 2>&1 | grep "reloaded"

# View latest DAG run logs
ls -t volumes/airflow/logs/dag_id=ml_model_training/ | head -1
```

