"""Realistic mock data for all connectors — zero API calls needed."""

from __future__ import annotations

import time

_NOW_TS = int(time.time())

# ──────────────────────────────────────────────────────────────────────
# Jira (20 issues, 5 projects, sprint, board)
# ──────────────────────────────────────────────────────────────────────

JIRA_PROJECTS = [
    {"key": "PAY", "name": "Payment Service", "projectTypeKey": "software"},
    {"key": "INFRA", "name": "Infrastructure", "projectTypeKey": "software"},
    {"key": "MOBILE", "name": "Mobile App", "projectTypeKey": "software"},
    {"key": "DATA", "name": "Data Platform", "projectTypeKey": "software"},
    {"key": "SEC", "name": "Security", "projectTypeKey": "software"},
]

JIRA_ISSUES: list[dict] = [
    {
        "key": "PAY-101", "fields": {
            "summary": "Payment service timeout in prod — checkout 500s",
            "status": {"name": "In Progress"}, "priority": {"name": "Highest"},
            "issuetype": {"name": "Bug"}, "assignee": {"displayName": "Sarah Chen"},
            "labels": ["p1", "prod-incident"], "created": "2026-03-16T08:22:00Z",
            "updated": "2026-03-17T02:15:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Connection pool exhaustion causing 500 errors on /checkout endpoint. ~5% of requests affected since 06:00 UTC."}]}]},
        },
    },
    {
        "key": "PAY-98", "fields": {
            "summary": "Stripe webhook signature validation fails intermittently",
            "status": {"name": "Open"}, "priority": {"name": "High"},
            "issuetype": {"name": "Bug"}, "assignee": {"displayName": "Marcus Johnson"},
            "labels": ["payments", "webhooks"], "created": "2026-03-15T14:30:00Z",
            "updated": "2026-03-16T09:45:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Approximately 2% of Stripe webhook deliveries fail signature verification. Suspect clock skew between load balancer and app servers."}]}]},
        },
    },
    {
        "key": "INFRA-892", "fields": {
            "summary": "Kubernetes pod OOMKilled — payment-worker in us-east-1",
            "status": {"name": "Open"}, "priority": {"name": "Highest"},
            "issuetype": {"name": "Bug"}, "assignee": {"displayName": "Alex Rivera"},
            "labels": ["p1", "kubernetes", "memory"], "created": "2026-03-17T01:10:00Z",
            "updated": "2026-03-17T03:30:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "payment-worker pods are getting OOMKilled after ~45min of operation. Memory leak suspected in batch processing pipeline."}]}]},
        },
    },
    {
        "key": "INFRA-890", "fields": {
            "summary": "Upgrade Redis cluster from 6.2 to 7.2",
            "status": {"name": "In Progress"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Task"}, "assignee": {"displayName": "Alex Rivera"},
            "labels": ["infrastructure", "redis"], "created": "2026-03-10T11:00:00Z",
            "updated": "2026-03-15T16:20:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Upgrade all Redis clusters to 7.2 for improved performance and new data types support. Rolling upgrade planned for off-peak hours."}]}]},
        },
    },
    {
        "key": "MOBILE-445", "fields": {
            "summary": "iOS crash on biometric auth — iPhone 15 Pro",
            "status": {"name": "Open"}, "priority": {"name": "High"},
            "issuetype": {"name": "Bug"}, "assignee": {"displayName": "Priya Patel"},
            "labels": ["ios", "crash", "auth"], "created": "2026-03-16T17:45:00Z",
            "updated": "2026-03-17T08:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Crash in FaceID flow when user switches from FaceID to passcode mid-auth. Affects ~0.3% of auth attempts on iPhone 15 Pro."}]}]},
        },
    },
    {
        "key": "MOBILE-440", "fields": {
            "summary": "Implement push notification deep linking for order updates",
            "status": {"name": "In Review"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Story"}, "assignee": {"displayName": "Priya Patel"},
            "labels": ["notifications", "feature"], "created": "2026-03-08T10:00:00Z",
            "updated": "2026-03-16T14:30:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "When user taps order update notification, deep link directly to order detail screen with tracking info."}]}]},
        },
    },
    {
        "key": "DATA-267", "fields": {
            "summary": "ETL pipeline failing for customer_events table — schema drift",
            "status": {"name": "In Progress"}, "priority": {"name": "High"},
            "issuetype": {"name": "Bug"}, "assignee": {"displayName": "Jordan Kim"},
            "labels": ["data-pipeline", "etl"], "created": "2026-03-15T09:00:00Z",
            "updated": "2026-03-16T22:10:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Schema drift detected in upstream customer_events table. New columns added without migration, causing ETL to fail on type mismatch."}]}]},
        },
    },
    {
        "key": "DATA-265", "fields": {
            "summary": "Add real-time revenue dashboard to Looker",
            "status": {"name": "Open"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Story"}, "assignee": {"displayName": "Jordan Kim"},
            "labels": ["analytics", "dashboard"], "created": "2026-03-14T13:00:00Z",
            "updated": "2026-03-14T13:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Create real-time revenue dashboard pulling from Snowflake materialized views. Include hourly/daily/weekly comparisons."}]}]},
        },
    },
    {
        "key": "SEC-156", "fields": {
            "summary": "Rotate all service account credentials — Q1 compliance",
            "status": {"name": "In Progress"}, "priority": {"name": "High"},
            "issuetype": {"name": "Task"}, "assignee": {"displayName": "Taylor Brooks"},
            "labels": ["security", "compliance"], "created": "2026-03-01T09:00:00Z",
            "updated": "2026-03-16T11:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Quarterly credential rotation for all service accounts. 14 of 23 accounts completed. Deadline: March 31."}]}]},
        },
    },
    {
        "key": "SEC-155", "fields": {
            "summary": "Implement CSP headers for customer portal",
            "status": {"name": "Open"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Task"}, "assignee": {"displayName": "Taylor Brooks"},
            "labels": ["security", "web"], "created": "2026-03-12T10:30:00Z",
            "updated": "2026-03-12T10:30:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Add Content-Security-Policy headers to customer portal. Start with report-only mode, then enforce after 2 weeks."}]}]},
        },
    },
    {
        "key": "PAY-95", "fields": {
            "summary": "Add Apple Pay support for EU customers",
            "status": {"name": "In Review"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Story"}, "assignee": {"displayName": "Sarah Chen"},
            "labels": ["payments", "feature", "eu"], "created": "2026-03-05T08:00:00Z",
            "updated": "2026-03-15T17:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Extend Apple Pay integration to support EU customers with SCA (Strong Customer Authentication) requirements."}]}]},
        },
    },
    {
        "key": "INFRA-885", "fields": {
            "summary": "Set up Terraform modules for new AWS region (eu-west-2)",
            "status": {"name": "Done"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Task"}, "assignee": {"displayName": "Alex Rivera"},
            "labels": ["terraform", "infrastructure"], "created": "2026-03-01T09:00:00Z",
            "updated": "2026-03-14T16:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Create Terraform modules for eu-west-2 region deployment. VPC, EKS, RDS, and ElastiCache modules completed and tested."}]}]},
        },
    },
    {
        "key": "PAY-92", "fields": {
            "summary": "Refund API returns stale data after partial refund",
            "status": {"name": "Done"}, "priority": {"name": "High"},
            "issuetype": {"name": "Bug"}, "assignee": {"displayName": "Marcus Johnson"},
            "labels": ["payments", "api", "bug"], "created": "2026-03-10T14:00:00Z",
            "updated": "2026-03-13T11:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "After a partial refund, the GET /refunds/{id} endpoint returns the pre-refund amount until cache TTL expires. Fixed by invalidating cache on write."}]}]},
        },
    },
    {
        "key": "MOBILE-435", "fields": {
            "summary": "Android app ANR on cold start — Pixel 8",
            "status": {"name": "Open"}, "priority": {"name": "Low"},
            "issuetype": {"name": "Bug"}, "assignee": None,
            "labels": ["android", "performance"], "created": "2026-03-14T08:00:00Z",
            "updated": "2026-03-14T08:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "ANR reported on cold start for Pixel 8 devices running Android 15. Trace shows main thread blocked on database initialization."}]}]},
        },
    },
    {
        "key": "DATA-260", "fields": {
            "summary": "Migrate analytics from BigQuery to Snowflake",
            "status": {"name": "In Progress"}, "priority": {"name": "Low"},
            "issuetype": {"name": "Epic"}, "assignee": {"displayName": "Jordan Kim"},
            "labels": ["migration", "analytics"], "created": "2026-02-15T10:00:00Z",
            "updated": "2026-03-16T09:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Phase 2 of analytics migration: move remaining 12 dashboards and 8 scheduled queries from BigQuery to Snowflake."}]}]},
        },
    },
    # ── 5 additional issues to reach 20 ──────────────────────────────
    {
        "key": "PAY-88", "fields": {
            "summary": "Implement idempotency keys for payment retries",
            "status": {"name": "In Review"}, "priority": {"name": "High"},
            "issuetype": {"name": "Story"}, "assignee": {"displayName": "Marcus Johnson"},
            "labels": ["payments", "reliability"], "created": "2026-03-07T09:00:00Z",
            "updated": "2026-03-16T10:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Add idempotency key support to all payment mutation endpoints. Prevents duplicate charges on network retries. Store keys in Redis with 24h TTL."}]}]},
        },
    },
    {
        "key": "INFRA-878", "fields": {
            "summary": "Enable Datadog APM distributed tracing for all services",
            "status": {"name": "Done"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Task"}, "assignee": {"displayName": "Alex Rivera"},
            "labels": ["observability", "datadog"], "created": "2026-03-03T10:00:00Z",
            "updated": "2026-03-12T15:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Roll out dd-trace-py and dd-trace-js to all production services. Unified service map now shows end-to-end request flow."}]}]},
        },
    },
    {
        "key": "SEC-150", "fields": {
            "summary": "Audit third-party npm packages for known CVEs",
            "status": {"name": "Done"}, "priority": {"name": "High"},
            "issuetype": {"name": "Task"}, "assignee": {"displayName": "Taylor Brooks"},
            "labels": ["security", "dependencies"], "created": "2026-03-02T08:00:00Z",
            "updated": "2026-03-10T17:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Full audit of 342 npm dependencies across customer-portal and mobile-app. Found 3 high-severity CVEs, all patched. Added Snyk to CI pipeline."}]}]},
        },
    },
    {
        "key": "MOBILE-430", "fields": {
            "summary": "Add offline mode for order history screen",
            "status": {"name": "In Progress"}, "priority": {"name": "Medium"},
            "issuetype": {"name": "Story"}, "assignee": {"displayName": "Priya Patel"},
            "labels": ["mobile", "offline", "feature"], "created": "2026-03-11T09:30:00Z",
            "updated": "2026-03-16T16:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Cache last 50 orders locally using SQLite. Show cached data when offline with a banner indicating stale data. Sync on reconnect."}]}]},
        },
    },
    {
        "key": "DATA-255", "fields": {
            "summary": "Set up dbt CI checks for PR-level data model validation",
            "status": {"name": "Open"}, "priority": {"name": "Low"},
            "issuetype": {"name": "Task"}, "assignee": {"displayName": "Jordan Kim"},
            "labels": ["dbt", "ci-cd", "data-quality"], "created": "2026-03-13T11:00:00Z",
            "updated": "2026-03-13T11:00:00Z",
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Add dbt test and dbt compile steps to GitHub Actions for data-pipeline repo. Block merge on model compilation failures or test regressions."}]}]},
        },
    },
]

