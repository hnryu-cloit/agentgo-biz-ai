# AgentGo Biz AI

FastAPI-based AI server for the AgentGo Biz platform.

## Goal

This repository is the AI/ML execution layer for AgentGo Biz.
The product should not treat every feature as an LLM task. The correct split is:

- `ML` for prediction, classification, anomaly scoring, optimization, ranking
- `AI/LLM` for explanation, summarization, recommendation wording, checklist extraction, report generation
- `Rule engine` for policy enforcement, guardrails, thresholds, approvals, compliance checks

This document defines what should be built with ML, what should be built with AI, and what mock data is required to develop the models before production data is fully ready.

## Current MVP Scope

Implemented in the current codebase:

- model/prompt version registry
- evidence packaging
- data sufficiency validation
- cold-start handling
- PII masking and policy filtering
- sales diagnostics, churn insight, anomaly explanation
- retention offer strategy
- campaign target validation and execution handoff
- OCR summary/checklist extraction
- analysis -> strategy -> execution workflow orchestration

API entry points live in `app/api/v1/endpoints/ai.py`.

## Architecture Principle

Each agent feature should follow the same pipeline:

1. `Raw data -> feature engineering`
2. `ML scoring / forecasting / clustering / optimization`
3. `Rule-based validation and business constraints`
4. `LLM explanation and action generation`
5. `Evidence packaging + version tag + safety filter`

That means:

- the model decides `what is likely true`
- the rules decide `what is allowed`
- the LLM decides `how to explain it to a user`

## What To Build With ML

### P0 first

| Feature | Build Type | Recommended ML approach | Output |
|---|---|---|---|
| 매출 하락 원인 Top3 도출 | ML + Rules + LLM | feature attribution on regression / gradient boosting, or heuristic decomposition in MVP | factor scores, Top3 drivers |
| 마진 하락 위험 탐지 | ML + Rules + LLM | margin risk scoring model | menu risk score, recommended price band |
| 리뷰 감성 분류 | ML | Korean text classifier or embedding + linear classifier | positive/neutral/negative, confidence |
| RFM 세그먼트 생성 | ML/Analytics | RFM scoring + clustering | segment label, risk flag |
| 이탈 위험 탐지 | ML | churn classifier, survival model, or uplift-ready score | churn probability, risk tier |
| 이상 결제/누수 탐지 | ML | anomaly detection: IsolationForest, LOF, z-score ensemble | anomaly score, anomaly type |
| 리텐션 오퍼 최적화 | ML + Rules + LLM | response propensity model + budget optimization | offer amount, target rank |
| 프로모션 ROI 사전 검증 | ML | causal-lite uplift or forecast delta simulator | expected revenue/profit/ROI |
| 재고 손실 이상 감지 | ML + Rules + LLM | threshold + anomaly scoring | loss item list, likely causes |
| 인력 부족/과잉 감지 | ML + Rules + LLM | demand forecasting + staffing gap model | hourly staffing recommendation |

### P1 later

| Feature | Build Type | Recommended ML approach |
|---|---|---|
| 유사 상권 벤치마크 | ML + LLM | similarity search / metric learning |
| 시간대 세트 전략 | ML + LLM | hourly elasticity and attach-rate forecasting |
| 발주량 최적화 | ML + OR | demand forecasting + constrained optimization |
| 수요 기반 최적 인원 예측 | ML | time-series forecasting with exogenous variables |
| SV 구역 공통 패턴 식별 | ML + LLM | clustering + outlier comparison |

## What To Build With AI / LLM

These should not be pure ML targets because they are language-generation or explanation tasks.

| Feature | Build Type | Input | Output |
|---|---|---|---|
| PQ 해석 문장 생성 | LLM | PQ decomposition numbers | manager-friendly explanation |
| 마진 리스크 해석 | LLM | margin score + evidence | risk reason and action wording |
| 이탈 징후 원인 설명 | LLM | churn score + customer behavior features | reason hypotheses + action plan |
| 이상 탐지 설명 | LLM | anomaly score + event details | cause hypotheses + checklist |
| OCR 공지 요약 | LLM | OCR text blocks | concise summary |
| OCR 체크리스트 추출 | LLM + Rules | OCR text | action items, deadline, assignee |
| 점주 일간 브리핑 | LLM | metrics + alerts + notices | short daily briefing |
| SV 방문 리포트 | LLM | store KPIs + prior actions | coaching report |
| 본사 주간 요약 | LLM | multi-store aggregate data | weekly management report |
| 리뷰 응답 초안 | LLM | review text + tone guide | editable response draft |

