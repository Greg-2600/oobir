# OOBIR API Versioning and Deprecation Policy

`flow_api.py` serves the public REST API. This policy states what clients can rely
on when the API changes, so integrations can pin to a known contract before they
depend on today's route shapes. It applies to routes under `/api/`. Operational
routes (`/health`, `/health/*`, `/metrics`, `/docs`, `/redoc`, `/openapi.json`)
and the `/ws/prices/{symbol}` WebSocket are unversioned and carry no API
compatibility promise.

## Current version

| API version | Product version | Route prefix    | Status              |
| ----------- | --------------- | --------------- | ------------------- |
| v1          | 1.0.0           | none (`/api/*`) | Current, supported  |

The product version is reported by `app.version` in `flow_api.py` and by
`CITATION.cff`. The API contract is the generated OpenAPI schema at
`/openapi.json`; it is authoritative if it disagrees with prose in this file.

## Compatibility rules

These changes are compatible and may ship within v1 without a version bump:

- new routes, new optional request parameters, and new response fields;
- new values in fields that clients already treat as opaque strings;
- fixes to data, validation messages, or documentation that leave the meaning
  of a successful response unchanged.

These changes are breaking and require a new major API version:

- removing or renaming a route, request parameter, or response field;
- changing a field's type, unit, currency, or meaning;
- making an optional parameter required, or narrowing the accepted values;
- changing a status code or error shape that clients branch on;
- changing authentication requirements for an existing route.

Clients must ignore response fields they do not recognize, because compatible
releases add fields. Clients must not depend on response field order or use
routes that are not documented in the OpenAPI schema.

## Introducing a new version

1. Implement the new contract under `/api/v2/` and leave v1 routes serving
   unchanged responses.
2. Mark replaced v1 operations `deprecated: true` in the OpenAPI schema and add
   a row to the deprecation register below.
3. Emit deprecation headers from the v1 routes and keep them available for at
   least 90 days after the announcement.
4. Update this document, the README endpoint list, and the product version when
   the old version is removed. For the first release after sunset, a removed
   route returns `410 Gone` rather than a silent `404`.

## Deprecation notices

A deprecated route responds with:

- `Deprecation: true` as defined by RFC 8631;
- `Sunset` with an HTTP-date as defined by RFC 8594, at least 90 days after the
  announcement;
- a `Link` header pointing to this policy;
- an OpenAPI `deprecated` flag and a description naming the replacement.

Clients should log these headers, move to the named replacement, and stop using
the old route before its sunset date. Do not hard-code a sunset date in client
code; read it from the response header and from the register below.

## Deprecation register

| Route | Announced | Sunset (HTTP-date) | Replacement | Notes |
| ----- | --------- | ------------------ | ----------- | ----- |
| _None currently deprecated._ | | | | |

Add a row before announcing a deprecation. `Announced` uses `YYYY-MM-DD`.
`Sunset` uses the IMF-fixdate format required by RFC 8594, for example
`Wed, 31 Mar 2027 00:00:00 GMT`, and must be at least 90 days after `Announced`.
The replacement column names the route clients should use instead.

## Client checklist

- Treat `/openapi.json` as the contract and regenerate clients from it.
- Reject unknown values only where the schema declares a closed set.
- Keep response parsing tolerant of added fields.
- Monitor `Deprecation` and `Sunset` headers in production traffic.
