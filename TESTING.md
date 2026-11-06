# Local security and functional checks

1. Copy .env.example to .env and configure separate random database and access secrets as described in README.md.
2. Keep ALLOW_UPLOADS=false initially. Run docker compose up --build -d on a machine with Docker available.
3. Open http://localhost:5173. The dashboard must stay locked without the token; /api/uploads must return 401 without an Authorization header.
4. Unlock with the token. Uploads should return 403 until ALLOW_UPLOADS=true and the backend is restarted.
5. Enable uploads only for the trusted operator. Use a fictional workbook following docs/WORKBOOK_STRUCTURE.md. Confirm replacement before import.
6. Verify overview, bookings, errors and authorized exports. Lock the dashboard and verify data is no longer visible. Reload should require unlocking again.
7. AI stays off unless explicitly opted in. Test only with invented issue text. Never send client identifiers or confidential free text to a provider without a separate approved data-handling decision.

Do not create public tunnels or share source workbooks. Keep data and screenshots out of Git. Uploaded records remain in the local database volume after docker compose down.

Automated checks: backend `python -m pytest -q`; frontend `npm ci`, `npm run build`, `npm audit`. Run the Python dependency scanner separately in an isolated environment.