JIRA_SPRINT = {
    "id": 142,
    "name": "Sprint 23 — March Storm",
    "state": "active",
    "startDate": "2026-03-10T09:00:00.000Z",
    "endDate": "2026-03-24T09:00:00.000Z",
    "goal": "Ship Apple Pay EU, fix payment timeouts, complete credential rotation",
}

JIRA_BOARD = {
    "id": 12,
    "name": "Payment Team Board",
    "type": "scrum",
    "configuration": {
        "columnConfig": {
            "columns": [
                {"name": "Open", "statuses": [{"id": "1", "self": ""}]},
                {"name": "In Progress", "statuses": [{"id": "3", "self": ""}]},
                {"name": "In Review", "statuses": [{"id": "10001", "self": ""}]},
                {"name": "Done", "statuses": [{"id": "10002", "self": ""}]},
            ]
        }
    },
}

# ──────────────────────────────────────────────────────────────────────
# GitHub (5 repos, 10 PRs, 2 issues)
# ──────────────────────────────────────────────────────────────────────

GITHUB_REPOS: list[dict] = [
    {
        "name": "payment-service",
        "full_name": "acme-corp/payment-service",
        "description": "Core payment processing microservice (Stripe, Apple Pay, Google Pay)",
        "stargazers_count": 48, "forks_count": 12, "open_issues_count": 7,
        "default_branch": "main", "language": "Python", "private": True,
        "topics": ["payments", "microservice", "python"],
    },
    {
        "name": "mobile-app",
        "full_name": "acme-corp/mobile-app",
        "description": "React Native mobile application for iOS and Android",
        "stargazers_count": 32, "forks_count": 8, "open_issues_count": 15,
        "default_branch": "main", "language": "TypeScript", "private": True,
        "topics": ["react-native", "mobile", "typescript"],
    },
    {
        "name": "infra-terraform",
        "full_name": "acme-corp/infra-terraform",
        "description": "Terraform modules for AWS infrastructure",
        "stargazers_count": 25, "forks_count": 5, "open_issues_count": 3,
        "default_branch": "main", "language": "HCL", "private": True,
        "topics": ["terraform", "aws", "infrastructure"],
    },
    {
        "name": "data-pipeline",
        "full_name": "acme-corp/data-pipeline",
        "description": "ETL pipelines and data transformations (Airflow + dbt)",
        "stargazers_count": 18, "forks_count": 4, "open_issues_count": 9,
        "default_branch": "main", "language": "Python", "private": True,
        "topics": ["data-engineering", "airflow", "dbt"],
    },
    {
        "name": "customer-portal",
        "full_name": "acme-corp/customer-portal",
        "description": "Customer-facing web portal (Next.js)",
        "stargazers_count": 22, "forks_count": 6, "open_issues_count": 11,
        "default_branch": "main", "language": "TypeScript", "private": True,
        "topics": ["nextjs", "react", "frontend"],
    },
]

