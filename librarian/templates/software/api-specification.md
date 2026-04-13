---
template_id: api-specification
display_name: API Specification
preset: software
description: RESTful or gRPC API specification with endpoints, authentication, error handling, and data models
suggested_tags:
  - api
  - specification
  - technical
suggested_folder: specs/
typical_cross_refs:
  - technical-architecture
requires: []
recommended_with:
  - technical-architecture
sections:
  - Overview
  - Base URL & Versioning
  - Authentication
  - Endpoints
  - Error Handling
  - Rate Limiting
  - Data Models
---

# API Specification: {{title}}

**API Version:** {{version}}  
**Last Updated:** {{date}}  
**Author:** {{author}}  
**Status:** {{status}}

---

## Overview

[*High-level description of the API's purpose and primary use cases.*]

### API Type

- **Protocol:** [*REST / gRPC / GraphQL / SOAP*]
- **Format:** [*JSON / Protocol Buffers / XML*]
- **Target Audience:** [*Internal services / Partners / Public / Deprecated*]

### Quick Links

- **Base URL:** [*Production URL*]
- **Sandbox URL:** [*Development/test endpoint*]
- **Documentation:** [*Link to interactive docs (Swagger, etc.)*]
- **Support Contact:** [*Email or ticket system*]

---

## Base URL & Versioning

### URL Structure

```
https://api.example.com/v{{version}}/resource-name
```

### API Versioning Strategy

- **Version Scheme:** [*Semantic Versioning / Date-based*]
- **Current Version:** {{version}}
- **Deprecated Versions:** [*List with sunset dates*]
- **Backward Compatibility:** [*What guarantees are maintained?*]

### HTTP Methods

| Method | Purpose | Idempotent |
|--------|---------|-----------|
| GET | Retrieve resource | Yes |
| POST | Create resource | No |
| PUT | Replace entire resource | Yes |
| PATCH | Partial update | No |
| DELETE | Remove resource | Yes |

---

## Authentication

### Authentication Method

**Type:** [*Bearer Token / OAuth 2.0 / API Key / mTLS*]

### Getting Started

[*Step-by-step instructions for obtaining credentials.*]

1. [*Step 1: e.g., Sign up or request access*]
2. [*Step 2: e.g., Generate API key in dashboard*]
3. [*Step 3: e.g., Include in Authorization header*]

### Authorization

```
Authorization: Bearer <your-api-token>
```

Or for API Key:

```
X-API-Key: <your-api-key>
```

### Token Management

- **Expiration:** [*Duration until token expires*]
- **Refresh Strategy:** [*How to obtain new token*]
- **Revocation:** [*Immediate revocation available?*]
- **Scopes:** [*If OAuth: list available scopes*]

{% if "iso_27001" in compliance %}

### API Security Controls

- **TLS Version:** [*1.3 minimum*]
- **Cipher Suites:** [*Approved list*]
- **Certificate Pinning:** [*Enabled / Recommended*]
- **Request Signing:** [*HMAC-SHA256 / RSA / None*]
- **IP Whitelisting:** [*Available / Required*]

{% endif %}

---

## Endpoints

### Resource: [Resource Name]

#### GET /v{{version}}/resources

**Description:** [*Retrieve a list of resources with optional filtering.*]

**Request:**

```
GET /v1/resources?status=active&limit=20&offset=0
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | [*Filter by status: active, inactive, pending*] |
| limit | integer | No | [*Max results per page (default: 20, max: 100)*] |
| offset | integer | No | [*Pagination offset (default: 0)*] |
| sort | string | No | [*Field to sort by: created_at, updated_at (prefix - for desc)*] |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "res_12345",
      "name": "Example Resource",
      "status": "active",
      "created_at": "2026-04-13T10:00:00Z",
      "updated_at": "2026-04-13T12:30:00Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 150
  }
}
```

---

#### GET /v{{version}}/resources/{id}

**Description:** [*Retrieve a single resource by ID.*]

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | [*Resource identifier (e.g., res_12345)*] |

**Response (200 OK):**

```json
{
  "id": "res_12345",
  "name": "Example Resource",
  "description": "[*Resource description*]",
  "status": "active",
  "metadata": {},
  "created_at": "2026-04-13T10:00:00Z",
  "updated_at": "2026-04-13T12:30:00Z"
}
```

---

#### POST /v{{version}}/resources

**Description:** [*Create a new resource.*]

**Request Body:**

```json
{
  "name": "New Resource",
  "description": "[*Resource description*]",
  "metadata": {}
}
```

**Required Fields:**
- `name` (string): [*Resource name, 1-255 characters*]

**Optional Fields:**
- `description` (string): [*Detailed description*]
- `metadata` (object): [*Custom key-value pairs*]

**Response (201 Created):**

```json
{
  "id": "res_67890",
  "name": "New Resource",
  "status": "active",
  "created_at": "2026-04-13T14:00:00Z",
  "updated_at": "2026-04-13T14:00:00Z"
}
```

---

#### PATCH /v{{version}}/resources/{id}

**Description:** [*Partially update a resource.*]

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | [*Resource identifier*] |

**Request Body:** [*Include only fields to update*]

```json
{
  "status": "inactive"
}
```

**Response (200 OK):** [*Updated resource object*]

---

#### DELETE /v{{version}}/resources/{id}

**Description:** [*Delete a resource (soft delete / hard delete?).*]

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | [*Resource identifier*] |

**Response (204 No Content):** [*Empty response on success*]

---

## Error Handling

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "[*Human-readable error message*]",
    "details": [
      {
        "field": "name",
        "message": "[*Field-specific error*]"
      }
    ],
    "request_id": "req_abc123xyz"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion or empty response |
| 400 | Bad Request | Malformed request, validation failed |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource already exists or state conflict |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Server temporarily down |

### Common Error Codes

| Code | HTTP | Description | Retry? |
|------|------|-------------|--------|
| INVALID_REQUEST | 400 | Malformed JSON or missing required fields | No |
| VALIDATION_ERROR | 400 | Field validation failed | No |
| AUTHENTICATION_FAILED | 401 | Invalid or expired token | No |
| FORBIDDEN | 403 | Insufficient permissions for this resource | No |
| NOT_FOUND | 404 | Resource does not exist | No |
| CONFLICT | 409 | Resource already exists | No |
| RATE_LIMITED | 429 | Too many requests | Yes |
| SERVER_ERROR | 500 | Internal error | Yes |

---

## Rate Limiting

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1681234567
```

### Rate Limit Tiers

| Tier | Requests/Hour | Requests/Day | Authentication |
|------|---------------|--------------|-----------------|
| Unauthenticated | 100 | 1,000 | None |
| Standard | 5,000 | 50,000 | API Key |
| Premium | 50,000 | 500,000 | OAuth Token |

### Best Practices

- Implement exponential backoff for retries
- Check `X-RateLimit-Remaining` before each request
- Cache responses when possible to reduce API calls

---

## Data Models

### Resource Schema

```json
{
  "id": {
    "type": "string",
    "description": "[*Unique identifier (immutable)*]",
    "example": "res_12345"
  },
  "name": {
    "type": "string",
    "description": "[*Resource name*]",
    "minLength": 1,
    "maxLength": 255,
    "example": "Production Database"
  },
  "status": {
    "type": "string",
    "enum": ["active", "inactive", "pending", "archived"],
    "description": "[*Current status*]"
  },
  "created_at": {
    "type": "string",
    "format": "date-time",
    "description": "[*ISO 8601 timestamp*]",
    "example": "2026-04-13T10:00:00Z"
  },
  "updated_at": {
    "type": "string",
    "format": "date-time",
    "description": "[*ISO 8601 timestamp of last update*]"
  }
}
```

---

## Appendix: Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | {{date}} | Initial API release |

---

*Document generated by librarian v{{librarian_version}} from template \`api-specification\`.*