## What To Keep As Rules

The following should stay deterministic even after ML is added:

- 개인정보 마스킹
- 정책 위반 차단
- 데이터 충분성 검증
- 승인 필요 액션 차단
- 발송 대상 동의/쿨다운/중복 검증
- POS 변경 상한/하한 룰
- 급격한 가격 조정 방지 룰
- evidence 필수 첨부

## Detailed Modeling Plan

### 1. Sales diagnostics

`Goal`

- explain why revenue dropped or rose

`ML`

- target: `daily_sales`
- features:
  - day of week
  - holiday flag
  - weather
  - traffic proxy
  - channel mix
  - customer count
  - avg ticket
  - discount rate
- model candidates:
  - MVP: rule-based decomposition
  - Phase 1: XGBoost/LightGBM regression
  - Phase 2: SHAP-based Top3 factor attribution

`AI`

- convert factor outputs into a readable management summary

### 2. Churn risk and retention

`Goal`

- identify at-risk customers and choose a cost-effective offer

`ML`

- target: revisit within 14/30 days
- features:
  - recency
  - frequency
  - monetary
  - visit interval variance
  - coupon usage
  - last channel
  - complaint/review sentiment
- model candidates:
  - logistic regression baseline
  - gradient boosting classifier
  - uplift model later for offer selection

`AI`

- explain churn reasons
- draft retention action wording

### 3. Review analytics

`Goal`

- classify sentiment and extract issue clusters

`ML`

- sentiment classifier
- embedding clustering for topics

`AI`

- summarize top complaints and create a response draft

### 4. Anomaly detection

`Goal`

- detect abnormal discounts, cancellations, point leakage, and inventory loss

`ML`

- features:
  - event count by employee/time/menu
  - cancellation ratio
  - discount ratio
  - refund lag
  - point adjustment frequency
  - inventory variance
- model candidates:
  - z-score baseline
  - IsolationForest
  - one-class model later if enough history exists

`AI`

- explain likely reasons and generate follow-up checklist

### 5. Menu strategy and price recommendation

`Goal`

- identify menus to keep, boost, bundle, or reprice

`ML`

- ABC classification
- price elasticity estimation
- attach-rate / market-basket analysis
- ROI simulator for promotion scenarios

`AI`

- turn optimization output into an action plan for HQ/store owner

### 6. OCR and notice compliance

`Goal`

- convert notice images into structured operational tasks

`ML`

- OCR engine and layout understanding

`AI`

- summary
- checklist extraction
- ambiguity detection

## Development Sequence

Recommended implementation order:

1. `Rules first`
   - data sufficiency
   - evidence schema
   - safety and policy filters
2. `Analytics/ML baseline`
   - RFM
   - churn score
   - anomaly score
   - sales factor score
3. `LLM explanation layer`
   - explanation prompt templates
   - report generation
   - OCR summary/checklist
4. `Optimization layer`
   - offer recommendation
   - pricing
   - staffing
   - inventory order quantity
5. `Offline evaluation and A/B testing`

## Mock Data Plan

Even before real production data is complete, development should start with normalized mock data.

### Required mock datasets