GITHUB_PRS: list[dict] = [
    {
        "number": 347, "title": "Refactor connection pool timeout config",
        "state": "open", "user": {"login": "schen"},
        "head": {"ref": "fix/connection-pool-timeout"}, "base": {"ref": "main"},
        "body": "Increases connection pool size from 10 to 50 and adds configurable timeout.\n\nFixes PAY-101.",
        "created_at": "2026-03-16T19:00:00Z", "updated_at": "2026-03-17T01:30:00Z",
        "additions": 45, "deletions": 12, "changed_files": 3,
        "reviews": [{"user": {"login": "mjohnson"}, "state": "APPROVED"}],
    },
    {
        "number": 345, "title": "Add Apple Pay SCA flow for EU",
        "state": "open", "user": {"login": "schen"},
        "head": {"ref": "feat/apple-pay-eu"}, "base": {"ref": "main"},
        "body": "Implements Strong Customer Authentication for Apple Pay in EU markets.\n\nRef: PAY-95",
        "created_at": "2026-03-14T10:00:00Z", "updated_at": "2026-03-16T14:00:00Z",
        "additions": 320, "deletions": 45, "changed_files": 12,
        "reviews": [{"user": {"login": "tbrooks"}, "state": "CHANGES_REQUESTED"}],
    },
    {
        "number": 112, "title": "Fix biometric auth crash on iPhone 15 Pro",
        "state": "open", "user": {"login": "ppatel"},
        "head": {"ref": "fix/biometric-crash"}, "base": {"ref": "main"},
        "body": "Handles edge case where user switches auth method during FaceID prompt.\n\nFixes MOBILE-445",
        "created_at": "2026-03-17T06:00:00Z", "updated_at": "2026-03-17T08:00:00Z",
        "additions": 28, "deletions": 5, "changed_files": 2,
        "reviews": [],
    },
    {
        "number": 344, "title": "Add idempotency key middleware",
        "state": "open", "user": {"login": "mjohnson"},
        "head": {"ref": "feat/idempotency-keys"}, "base": {"ref": "main"},
        "body": "Middleware that checks Redis for existing idempotency keys before processing payment mutations.\n\nRef: PAY-88",
        "created_at": "2026-03-13T14:00:00Z", "updated_at": "2026-03-16T09:30:00Z",
        "additions": 185, "deletions": 20, "changed_files": 6,
        "reviews": [{"user": {"login": "schen"}, "state": "APPROVED"}],
    },
    {
        "number": 343, "title": "Upgrade Redis client to support cluster mode",
        "state": "merged", "user": {"login": "arivera"},
        "head": {"ref": "feat/redis-cluster"}, "base": {"ref": "main"},
        "body": "Switches from single-node redis-py to redis.cluster for multi-node support.\n\nRef: INFRA-890",
        "created_at": "2026-03-11T10:00:00Z", "updated_at": "2026-03-14T11:00:00Z",
        "additions": 92, "deletions": 38, "changed_files": 4,
        "reviews": [{"user": {"login": "schen"}, "state": "APPROVED"}, {"user": {"login": "tbrooks"}, "state": "APPROVED"}],
    },
    {
        "number": 110, "title": "Implement offline order history caching",
        "state": "open", "user": {"login": "ppatel"},
        "head": {"ref": "feat/offline-orders"}, "base": {"ref": "main"},
        "body": "SQLite-backed offline cache for last 50 orders. Shows stale banner when offline.\n\nRef: MOBILE-430",
        "created_at": "2026-03-14T08:30:00Z", "updated_at": "2026-03-16T15:00:00Z",
        "additions": 410, "deletions": 15, "changed_files": 9,
        "reviews": [{"user": {"login": "mjohnson"}, "state": "CHANGES_REQUESTED"}],
    },
    {
        "number": 78, "title": "Add Terraform modules for eu-west-2",
        "state": "merged", "user": {"login": "arivera"},
        "head": {"ref": "feat/eu-west-2"}, "base": {"ref": "main"},
        "body": "VPC, EKS, RDS, and ElastiCache Terraform modules for the London region.\n\nRef: INFRA-885",
        "created_at": "2026-03-08T09:00:00Z", "updated_at": "2026-03-14T15:30:00Z",
        "additions": 540, "deletions": 0, "changed_files": 18,
        "reviews": [{"user": {"login": "tbrooks"}, "state": "APPROVED"}],
    },
    {
        "number": 42, "title": "Fix schema drift handling in customer_events ETL",
        "state": "open", "user": {"login": "jkim"},
        "head": {"ref": "fix/schema-drift"}, "base": {"ref": "main"},
        "body": "Adds schema evolution support: auto-detect new columns, apply ALTER TABLE, reprocess failed batches.\n\nFixes DATA-267",
        "created_at": "2026-03-15T14:00:00Z", "updated_at": "2026-03-16T21:00:00Z",
        "additions": 156, "deletions": 42, "changed_files": 5,
        "reviews": [],
    },
    {
        "number": 341, "title": "Add Stripe webhook retry with exponential backoff",
        "state": "open", "user": {"login": "mjohnson"},
        "head": {"ref": "feat/webhook-retry"}, "base": {"ref": "main"},
        "body": "Implements exponential backoff retry queue for failed webhook deliveries. Max 5 retries over 24h.\n\nRef: PAY-98",
        "created_at": "2026-03-15T16:00:00Z", "updated_at": "2026-03-16T08:00:00Z",
        "additions": 210, "deletions": 35, "changed_files": 7,
        "reviews": [],
    },
    {
        "number": 55, "title": "Add CSP headers to customer portal",
        "state": "open", "user": {"login": "tbrooks"},
        "head": {"ref": "feat/csp-headers"}, "base": {"ref": "main"},
        "body": "Content-Security-Policy in report-only mode. Sends violations to /api/csp-report endpoint.\n\nRef: SEC-155",
        "created_at": "2026-03-14T11:00:00Z", "updated_at": "2026-03-15T09:00:00Z",
        "additions": 78, "deletions": 3, "changed_files": 4,
        "reviews": [{"user": {"login": "arivera"}, "state": "APPROVED"}],
    },
]

