# Budget - PF POC Dashboard

A proof of concept dashboard for FR-GM review of the mapping between Budget and Performance Framework, using publicly available GC7 data for now.

Designed to be used for Regional, Country-level or Grant-level review natively hosted using **Plotly Dash**.

---

## Azure App Service Deployment Guidelines

This repository is completely prepared to be deployed directly onto a **Python Linux Azure App Service** instance via Azure Repos / Azure DevOps.

### 1. Requirements
Azure natively builds and installs all dependencies listed in `requirements.txt` via its Oryx build engine upon deployment. The list cleanly defines the critical data processing and web frameworks required.

### 2. Startup Command (Important!)
Because this application is built on top of **Plotly Dash** (which encapsulates standard Flask WSGI architectures), you must explicitly tell the Azure App Service engine how to hook into the underlying HTTP server.

In your Azure App Service configuration panel, under **Configuration -> General Settings**, set the **Startup Command** exactly to:

```bash
gunicorn --bind=0.0.0.0 --timeout 600 app:server
```

> **Why this matters:** Azure usually natively hooks into a default initialization endpoint called `app:app`, but Dash runs inherently through an isolated `app.server` boundary logic to manage the react routing map dynamically. Our code natively exposes this to Azure via `server = app.server`!
