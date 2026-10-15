# Daily Update

A daily geopolitical and military awareness brief that is automatically generated and published, with no one in the loop.

This is a public, portfolio-scale adaptation of a structured 14-topic military awareness taxonomy. It was built to demonstrate an end-to-end AI/automation pipeline (scheduled ingestion, AI-assisted processing, and automated publishing) using only publicly available data.

**[View today's brief →](https://spillers478.github.io/REPO-NAME/)**

## What it does

Every morning the pipeline:

- **Collects** the day's reporting across 17 topics. These are three flagship flashpoints (Russia/Ukraine, Iran/Israel and the wider Middle East, and disaster/access denial) plus a broader sweep that covers armed conflict, coups, nuclear activity, cyberattacks, humanitarian crises, migration, and more.
- **Vets** every article with AI. It confirms the article belongs to its topic, reassigns or discards it if it doesn't, and tags the combatant command (COCOM) region the story concerns.
- **Groups** coverage of the same event into story threads and ranks them by corroboration, source quality, recency, and escalation signals.
- **Tracks change** from day to day, flagging stories as new, continuing, returning, or growing.
- **Writes** a BLUF (Bottom Line Up Front) from the top developments, plus a short summary for each topic.
- **Publishes** the result as a clean, readable briefing page.

## Design highlights

- **Fully unattended.** It runs on a schedule and needs no server or database.
- **Fault-tolerant.** If an AI stage fails, the brief still publishes without that layer instead of breaking.
- **Honest about gaps.** A topic with nothing relevant shows "No signal today" rather than filler headlines.
- **Auditable.** Every vetting decision and ranking score is logged alongside that day's data.

## Built with

Python · GitHub Actions · Claude API · GitHub Pages