GITHUB_ISSUES: list[dict] = [
    {
        "number": 348, "title": "payment-service: 500 errors on /checkout endpoint",
        "state": "open", "user": {"login": "oncall-bot"},
        "labels": [{"name": "bug"}, {"name": "p1"}],
        "assignee": {"login": "schen"},
        "body": "Automated alert: 5% error rate on /checkout. See PAY-101.",
        "created_at": "2026-03-16T08:30:00Z",
    },
    {
        "number": 346, "title": "Add retry logic for webhook delivery",
        "state": "open", "user": {"login": "mjohnson"},
        "labels": [{"name": "enhancement"}],
        "assignee": {"login": "mjohnson"},
        "body": "Implement exponential backoff retry for failed webhook deliveries.",
        "created_at": "2026-03-15T11:00:00Z",
    },
]

GITHUB_FILE_CONTENT = {
    "name": "config.py",
    "path": "src/config.py",
    "sha": "abc123def456",
    "size": 1024,
    "encoding": "base64",
    "decoded_content": (
        "# Payment Service Configuration\n"
        "POOL_SIZE = 10  # TODO: increase for production load\n"
        "POOL_TIMEOUT = 30\n"
        "STRIPE_WEBHOOK_TOLERANCE = 300\n"
    ),
}

GITHUB_CODE_SEARCH = {
    "total_count": 3,
    "items": [
        {"name": "config.py", "path": "src/config.py", "repository": {"full_name": "acme-corp/payment-service"}},
        {"name": "pool.py", "path": "src/db/pool.py", "repository": {"full_name": "acme-corp/payment-service"}},
        {"name": "settings.py", "path": "src/settings.py", "repository": {"full_name": "acme-corp/customer-portal"}},
    ],
}

