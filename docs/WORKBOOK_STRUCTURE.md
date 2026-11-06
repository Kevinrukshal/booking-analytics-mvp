# Workbook schema (fictional examples only)

This document describes the supported format. It contains no source-workbook profile, client names, booking references, financial totals or machine paths.

## Bookings

Include Booking Reference and at least two of Agent, Team, Travel Date and Selling Cost. Optional fields include Date, Profit, Type and status/check columns.

For example, a fictional row may use reference DEMO-001, agent Demo Agent, team Demo Team and selling cost 100. These are invented values, not client records.

## Errors

Include Booking Reference and Issue Found. Optional fields include Issue Found Date, Status, Responsible Agent and Handled Agent.

An invented issue such as "Example voucher missing" can reference DEMO-001. Use DEMO-HISTORICAL for an unmatched test record. Matched current-booking errors contribute to booking KPIs; unmatched historical errors remain separately searchable.

## Safety

The importer bounds compressed and expanded size, sheet count, total rows and cells. Macros and external workbook links are rejected. Only upload data you are authorized to process. Never commit input workbooks, exports, screenshots or reports containing client data.
