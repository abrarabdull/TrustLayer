# AI Anti-Fraud Co-Pilot

A Django web application that demonstrates how an AI assistant can support fraud monitoring teams **after** existing fraud detection systems (SAS, PRM, etc.) generate alerts. The Co-Pilot focuses on low and medium risk suspicious cases while high-risk alerts remain under manual employee or Investigation team review.

## Problem Statement

Fraud monitoring teams receive large volumes of alerts from enterprise detection systems. Many alerts fall into gray-area territory — suspicious enough to warrant review, but not severe enough to justify full investigation overhead. Analysts spend significant time triaging these cases manually.

## Solution

The AI Anti-Fraud Co-Pilot:

- Displays alerts routed from upstream monitoring systems
- Classifies cases using a rule-based risk engine
- Provides AI-powered case summaries and recommendations for low/medium risk alerts
- Simulates customer verification notifications
- Keeps the **final decision with the human analyst**
- **Never automates high-risk case handling**

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python, Django 5 |
| Frontend | Django Templates, Bootstrap 5, Custom CSS |
| Database | SQLite |
| AI | OpenAI API (optional) with mock fallback |
| Data | Synthetic seed data (40 cases) |

## How to Run

```bash
cd fraud_copilot
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_cases
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

### Optional: Enable OpenAI Integration

```bash
export OPENAI_API_KEY=your-api-key-here
python manage.py runserver
```

Without an API key, the app uses professional mock AI responses — fully functional for demo purposes.

### Re-seed Data

```bash
python manage.py seed_cases --clear
```

## How to Seed Data

The seed command loads 40 synthetic cases from `data/seed_cases.json`:

- **10** Low risk
- **20** Medium risk (largest category — gray-area focus)
- **10** High risk

```bash
python manage.py seed_cases          # Add new cases (skip duplicates)
python manage.py seed_cases --clear  # Clear all and re-seed
```

## How the Risk Engine Works

The rule-based engine in `cases/services/risk_engine.py` scores cases from 0–100 based on:

| Factor | Max Points |
|--------|-----------|
| Amount vs customer average (2x–5x+) | 10–25 |
| New device | 15 |
| New beneficiary | 15 |
| Unusual location | 15 |
| Failed login attempts (3–5+) | 12–20 |
| Previous fraud flag | 25 |
| Unusual transaction time | 5–10 |

**Risk levels:**

- **0–39**: Low
- **40–69**: Medium
- **70–100**: High

**Recommended actions:**

- High → Escalate to Investigation
- Medium → Send Customer Verification Notification
- Low → Mark as Safe

## AI Fallback Behavior

The AI analyzer (`cases/services/ai_analyzer.py`):

1. Computes risk assessment via the rule engine
2. **Blocks AI automation for high-risk cases** — returns a manual review message
3. If `OPENAI_API_KEY` is set, calls OpenAI for analyst summaries
4. If no key or API failure, uses **mock fallback** with professional, demo-ready content

The app works completely without OpenAI.

## Demo Flow

1. **Dashboard** — View 40 seeded alerts with summary cards and filters
2. **Filter medium-risk cases** — Use the risk level dropdown
3. **Open a medium-risk case** — Review transaction details and risk indicators
4. **Analyze with AI Co-Pilot** — See risk score, summary, and recommendations
5. **Send Customer Verification** — Simulate notification (demo only)
6. **Open a high-risk case** — Observe the warning banner and disabled AI actions
7. **Escalate to Investigation** — Update case status
8. **About MVP** — Read project context and disclaimers

## Project Structure

```
fraud_copilot/
├── manage.py
├── fraud_copilot/          # Django project settings
├── cases/                  # Main application
│   ├── models.py           # FraudCase model
│   ├── views.py            # Page and action views
│   ├── services/
│   │   ├── risk_engine.py  # Rule-based scoring
│   │   ├── ai_analyzer.py  # OpenAI + mock fallback
│   │   └── notification_service.py
│   ├── templates/cases/    # HTML templates
│   ├── static/             # CSS and JS
│   └── management/commands/seed_cases.py
├── data/seed_cases.json    # 40 synthetic cases
├── requirements.txt
└── README.md
```

## Future Improvements

- User authentication and role-based access (analyst vs investigator)
- Audit trail for all analyst actions
- Integration with real fraud detection system APIs
- Real SMS/email notification channels
- Machine learning model for risk scoring
- Case assignment workflow and team queues
- Dashboard analytics and reporting
- Multi-tenant support for different banking units

## Disclaimers

- **Synthetic data only** — no real customer or banking information
- **No real notifications** — customer messages are simulated in the UI
- **Hackathon MVP** — built for demonstration and proof of concept