# ──────────────────────────────────────────────────────────────────────
# Confluence (15 pages, 4 spaces)
# ──────────────────────────────────────────────────────────────────────

CONFLUENCE_SPACES = {
    "results": [
        {"id": "1001", "key": "ENG", "name": "Engineering", "type": "global"},
        {"id": "1002", "key": "OPS", "name": "Operations & SRE", "type": "global"},
        {"id": "1003", "key": "SEC", "name": "Security", "type": "global"},
        {"id": "1004", "key": "DATA", "name": "Data Team", "type": "global"},
    ]
}

CONFLUENCE_PAGES: dict[str, dict] = {
    "90001": {
        "id": "90001", "title": "Payment Service Runbook",
        "spaceId": "1001",
        "version": {"number": 14},
        "body": {"storage": {"value": "<h1>Payment Service Runbook</h1><h2>Common Issues</h2><h3>Connection Pool Exhaustion</h3><p>Symptoms: 500 errors on /checkout, connection timeout in logs.</p><p>Mitigation: 1) Restart payment-worker pods. 2) Check Redis connection count. 3) Verify Stripe API status.</p><h3>Webhook Signature Failures</h3><p>Check NTP sync on app servers. Stripe allows 300s clock tolerance.</p>"}},
    },
    "90002": {
        "id": "90002", "title": "Incident Response Playbook",
        "spaceId": "1002",
        "version": {"number": 8},
        "body": {"storage": {"value": "<h1>Incident Response Playbook</h1><p>1. Acknowledge in PagerDuty within 5 min. 2. Create Slack thread in #incidents. 3. Identify blast radius. 4. Mitigate, then root-cause. 5. Write postmortem within 48h.</p>"}},
    },
    "90003": {
        "id": "90003", "title": "API Rate Limiting Strategy",
        "spaceId": "1001",
        "version": {"number": 5},
        "body": {"storage": {"value": "<h1>API Rate Limiting</h1><p>All external APIs use token bucket rate limiting. Default: 100 req/min per client. Burst: 20 req/s. Rate limit headers returned on every response.</p>"}},
    },
    "90004": {
        "id": "90004", "title": "On-Call Rotation — Q1 2026",
        "spaceId": "1002",
        "version": {"number": 3},
        "body": {"storage": {"value": "<h1>On-Call Rotation Q1 2026</h1><p>Week of Mar 17: Alex Rivera (primary), Sarah Chen (secondary). Escalation: Taylor Brooks (security). PagerDuty schedule ID: PSCHED01.</p>"}},
    },
    "90005": {
        "id": "90005", "title": "Data Pipeline Architecture",
        "spaceId": "1004",
        "version": {"number": 11},
        "body": {"storage": {"value": "<h1>Data Pipeline Architecture</h1><p>Source: PostgreSQL CDC via Debezium. Transform: Airflow + dbt. Warehouse: Snowflake. Visualization: Looker. Schema registry: Confluent.</p>"}},
    },
    "90006": {
        "id": "90006", "title": "Security Compliance Checklist — SOC2",
        "spaceId": "1003",
        "version": {"number": 6},
        "body": {"storage": {"value": "<h1>SOC2 Compliance Checklist</h1><p>Access control: MFA enforced. Credential rotation: quarterly. Logging: all API calls audited. Encryption: AES-256 at rest, TLS 1.3 in transit.</p>"}},
    },
    "90007": {
        "id": "90007", "title": "Kubernetes Cluster Upgrade Guide",
        "spaceId": "1002",
        "version": {"number": 9},
        "body": {"storage": {"value": "<h1>K8s Cluster Upgrade Guide</h1><p>1. Review changelog for breaking changes. 2. Test in staging. 3. Cordon/drain nodes one at a time. 4. Upgrade control plane. 5. Upgrade workers. 6. Verify all workloads.</p>"}},
    },
    "90008": {
        "id": "90008", "title": "Mobile App Release Process",
        "spaceId": "1001",
        "version": {"number": 7},
        "body": {"storage": {"value": "<h1>Mobile App Release Process</h1><p>1. Feature freeze (Monday). 2. QA regression (Tue-Wed). 3. Beta release (Thursday). 4. Monitor crash rates 48h. 5. Production rollout (following Monday). Rollback: revert to previous build in App Store Connect / Play Console.</p>"}},
    },
    # ── 7 additional pages to reach 15 ───────────────────────────────
    "90009": {
        "id": "90009", "title": "Stripe Integration Guide",
        "spaceId": "1001",
        "version": {"number": 10},
        "body": {"storage": {"value": "<h1>Stripe Integration Guide</h1><h2>Payment Intents</h2><p>All payments use PaymentIntents API. Create intent server-side, confirm client-side. Webhooks handle async status updates (payment_intent.succeeded, payment_intent.payment_failed).</p><h2>Idempotency</h2><p>All POST requests include Idempotency-Key header. Keys stored in Redis with 24h TTL. Retry-safe for network failures.</p>"}},
    },
    "90010": {
        "id": "90010", "title": "Database Migration Runbook",
        "spaceId": "1002",
        "version": {"number": 4},
        "body": {"storage": {"value": "<h1>Database Migration Runbook</h1><p>1. Test migration on staging clone. 2. Take pg_dump backup. 3. Enable maintenance mode. 4. Run migration with --lock-timeout=5s. 5. Verify row counts and constraints. 6. Disable maintenance mode. Rollback: restore from pg_dump.</p>"}},
    },
    "90011": {
        "id": "90011", "title": "CI/CD Pipeline Architecture",
        "spaceId": "1001",
        "version": {"number": 12},
        "body": {"storage": {"value": "<h1>CI/CD Pipeline Architecture</h1><p>GitHub Actions for CI. ArgoCD for CD. Pipeline stages: lint, test, build Docker image, push to ECR, deploy to staging (auto), deploy to production (manual approval). Canary deploys: 10% traffic for 15min before full rollout.</p>"}},
    },
    "90012": {
        "id": "90012", "title": "API Versioning Strategy",
        "spaceId": "1001",
        "version": {"number": 3},
        "body": {"storage": {"value": "<h1>API Versioning Strategy</h1><p>URL-based versioning: /api/v1/, /api/v2/. Deprecation policy: minimum 6 months notice. Sunset header added to deprecated endpoints. Breaking changes only in major versions. Non-breaking additions (new fields, new endpoints) allowed in minor versions.</p>"}},
    },
    "90013": {
        "id": "90013", "title": "Disaster Recovery Plan",
        "spaceId": "1002",
        "version": {"number": 5},
        "body": {"storage": {"value": "<h1>Disaster Recovery Plan</h1><h2>RTO/RPO</h2><p>RTO: 4 hours. RPO: 1 hour. Multi-region failover: us-east-1 (primary) to eu-west-2 (secondary). Route53 health checks trigger automatic DNS failover. Database: RDS cross-region read replicas promoted on failover.</p>"}},
    },
    "90014": {
        "id": "90014", "title": "Secrets Management with Vault",
        "spaceId": "1003",
        "version": {"number": 8},
        "body": {"storage": {"value": "<h1>Secrets Management</h1><p>HashiCorp Vault for all secrets. Kubernetes auth method for pod-level access. Dynamic database credentials with 1h TTL. Transit engine for encryption-as-a-service. Audit logging enabled on all secret access.</p>"}},
    },
    "90015": {
        "id": "90015", "title": "Snowflake Data Warehouse — Access & Usage Guide",
        "spaceId": "1004",
        "version": {"number": 6},
        "body": {"storage": {"value": "<h1>Snowflake Access Guide</h1><p>Warehouse: ANALYTICS_WH (auto-suspend 5min). Databases: RAW (ingestion), TRANSFORM (dbt models), ANALYTICS (reporting views). Role hierarchy: READER -> ANALYST -> ENGINEER -> ADMIN. Query cost monitoring: $2/credit, budget alert at 80% monthly allocation.</p>"}},
    },
}

