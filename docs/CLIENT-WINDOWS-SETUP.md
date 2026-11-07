# Booking Analytics - Windows client setup

This package runs locally on the client's Windows PC. GitHub and developer tools are not required.

Configure the ignored .env with separate random POSTGRES_PASSWORD and API_ACCESS_TOKEN values before starting. See the [repository README](../README.md). The dashboard requires the access token and forgets it on reload. Set ALLOW_UPLOADS=true only when ready to import approved local data.

## Before starting

The client needs:

- Windows 10 or Windows 11;
- Docker Desktop with WSL 2 enabled;
- at least 8 GB RAM;
- internet access during the first build so Docker can download its base images.

Install Docker Desktop from `https://docs.docker.com/desktop/setup/install/windows-install/`, restart Windows if requested, and open Docker Desktop. Wait until Docker reports that it is running.

The `.cmd` launchers remain in the extracted project root, one folder above this guide.

## Install from the ZIP

1. Save the supplied ZIP file on the client PC.
2. Right-click the ZIP and choose **Extract All**. Do not run the application from inside the ZIP preview.
3. Extract it to a simple local folder, for example `C:\BookingAnalytics`.
4. Double-click `INSTALL-WINDOWS.cmd`.
5. Approve Docker Desktop network access only for private networks if Windows asks.
6. Wait for the first build to finish. The browser opens automatically at `http://localhost:5173`.

The same setup can be run from Command Prompt:

```cmd
cd /d C:\BookingAnalytics
INSTALL-WINDOWS.cmd
```

## Daily use

- Double-click `START-APP.cmd` to start the app and open the browser.
- Double-click `STOP-APP.cmd` to stop the containers without deleting data.
- Upload a monthly or full-year `.xlsx` workbook (up to 100 MB) from the **Upload** page.
- On **Bookings** or **Errors**, apply filters and choose **Export filtered**.
- Tick individual rows and choose **Export selected** to download only those records.

The exported file is a simple standard `.xlsx` workbook, similar to the supplied source file, and can be opened in Microsoft Excel.

## Data and privacy

- Uploaded workbooks and database data are processed locally. Optional AI sends issue text to the configured provider only after explicit ALLOW_EXTERNAL_AI opt-in. Keep it off for confidential client data.
- `.env`, uploaded Excel files, and PostgreSQL data are not included in the distributed ZIP.
- The local database is stored in a Docker volume and remains available after `STOP-APP.cmd`.
- Do not run `docker compose down -v` unless the client intentionally wants to delete the local database.

## Troubleshooting

Check container status from Command Prompt:

```cmd
cd /d C:\BookingAnalytics
docker compose ps
docker compose logs --tail 100
```

If port `5173` or `8000` is already in use, stop the other application using that port before starting Booking Analytics.
