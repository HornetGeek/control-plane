# Control Plane - Multi-tenant SaaS Control Plane API

## Architecture

```
                    ┌───────────────────────────────┐
                    │        auth.craft-crew.com     │
                    │            (SSO / IdP)         │
                    └───────────────▲───────────────┘
                                    │ OIDC/SAML
                                    │
                           login / token validation
                                    │
┌───────────────────────────────────┴───────────────────────────────────┐
│                         CONTROL PLANE (Generic SaaS)                  │
│------------------------------------------------------------------------│
│ - App Catalog (PACS/ERP/...)                                           │
│ - Subscriptions / Entitlements (trial/active/...)                      │
│ - Launch / Redirect (creates short-lived launch token)                 │
│ - Minimal Tenant/Org/User mapping for MVP                              │
└───────────────▲───────────────────────────────▲───────────────────────┘
                │                               │
        entitlement check                  launch redirect
                │                               │
                │                          (token + context)
                │                               │
                │                     ┌─────────┴─────────┐
                │                     │  APP FRONTEND/UI   │
                │                     │  (PACS UI / ERP UI) │
                │                     └─────────▲─────────┘
                │                               │ API calls
                │                               │ (tenant/org/user context)
┌───────────────┴───────────────────────────────┴───────────────────────┐
│                          CORE SERVICES (Platform)                      │
│------------------------------------------------------------------------│
│ - Users directory (linked to IdP subject)                               │
│ - Memberships (user↔tenant/org)                                         │
│ - RBAC (roles/permissions/assignments)                                  │
│ - Audit (append-only events)                                            │
│ - Notifications (email/SMS/etc)                                         │
└───────────────▲───────────────────────────────▲───────────────────────┘
                │                               │
        authZ decision                     audit/notify
                │                               │
                │                               │
┌───────────────┴───────────────────────────────┴───────────────────────┐
│                               DATA PLANE                               │
│                 (Domain microservices per application)                  │
│------------------------------------------------------------------------│
│  ┌───────────────────────────┐        ┌───────────────────────────┐    │
│  │   PACS Service (FastAPI?)  │        │    ERP Service (FastAPI?)  │    │
│  │ - PACS DB (tenant-aware)   │        │ - ERP DB (tenant-aware)    │    │
│  │ - domain APIs/workflows    │        │ - domain APIs/workflows     │    │
│  └───────────────────────────┘        └───────────────────────────┘    │
│                                                                         │
│ (Each service enforces tenant/org isolation + asks Core/Control as needed)│
└─────────────────────────────────────────────────────────────────────────┘
```