CONFLUENCE_SEARCH_RESULTS = {
    "results": [
        {"content": {"id": "90001", "title": "Payment Service Runbook", "type": "page"}, "excerpt": "Connection Pool Exhaustion... 500 errors on /checkout..."},
        {"content": {"id": "90002", "title": "Incident Response Playbook", "type": "page"}, "excerpt": "Acknowledge in PagerDuty within 5 min..."},
        {"content": {"id": "90003", "title": "API Rate Limiting Strategy", "type": "page"}, "excerpt": "Token bucket rate limiting. Default: 100 req/min..."},
    ],
    "totalSize": 3,
}

# ──────────────────────────────────────────────────────────────────────
# Slack (5 channels with message history)
# ──────────────────────────────────────────────────────────────────────

SLACK_CHANNELS = {
    "ok": True,
    "channels": [
        {"id": "C001INCIDENTS", "name": "incidents", "topic": {"value": "Production incidents — see playbook"}, "num_members": 45},
        {"id": "C002PAYMENTS", "name": "team-payments", "topic": {"value": "Payment team discussions"}, "num_members": 12},
        {"id": "C003DEPLOYS", "name": "deploys", "topic": {"value": "Deployment notifications"}, "num_members": 60},
        {"id": "C004ONCALL", "name": "oncall", "topic": {"value": "On-call coordination and escalations"}, "num_members": 25},
        {"id": "C005GENERAL", "name": "engineering-general", "topic": {"value": "Engineering-wide announcements and discussion"}, "num_members": 85},
    ],
}

