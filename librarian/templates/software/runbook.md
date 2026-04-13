---
template_id: runbook
display_name: Runbook
preset: software
description: Operational runbook with procedures for common operations, troubleshooting, and incident response
suggested_tags:
  - operational
  - runbook
  - infrastructure
suggested_folder: runbooks/
typical_cross_refs:
  - technical-architecture
  - incident-postmortem
requires: []
recommended_with:
  - technical-architecture
  - incident-postmortem
sections:
  - Service Overview
  - Prerequisites
  - Common Operations
  - Troubleshooting
  - Escalation
  - Recovery Procedures
  - Monitoring & Alerts
---

# Runbook: {{title}}

**Service:** {{project_name}}  
**Version:** {{version}}  
**Last Updated:** {{date}}  
**Maintained By:** {{author}}

---

## Service Overview

[*Brief description of the service, what it does, who depends on it, and business criticality.*]

### Quick Facts

| Attribute | Value |
|-----------|-------|
| **Service Owner** | [*Team name and Slack channel*] |
| **On-Call Rotation** | [*PagerDuty schedule or link*] |
| **SLA** | [*e.g., 99.9% availability, P99 latency < 200ms*] |
| **Dependencies** | [*List critical upstream services*] |
| **Dependent Services** | [*List downstream services that depend on us*] |

### Access

- **Dashboard:** [*Link to monitoring dashboard*]
- **Logs:** [*Link to centralized logging (ELK, Datadog, etc.)*]
- **Runbook Repo:** [*Git or Wiki link*]
- **On-Call:** [*PagerDuty or Slack channel*]

---

## Prerequisites

### Required Access & Credentials

- [ ] SSH access to production servers
- [ ] Database credentials in password manager
- [ ] API keys for [*external service names*]
- [ ] Container registry credentials
- [ ] SSH key pairs in ~/.ssh/

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| kubectl | v1.28+ | [*brew install kubernetes-cli*] |
| docker | v24.0+ | [*docker.com or brew*] |
| aws-cli | v2.x | [*aws.amazon.com*] |
| [tool-name] | [*version*] | [*installation command*] |

### Verification

Run this to verify your setup:

```bash
kubectl version --client
docker --version
aws sts get-caller-identity
```

---

## Common Operations

### Deployment

#### Standard Blue-Green Deployment

```bash
# 1. Verify current state
kubectl get deployment {{project_name}} -n production

# 2. Create new version
kubectl set image deployment/{{project_name}} \
  {{project_name}}=myregistry/{{project_name}}:v2.0.0 \
  -n production

# 3. Monitor rollout
kubectl rollout status deployment/{{project_name}} -n production

# 4. Verify health
curl https://api.example.com/health
```

**Rollback if needed:**

```bash
kubectl rollout undo deployment/{{project_name}} -n production
```

---

### Database Maintenance

#### Backup

```bash
# Full backup
pg_dump -h db.prod.example.com -U postgres {{project_name}}_db > backup-$(date +%Y%m%d).sql

# Verify backup
gunzip -c backup-*.sql | head -20
```

**Schedule:** [*Daily at 2am UTC, retained for 30 days*]  
**Location:** [*S3 bucket with versioning enabled*]

---

#### Schema Migration

```bash
# 1. Create migration branch
git checkout -b migration/add-user-table

# 2. Write migration file
cat > migrations/001_add_users_table.sql << 'EOF'
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);
EOF

# 3. Test locally
docker compose up -d postgres
psql -h localhost -U test -d {{project_name}} < migrations/001_add_users_table.sql

# 4. Deploy to staging
kubectl set env deployment/{{project_name}} \
  RUN_MIGRATIONS=true \
  -n staging

# 5. Verify, then production
```

---

### Configuration Changes

#### Environment Variables

```bash
# Add or update
kubectl set env deployment/{{project_name}} \
  LOG_LEVEL=DEBUG \
  DB_POOL_SIZE=50 \
  -n production

# Restart to pick up changes
kubectl rollout restart deployment/{{project_name}} -n production
```

#### Secrets Management

```bash
# Update a secret
kubectl create secret generic {{project_name}}-secrets \
  --from-literal=db-password='newpassword' \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify
kubectl get secret {{project_name}}-secrets -o yaml
```

---

## Troubleshooting

### Service is Down (No Response)

1. **Check pod status:**
   ```bash
   kubectl get pods -n production -l app={{project_name}}
   kubectl describe pod <pod-name> -n production
   ```

2. **Check logs:**
   ```bash
   kubectl logs -f <pod-name> -n production
   ```

3. **Check resource usage:**
   ```bash
   kubectl top nodes
   kubectl top pods -n production
   ```

4. **Check networking:**
   ```bash
   kubectl exec -it <pod-name> -n production -- \
     curl localhost:8080/health
   ```

