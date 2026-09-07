<div align="center">

# Auction Importers for WordPress

**Live auction stock on the dealer's own website — no manual entry, no disk usage.**
A Python scraper on a VPS keeps a private MySQL database current; a WordPress plugin
reads it **read-only** and renders a filterable catalogue. Images are hotlinked, so
the client's hosting uses **0 MB** regardless of inventory size.

[▶ Launch the demo](https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/krzysiek2115op/iaai-importer-demo/main/blueprint.json) ·
[Changelog](CHANGELOG.md) ·
[Contributing](CONTRIBUTING.md) ·
[Releases](https://github.com/krzysiek2115op/copart-iaai-importer/releases) ·
[GPL-2.0+ licence](LICENSE) ·
[Polski](README.md)

<br>

[![The „Nasze auta" catalogue page — source, make, year and damage filters, vehicle cards with Buy Now price and mileage](docs/zrzuty/01-nasze-auta-lista.png)](https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/krzysiek2115op/iaai-importer-demo/main/blueprint.json)

*WordPress boots in your browser with the plugin installed and the catalogue page
ready. Nothing to install, nothing to configure.*

<sub>**The coloured tiles instead of photos are a property of the demo, not the
product** — the demo does not hotlink real auction photography. In a live deployment
these are the source images, and that is the whole point of the solution.</sub>

![CI](https://github.com/krzysiek2115op/copart-iaai-importer/actions/workflows/ci.yml/badge.svg?branch=main)

</div>

---

## The problem

A dealer importing cars from US Copart and IAAI auctions wanted current stock on his own
website, so buyers would come to him rather than to the auction.

Manual entry was impossible: inventory turns over daily, each vehicle carries a dozen photos
and a set of technical parameters, and stale stock on a website is worse than none at all.

## Architecture — two parts joined only by a database

```
Copart / IAAI  →  scraper (Python, VPS, systemd timer)  →  MySQL  →  WP plugin (read-only)  →  visitor
                  fetch → normalise → dedupe → audit → write
```

**The scraper** runs from a systemd timer. Each stage is a separate documented module —
the repository contains nine, from `01-pobieranie` (fetching) through `09-front-media`.
The audit stage matters most and is the one usually skipped: data is checked for completeness
and plausibility *before* it reaches the client's database.

**The plugin** reads that database read-only and renders the listing: make / year / damage-type
filters, sorting, pagination, caching, Schema.org structured data and its own sitemap.

### Why this split

Had the scraper run as a WordPress plugin, every fetch would load the client's web server and
a scraper bug could take the site down. Separated, the site doesn't know the scraper exists —
it keeps serving the last good data even when a fetch fails.

### Why images are hotlinked

The client's hosting uses **0 MB** whether the inventory holds 50 vehicles or 5,000, and there
is nothing to clean up after a car is sold. A deliberate trade-off: less control over image
availability in exchange for zero storage cost.

## Proof of reusability

A **second plugin** — for ex-lease motorcycles — runs on the same site with its own database
and its own release cycle. No name collisions, no shared code to coordinate.

| Plugin | Version | Scope |
|---|---|---|
| `auta-iaai` | 0.30.6 | Cars, dual source (IAAI + Copart) |
| `motocykle-poleasingowe` | 0.12.6 | Ex-lease motorcycles |

## Stack

`Python 3` · `pytest` · `jsonschema` · `pymysql` · `PHP` · `WordPress` · `MySQL` ·
`systemd .service` + `.timer` · `GitHub Actions`

7,958 lines of Python across 47 files and 3,634 lines of PHP across 21 files, in 134 commits
on `main` and 126 annotated tags.

## The part most projects skip

The repository ships a complete set of documentation **for a non-technical client**: nine
step-by-step documents plus **ten PDF files**. Not a developer README — instructions for the
person who has to operate the thing.

A system the client doesn't understand comes back to the developer for every small question.
Documentation is cheaper than support.

Also included: five audit documents (general, second pass, security, full-system test, detailed tests),
a primary-key migration performed when the second data source was added, `uninstall.php`
so the plugin cleans up after itself, and automatic pruning of images for expired listings.

## An honest caveat

A scraper depends on the structure of someone else's website. When the source changes, the
scraper needs a fix — which is why maintenance is part of the service rather than a sign of
a defect. Stating this up front saves an argument at the first outage.

## Contributing

Workflow, versioning (two separate version axes!) and commit conventions:
[`CONTRIBUTING.md`](CONTRIBUTING.md) (Polish). Release history:
[`CHANGELOG.md`](CHANGELOG.md) — built from annotated git tags, all 126 of which
carry a description.

## Licence

GPL-2.0 — see [LICENSE](LICENSE).