SLACK_MESSAGES: dict[str, dict] = {
    "C001INCIDENTS": {
        "ok": True,
        "messages": [
            {"user": "U_ALEX", "text": ":rotating_light: INC-2891: Payment API 5xx spike detected. Investigating.", "ts": "1742176200.000100"},
            {"user": "U_SARAH", "text": "Looks like connection pool exhaustion. PR #347 has the fix — increasing pool size.", "ts": "1742176800.000200"},
            {"user": "U_ALEX", "text": "Confirmed — pool was at 10 connections, hitting 100% utilization under load. Deploying fix now.", "ts": "1742177400.000300"},
            {"user": "U_SARAH", "text": "Fix deployed to staging. Error rate dropped to 0%. Pushing to prod.", "ts": "1742178000.000400"},
            {"user": "U_ALEX", "text": ":white_check_mark: Prod deploy complete. Error rate back to normal. Keeping PD incident open for monitoring.", "ts": "1742179200.000500"},
        ],
    },
    "C002PAYMENTS": {
        "ok": True,
        "messages": [
            {"user": "U_SARAH", "text": "Apple Pay EU PR is up for review: #345. Needs security review from @taylor.", "ts": "1742140000.000100"},
            {"user": "U_MARCUS", "text": "I'll review the Stripe webhook fix after standup.", "ts": "1742140600.000200"},
            {"user": "U_SARAH", "text": "Standup notes: PAY-101 is the top priority. Marcus on webhook fix, I'm on Apple Pay.", "ts": "1742141200.000300"},
        ],
    },
    "C003DEPLOYS": {
        "ok": True,
        "messages": [
            {"user": "U_BOT", "text": ":rocket: payment-service v2.4.1 deployed to production (us-east-1, us-west-2)", "ts": "1742179200.000100"},
            {"user": "U_BOT", "text": ":rocket: customer-portal v3.1.0 deployed to staging", "ts": "1742175600.000200"},
            {"user": "U_BOT", "text": ":rocket: data-pipeline v1.8.2 deployed to production", "ts": "1742172000.000300"},
        ],
    },
    "C004ONCALL": {
        "ok": True,
        "messages": [
            {"user": "U_ALEX", "text": "On-call handoff: All quiet on the western front. Watch the payment-worker memory usage.", "ts": "1742140000.000100"},
        ],
    },
    "C005GENERAL": {
        "ok": True,
        "messages": [
            {"user": "U_ALEX", "text": ":mega: Reminder: merge freeze starts Thursday for mobile release branch cut. Get your PRs in before EOD Wednesday.", "ts": "1742130000.000100"},
            {"user": "U_SARAH", "text": "Heads up: payment-service will be getting a Redis cluster upgrade this week. See INFRA-890 for details.", "ts": "1742133600.000200"},
            {"user": "U_JORDAN", "text": "Data team retro notes posted in Confluence. TL;DR: schema registry saved us this sprint.", "ts": "1742137200.000300"},
            {"user": "U_TAYLOR", "text": "Security reminder: Q1 credential rotation deadline is March 31. Check SEC-156 for your team's status.", "ts": "1742144400.000400"},
            {"user": "U_PRIYA", "text": "Mobile beta v4.2.0 is out on TestFlight and internal Google Play track. Please test the new offline mode!", "ts": "1742148000.000500"},
        ],
    },
}

SLACK_USERS: dict[str, dict] = {
    "U_SARAH": {
        "ok": True,
        "user": {"id": "U_SARAH", "name": "schen", "real_name": "Sarah Chen", "profile": {"email": "sarah@acme-corp.com", "title": "Senior Backend Engineer", "status_text": "Fixing PAY-101"}},
    },
    "U_ALEX": {
        "ok": True,
        "user": {"id": "U_ALEX", "name": "arivera", "real_name": "Alex Rivera", "profile": {"email": "alex@acme-corp.com", "title": "SRE Lead", "status_text": "On-call this week"}},
    },
    "U_MARCUS": {
        "ok": True,
        "user": {"id": "U_MARCUS", "name": "mjohnson", "real_name": "Marcus Johnson", "profile": {"email": "marcus@acme-corp.com", "title": "Backend Engineer", "status_text": ""}},
    },
    "U_JORDAN": {
        "ok": True,
        "user": {"id": "U_JORDAN", "name": "jkim", "real_name": "Jordan Kim", "profile": {"email": "jordan@acme-corp.com", "title": "Data Engineer", "status_text": "Fixing schema drift"}},
    },
    "U_TAYLOR": {
        "ok": True,
        "user": {"id": "U_TAYLOR", "name": "tbrooks", "real_name": "Taylor Brooks", "profile": {"email": "taylor@acme-corp.com", "title": "Security Engineer", "status_text": "Q1 credential rotation"}},
    },
    "U_PRIYA": {
        "ok": True,
        "user": {"id": "U_PRIYA", "name": "ppatel", "real_name": "Priya Patel", "profile": {"email": "priya@acme-corp.com", "title": "Mobile Engineer", "status_text": "Offline mode sprint"}},
    },
}