5. **If containers are restarting:**
   - Check startup errors: `kubectl logs <pod> --previous`
   - Verify configuration: `kubectl describe configmap {{project_name}}-config`
   - Check disk space: `kubectl exec <pod> -- df -h`

---

### High Latency

1. **Check current metrics:**
   ```
   Open: [*Dashboard link*]
   Look for: p99 latency, request queue depth, error rates
   ```

2. **Database performance:**
   ```sql
   -- Check slow queries
   SELECT query, mean_exec_time FROM pg_stat_statements
   ORDER BY mean_exec_time DESC LIMIT 10;

   -- Check table sizes
   SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
   FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

3. **Scale up if needed:**
   ```bash
   kubectl scale deployment {{project_name}} --replicas=10 -n production
   ```

---

### Memory Leak / OOM Crashes

1. **Check memory limits:**
   ```bash
   kubectl describe deployment {{project_name}} -n production | grep -i memory
   ```

2. **Analyze heap dumps:**
   ```bash
   # Generate heap dump
   jmap -dump:live,format=b,file=heap.bin <pid>

   # Analyze with tool
   jhat heap.bin
   ```

3. **Increase limits:**
   ```bash
   kubectl set resources deployment {{project_name}} \
     --limits=memory=4Gi \
     -n production
   ```

---

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 \
  --restart=Never -- \
  psql -h db.prod.example.com -U postgres -d {{project_name}}_db -c "SELECT version();"

# Check connection pool
psql -h db.prod.example.com -U postgres -d {{project_name}}_db \
  -c "SELECT count(*) as connections FROM pg_stat_activity;"
```

---

## Escalation

### Escalation Path

| Issue | Severity | Action |
|-------|----------|--------|
| P1: Service down | Critical | Page on-call engineer immediately via PagerDuty |
| P2: Elevated error rate (>1%) | High | Post to #incidents, notify team lead |
| P3: Degraded performance | Medium | Create ticket, plan fix for next sprint |
| P4: Log warnings | Low | Monitor, document |

### Communication

- **Status Page:** [*Update publicly visible status page if customer-impacting*]
- **Slack:** [*#incidents channel and team channel*]
- **PagerDuty:** [*Create incident if critical*]
- **Customer:** [*Send notification template if SLA impacted*]

---

{% if "dod_5200" in compliance %}

### Classified System Handling

**Classification Level:** {{classification}}

- **Incident Response:** Report to Information Security immediately
- **Data Handling:** Use sanitized logs when discussing (no PII/classified data)
- **External Access:** No external escalation without CISO approval
- **Audit Trail:** All access logged in compliance audit system

{% endif %}

---

## Recovery Procedures

### Service Recovery from Hard Failure

```bash
# 1. Verify infrastructure
kubectl get nodes
docker ps

# 2. Restore from backup
LATEST_BACKUP=$(aws s3 ls s3://backups/ | tail -1 | awk '{print $4}')
aws s3 cp s3://backups/$LATEST_BACKUP ./restore.sql.gz
gunzip restore.sql.gz

# 3. Apply to fresh database
psql -h new-db.example.com -U postgres < restore.sql

# 4. Redeploy application
kubectl delete deployment {{project_name}} -n production
kubectl apply -f deployment.yaml

# 5. Verify
kubectl rollout status deployment/{{project_name}} -n production
curl https://api.example.com/health
```

### Data Corruption Recovery

1. Notify CISO/Security team
2. Stop the affected service
3. Restore from backup
4. Verify integrity checksums
5. Run validation suite
6. Post-incident review

---

## Monitoring & Alerts

### Key Metrics

| Metric | Normal Range | Warning | Critical |
|--------|--------------|---------|----------|
| CPU Usage | < 50% | 70% | 90%+ |
| Memory Usage | < 60% | 80% | 95%+ |
| Disk Usage | < 70% | 85% | 95%+ |
| Error Rate | < 0.1% | 0.5% | 1%+ |
| P99 Latency | < 200ms | 500ms | 1000ms |
| Active Connections | < 100 | 200 | 500 |

### Dashboards

- **Overview:** [*Grafana dashboard link*]
- **Performance:** [*APM dashboard (DataDog, New Relic, etc.)*]
- **Logs:** [*Elasticsearch/Kibana or CloudWatch link*]

### Alert Rules

| Alert | Condition | Action |
|-------|-----------|--------|
| ServiceDown | No response for 5 min | Page on-call |
| HighErrorRate | Error rate > 1% for 10 min | Slack notification |
| DiskFull | Disk > 90% for 5 min | Slack notification |
| HighLatency | P99 > 1s for 10 min | Slack notification |

---

## Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | {{date}} | {{author}} | Initial runbook |

---

*Document generated by librarian v{{librarian_version}} from template \`runbook\`.*
