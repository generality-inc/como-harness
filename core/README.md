# como-core

Shared types and protocols for Como.

Both the public Python SDK (`como`) and the backend (`como-api`) depend on this
package. It is the single source of truth for the request/response shapes that
flow over the `/v1/*` HTTP surface.

Today this package holds Pydantic models for the LinkedIn ghost endpoints
(profiles, companies, posts, jobs, ads, groups, leads, services, geo). As the
platform grows it will also hold:

- shared error classes
- pagination protocols
- enums for cross-cutting concepts (kinds, scopes, statuses)

## Why a separate package

When the SDK owned the models, the backend had to either duplicate them or
import the SDK (inverting the dependency arrow). Extracting `como-core` puts
the contract in one place and lets both sides depend on it cleanly.
