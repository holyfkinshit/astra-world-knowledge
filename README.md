# ASTRA World Knowledge — GitHub Repository Template (R6)

This repository stores only normalized, **opt-in** OSRS game-world observations.
It is a versioned data repository, not a transactional online database.

## Set up

1. Create a dedicated GitHub repository (public to share/read globally, or private
   while testing). Avoid mixing code, credentials and data.
2. Add the template's `.github/workflows/`, `tools/` and `data/` directories.
3. Ensure **Actions** are enabled, and under **Settings → Actions → General →
   Workflow permissions** permit **Read and write permissions** for `GITHUB_TOKEN`.
4. Generate a **fine-grained personal access token** restricted to this
   repository, with **Contents: Read and write**. NEVER commit this token,
   share it with other ASTRA users, or embed it in an APK.
5. On your Android device open ASTRA → Diagnostics → R6 World Knowledge.
   Enable local capture, play or run scripts, then *separately* enable
   GitHub sharing. Enter **owner, repository, branch** and paste your token.
   Press **Upload Pending Batch to GitHub (Manual)**. Token input clears.
6. GitHub commits a file under `data/v1/batches/`; the workflow verifies
   record hashes, deduplicates and rebuilds `knowledge/world-v1.jsonl`.

No external Dax/cloud routing system is involved. GitHub is the *only* online
service for this owner-managed upload mode. Everything else works offline.

## Data format

Each immutable batch at `data/v1/batches/XX/<SHA256>.json` contains at most
80 `records` using the `schema=1` normalized ASTRA world-observation format.
Records have no timestamps or player/session/device identifiers.

Kinds:

- `NPC`: definition ID, NPC type name, world coordinates
- `LOC`: object base ID, tile, observed shape/orientation (where available)
- `GROUND`: item ID and ground position (not the quantity or owner)
- `EDGE`: one-step movement crossing observed at two consecutive reads
- `UI_SCHEMA`: attached component group/child and structural metadata
  (x/y represent group/child; `plane=-1`, never world coordinates)

`knowledge/world-v1.jsonl` is a flat deduplicated index. `knowledge/manifest.json`
records category counts. The local SQLite file is never committed.

## Important limitations

- This R6 version discovers **observed facts**, not every location or every
  possible interaction. Entity sightings do not prove they are always present.
- Traversed route edges do not prove reachability under different game states.
- Stored LOC IDs do not imply that an `Open` action exists or is safe now.
- No token is stored; the manual upload button requires a token each time.
- GitHub's Contents API has size/rate limits and is **not** a low-latency query
  server. For heavy global reads use regional shards or a hosted index later.
- GitHub permissions require authentication for uploads. A shared community
  cannot safely distribute the owner's write token. Multi-user contributions
  should use reviewed pull requests or a GitHub App/webhook ingestion gateway;
  neither is automatically enabled by this template.
- Direct GitHub uploads disclose connection metadata to GitHub; public
  repositories expose all uploaded world facts. Sharing is OFF by default.
