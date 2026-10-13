# DevOps Monitoring Stack — Jenkins · Docker · Prometheus · Grafana

A hands-on CI/CD + observability project. Jenkins tests, builds and deploys a
Python app as a Docker container; Prometheus scrapes the app, Jenkins, the host
and every container; Grafana shows it all on a pre-built dashboard.

```
 git push ──► Jenkins ──► docker build (test stage: pytest)
                 │          docker build (runtime image)
                 │          docker run demo-app  ──► smoke test /health
                 ▼
            ┌──────────── Docker network: monitoring ────────────┐
            │ demo-app:5000/metrics   jenkins:8080/prometheus/   │
            │ node-exporter:9100      cadvisor:8080              │
            │              ▲ scraped every 15s                   │
            │          Prometheus:9090 ──► Grafana:3000          │
            └────────────────────────────────────────────────────┘
```

## Structure
```
├── docker-compose.yml        # Jenkins, Prometheus, Grafana, node-exporter, cAdvisor
├── Jenkinsfile               # Checkout → Test → Build → Deploy → Smoke test
├── app/                      # Flask app instrumented with prometheus_client
│   ├── app.py  test_app.py  requirements.txt  Dockerfile (multi-stage)
├── jenkins/                  # Jenkins image with Docker CLI + plugins
├── prometheus/               # scrape config + alert rules
├── grafana/                  # auto-provisioned datasource + dashboard
└── scripts/load.sh           # traffic generator
```

## Prerequisites
Docker Engine 24+ with Docker Compose v2, roughly 4 GB free RAM. Linux is the
smoothest; on macOS/Windows (Docker Desktop) everything works except some
node-exporter/cAdvisor host metrics.

## 1. Start the stack
```bash
docker compose up -d --build
docker compose ps
```

| Service    | URL                     | Login        |
|------------|-------------------------|--------------|
| Jenkins    | http://localhost:8080   | see step 2   |
| Prometheus | http://localhost:9090   | –            |
| Grafana    | http://localhost:3000   | admin / admin |

## 2. Unlock Jenkins
```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```
Paste it in, choose **Install suggested plugins** (the required ones are
already baked in), and create an admin user.

## 3. Create the pipeline
1. Push this folder to a Git repo (GitHub/GitLab).
2. Jenkins → **New Item** → *Pipeline* → name it `demo-app`.
3. *Pipeline* section → **Pipeline script from SCM** → Git → your repo URL →
   branch `*/main` → script path `Jenkinsfile`.
4. Optional: tick **Poll SCM** with `H/2 * * * *` to auto-build on push.
5. **Build Now**.

The pipeline deploys `demo-app` onto the `monitoring` network, so Prometheus
picks it up automatically (it shows DOWN until the first successful build).

## 4. Generate traffic and watch
```bash
./scripts/load.sh
```
Open Grafana → Dashboards → **DevOps → DevOps Overview**.

## 5. Things to try
- **Break a test** in `app/test_app.py`, push, and watch the Test stage fail
  while the running app is untouched.
- **Stop the app** (`docker stop demo-app`) and watch `AppDown` go Pending →
  Firing at http://localhost:9090/alerts.
- Hit `/error` heavily to trip `HighErrorRate`.
- Add Alertmanager to forward alerts to Slack or email.

## Useful PromQL
```promql
sum by (endpoint) (rate(app_requests_total[1m]))
histogram_quantile(0.95, sum by (le) (rate(app_request_duration_seconds_bucket[5m])))
sum(rate(app_requests_total{status=~"5.."}[5m])) / sum(rate(app_requests_total[5m]))
```

## Teardown
```bash
docker rm -f demo-app
docker compose down -v      # -v also deletes Jenkins/Prometheus/Grafana data
```

## Security note
Jenkins runs as root with the host Docker socket mounted. That is fine for a
local lab but effectively gives Jenkins root on the host — in production use a
dedicated build agent, and change the Grafana admin password.