# ──────────────────────────────────────────────────────────────────────
# PagerDuty
# ──────────────────────────────────────────────────────────────────────

PAGERDUTY_INCIDENTS: list[dict] = [
    {
        "id": "INC-2891",
        "title": "Payment API 5xx spike — /checkout endpoint",
        "status": "acknowledged",
        "urgency": "high",
        "created_at": "2026-03-17T01:30:00Z",
        "service": {"id": "PSVC01", "summary": "Payment Service"},
        "assignments": [{"assignee": {"summary": "Alex Rivera"}}],
        "last_status_change_at": "2026-03-17T01:35:00Z",
    },
    {
        "id": "INC-2890",
        "title": "payment-worker OOMKilled in us-east-1",
        "status": "triggered",
        "urgency": "high",
        "created_at": "2026-03-17T01:10:00Z",
        "service": {"id": "PSVC02", "summary": "Infrastructure"},
        "assignments": [{"assignee": {"summary": "Alex Rivera"}}],
        "last_status_change_at": "2026-03-17T01:10:00Z",
    },
    {
        "id": "INC-2885",
        "title": "ETL pipeline failure — customer_events schema drift",
        "status": "resolved",
        "urgency": "low",
        "created_at": "2026-03-15T09:15:00Z",
        "service": {"id": "PSVC03", "summary": "Data Platform"},
        "assignments": [{"assignee": {"summary": "Jordan Kim"}}],
        "last_status_change_at": "2026-03-16T14:00:00Z",
    },
]

# ──────────────────────────────────────────────────────────────────────
# Datadog
# ──────────────────────────────────────────────────────────────────────

DATADOG_MONITORS: list[dict] = [
    {
        "id": 5001, "name": "Payment API Error Rate > 5%", "type": "metric alert",
        "overall_state": "Alert",
        "query": "avg(last_5m):sum:payment.api.errors{env:prod} / sum:payment.api.requests{env:prod} > 0.05",
        "tags": ["service:payment-api", "env:prod"],
    },
    {
        "id": 5002, "name": "Payment Worker Memory Usage > 90%", "type": "metric alert",
        "overall_state": "Warn",
        "query": "avg(last_10m):avg:kubernetes.memory.usage_pct{kube_deployment:payment-worker} > 90",
        "tags": ["service:payment-worker", "env:prod"],
    },
    {
        "id": 5003, "name": "API Latency p99 > 2s", "type": "metric alert",
        "overall_state": "OK",
        "query": "avg(last_15m):percentile:trace.http.request.duration{service:payment-api}.p99 > 2",
        "tags": ["service:payment-api", "env:prod"],
    },
    {
        "id": 5004, "name": "Database Connection Pool Saturation", "type": "metric alert",
        "overall_state": "Alert",
        "query": "avg(last_5m):avg:postgresql.connections.active{env:prod} / avg:postgresql.connections.max{env:prod} > 0.95",
        "tags": ["service:postgresql", "env:prod"],
    },
]

DATADOG_METRICS = {
    "status": "ok",
    "series": [
        {
            "metric": "system.cpu.user",
            "pointlist": [
                [_NOW_TS - 300, 45.2], [_NOW_TS - 240, 48.1], [_NOW_TS - 180, 52.7],
                [_NOW_TS - 120, 67.3], [_NOW_TS - 60, 72.1], [_NOW_TS, 58.4],
            ],
            "scope": "host:payment-api-1",
        }
    ],
}

DATADOG_LOGS = {
    "data": [
        {"id": "log1", "attributes": {"timestamp": "2026-03-17T02:00:00Z", "status": "error", "service": "payment-api", "message": "ConnectionPool exhausted: all 10 connections in use, 23 waiting"}},
        {"id": "log2", "attributes": {"timestamp": "2026-03-17T01:58:00Z", "status": "error", "service": "payment-api", "message": "HTTP 500 on POST /checkout — pool timeout after 30s"}},
        {"id": "log3", "attributes": {"timestamp": "2026-03-17T01:55:00Z", "status": "error", "service": "payment-worker", "message": "OOMKilled: container exceeded 512Mi memory limit"}},
        {"id": "log4", "attributes": {"timestamp": "2026-03-17T01:50:00Z", "status": "warn", "service": "payment-api", "message": "Connection pool at 90% capacity (9/10 connections active)"}},
        {"id": "log5", "attributes": {"timestamp": "2026-03-17T01:45:00Z", "status": "info", "service": "payment-api", "message": "Stripe webhook received: invoice.payment_succeeded for cus_ABC123"}},
    ],
}

DATADOG_EVENT_RESPONSE = {
    "status": "ok",
    "event": {"id": 99001, "title": "Demo event created", "text": "Event created via Enterprise MCP Server"},
}