| File | Purpose | Key columns |
|---|---|---|
| `mock_data/sales_daily.csv` | sales diagnosis, ROI, staffing | date, store_id, revenue, orders, customers, avg_ticket, channel, weather, promo_flag |
| `mock_data/customer_rfm.csv` | churn, retention, RFM | customer_id, recency, frequency, monetary, last_visit_days, coupon_use_rate, churned |
| `mock_data/reviews.csv` | sentiment, issue extraction | review_id, store_id, rating, review_text, sentiment_label |
| `mock_data/anomalies.csv` | anomaly detection | event_id, store_id, event_type, amount, employee_id, event_time, is_anomaly |
| `mock_data/menu_metrics.csv` | margin/price strategy | menu_id, price, cost, quantity, margin_rate, category |
| `mock_data/inventory_monthly.csv` | inventory loss | month, store_id, item_id, system_qty, actual_qty, loss_rate |
| `mock_data/staffing_hourly.csv` | staffing optimization | date, store_id, hour, sales, staff_actual, staff_recommended |
| `mock_data/notices.txt` | OCR/summary/checklist | unstructured notice text |

### Mock data principles

- each dataset should cover at least `3 stores`
- at least `90 days` of history for sales and staffing
- at least `500 customers` for churn experiments
- at least `300 reviews` with sentiment labels
- anomalies should include both normal and abnormal samples
- every record should contain `source_name` and `uploaded_at` at the pipeline level

## Baseline Metrics

Before advanced modeling, define minimum offline gates:

| Task | Metric | MVP gate |
|---|---|---|
| 리뷰 감성 분류 | macro F1 | `>= 0.80` |
| 이탈 예측 | ROC-AUC | `>= 0.75` |
| 이상 탐지 | precision at top K | `>= 0.60` |
| 매출 예측 | MAPE | `<= 20%` |
| 발주량 추천 | WAPE | `<= 25%` |
| 인력 예측 | hourly MAE | business threshold agreed |
| LLM 설명 | groundedness / factual consistency | manual QA pass |
| OCR 체크리스트 | required item recall | `>= 0.90` |

## Repository Structure Proposal

Recommended next directory layout:

```text
app/
  api/
  core/
  schemas/
  services/
  ml/
    features/
    training/
    inference/
    evaluation/
  prompts/
  mock_data/
  notebooks/
tests/
```

## Immediate Next Tasks

1. replace heuristic baselines with trainable models once real data volume is ready
2. add real data ingestion and feature-store style preprocessing
3. connect prompt rendering to a real LLM provider
4. add deployment quality gates using evaluation thresholds

## Implemented Baselines

Current baseline code:

- `app/ml/features/churn.py`: weighted churn score
- `app/ml/features/review.py`: keyword-based sentiment classifier
- `app/ml/features/anomaly.py`: robust z-score anomaly scoring
- `app/ml/features/sales.py`: factor-based sales driver breakdown
- `app/ml/features/menu.py`: price/margin action baseline
- `app/ml/features/staffing.py`: staffing gap and opportunity-cost baseline
- `app/ml/features/inventory.py`: inventory loss and reorder baseline
- `app/ml/inference/baseline_models.py`: CSV inference helpers
- `app/prompts/templates.py`: LLM-facing prompt templates
- `app/services/prompt_service.py`: prompt builder and rendering bridge
- `app/ml/evaluation/offline_eval.py`: offline evaluation runner
- `app/ml/evaluation/registry.py`: JSON metrics registry
- `app/data/preprocessors.py`: raw CSV to typed feature rows
- `app/data/pipelines.py`: dataset normalization and profiling
- `app/ml/training/train_churn.py`: churn baseline runner
- `app/ml/training/train_review_sentiment.py`: review sentiment baseline runner
- `app/ml/training/train_anomaly.py`: anomaly baseline runner
- `app/ml/training/train_sales.py`: sales factor runner
- `app/ml/training/train_menu.py`: menu strategy runner
- `app/ml/training/train_staffing.py`: staffing runner
- `app/ml/training/train_inventory.py`: inventory runner

Example:

```bash
python3 -m app.ml.training.train_churn
python3 -m app.ml.training.train_review_sentiment
python3 -m app.ml.training.train_anomaly
python3 -m app.ml.training.train_sales
python3 -m app.ml.training.train_menu
python3 -m app.ml.training.train_staffing
python3 -m app.ml.training.train_inventory
python3 -m app.ml.training.evaluate_baselines
python3 -m app.ml.training.profile_mock_data
```

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
python3 -m pytest -p no:cacheprovider
```
