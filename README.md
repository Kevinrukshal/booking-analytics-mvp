# Booking Analytics MVP

A desktop-first operations dashboard that turns a booking workbook into actionable booking, agent and error insights. Managers can upload an `.xlsx` file, see current booking quality immediately, compare agents using booking-level error rates, inspect unmatched historical errors and drill into individual bookings.

## Architecture

```text
React + Vite + TypeScript + Tailwind + Recharts
                        ↓ REST
                   FastAPI
                        ↓
              SQLAlchemy + PostgreSQL
                        ↓ optional, issue text only
                  Gemini API
```

Docker Compose runs three services:

- `frontend` at `http://localhost:5173`
- `backend` at `http://localhost:8000`
- `db` using PostgreSQL 16 with a persistent volume

API routes and documentation require an Authorization: Bearer token header. Only /health is public.

## Local setup

Windows PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

macOS/Linux:

```bash
cp .env.example .env
docker compose up --build
```

The committed `.env.example` contains placeholders only. Set a strong local PostgreSQL password in `.env`; the real `.env` is ignored by Git. Set API_ACCESS_TOKEN to a randomly generated value of at least 32 characters. Empty credentials fail closed. You must explicitly set ALLOW_UPLOADS=true to import files.

## Excel upload

Open the Upload page, drop a monthly or full-year workbook into the upload area and wait for the import summary. Uploading replaces the current dataset for this MVP. The default upload allowance is 100 MB for larger annual files.

The parser:

- detects booking and error sheets from normalized headers rather than sheet names;
- maps common header variants such as `Booking Ref` and `Booking Reference`;
- normalizes references, agents, statuses, dates and currency values;
- merges repeated booking references using the latest booking row while preserving every source row in JSON;
- retains every mapped source field in `raw_data`;
- retains unmatched error records for audit and filtering;
- rejects non-`.xlsx` files and files above the configured size limit.

Only fictional schema examples are documented in `docs/WORKBOOK_STRUCTURE.md`. Do not commit client workbooks or derived reports.

For safe local checks, see [local testing](docs/TESTING.md). Ports bind to loopback only; do not publish temporary public tunnels.

## Excel export

The Bookings and Errors pages support two export modes:

- **Export filtered** downloads every record matching the active filters, including results beyond the current page.
- **Export selected** downloads only the rows selected with the table checkboxes.

Exports are simple `.xlsx` tables modelled on the source workbook: headers begin on row 1, records begin on row 2, and dates/currency remain usable in Excel. The header row stays frozen and includes Excel filters.

## Windows client ZIP

The application can be delivered without GitHub. Send the client the clean project ZIP, have them extract it to a local folder, and run `INSTALL-WINDOWS.cmd`. Daily start and stop shortcuts are included. See [Windows client setup](docs/CLIENT-WINDOWS-SETUP.md) for the complete client instructions.

## Analytics rules

Numerical analytics are deterministic and run in Python/SQL. The main error rate is:

```text
unique bookings with one or more matched errors / total unique bookings
```

Agent status thresholds are configured through `MIN_AGENT_BOOKINGS` (default 10):

- Healthy: error rate below the overall average
- Watch: between the average and 1.5× the average
- Needs Attention: above 1.5× the average
- Insufficient sample: fewer than the minimum booking count

## API endpoints

```text
POST /api/uploads
GET  /api/uploads
GET  /api/dashboard
GET  /api/bookings
GET  /api/bookings/export
GET  /api/bookings/{booking_reference}
GET  /api/agents
GET  /api/agents/{agent}
GET  /api/errors
GET  /api/errors/export
GET  /api/filters
GET  /api/ai/status
POST /api/ai/classify
GET  /health
```

Lists support server-side filters and pagination. Dashboard aggregations are produced by FastAPI rather than calculated in React.

## Optional Gemini setup

AI is disabled unless ALLOW_EXTERNAL_AI=true and both provider values are configured in `.env`:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

The key is read only by FastAPI and is never exposed to React. Only individual issue text is sent to Gemini. All dashboard numbers, rates, rankings and financial totals remain deterministic. When AI is disabled, regex-based travel-operations categories and severity rules keep the application fully functional.

## Database migrations

The backend runs `alembic upgrade head` before the API starts. To run migrations manually inside the container:

```bash
docker compose exec backend alembic upgrade head
```

## Tests and builds

```bash
cd backend
pytest -q

cd ../frontend
npm install
npm run typecheck
npm run build
```

Backend coverage includes normalization, date/money parsing, booking/error joins, duplicate detection, agent error-rate logic and AI response validation.

## Deployment

This is a single-operator local application, not a multi-tenant service. The shared bearer token protects all data and grants the same permissions to its holder. Uploads are separately disabled by default. Before Internet hosting, add individual identity/roles, HTTPS, edge rate limits, private databases and tested backups. Per-process rate limits are not a distributed abuse-control service. The frontend container serves static files through nginx, not Vite preview.


## Security setup

Generate separate random secrets, for example `python -c "import secrets; print(secrets.token_hex(32))"`, for POSTGRES_PASSWORD and API_ACCESS_TOKEN in the ignored `.env`. Never share or commit this file. Enter the access token in the dashboard unlock screen; it stays only in page memory and is cleared on lock/reload. Keep the deployment local and use synthetic data for public demonstrations. See SECURITY.md for limitations and publication cleanup.
