# JANUS P=NP private Google Drive corpus setup

The integration is designed to work safely **without** Drive credentials. In that mode TOPA uses the pinned Git fallback and emits an explicit degraded receipt.

To enable live private Drive read/write in GitHub Actions, configure these repository secrets in `Hawkar-usls/TOPA`:

- `JANUS_GDRIVE_CLIENT_ID`
- `JANUS_GDRIVE_CLIENT_SECRET`
- `JANUS_GDRIVE_REFRESH_TOKEN`

The OAuth grant should be limited to the Drive access needed for the JANUS P=NP research pack. Do not commit tokens, access tokens, refresh tokens, client secrets, or exported credentials to Git.

## Bound Drive objects

- root pack folder: `1afNpNkT1KcTZie1SJQz6drmIg5kEfVMZ`
- materials index: `1lL5lftT64eojjeNcd0RqvS9XpCFyaqE9`
- automatic ingest folder: `1JPo-GtCtIO6yMDIsOvB9RTCDdZMNFDAk`
- weight-state folder: `1IwRcwQ9VCvku8P4AKJd2TkKiG1CU4b2F`

## Write policy

TOPA does not rewrite source papers or manual source notes. It publishes only:

- `TOPA_PNP_CORPUS_LATEST.json` into `AUTO_INGEST`;
- `TOPA_PNP_WEIGHT_LEDGER.json` into `WEIGHT_STATE`.

The weight ledger is routing metadata, not a truth/evidence score.

## Dedupe policy

Hard publication identity is evaluated in this order:

1. DOI;
2. canonical arXiv id with version stripped;
3. normalized title + first author;
4. normalized source URL;
5. exact content SHA-256.

Near-semantic duplicates are flagged and preserved; they are not auto-merged.

## Fail-closed behavior

If OAuth is missing or Drive is unavailable:

```text
DRIVE = DEGRADED
INDEX = PINNED_GITHUB_FALLBACK
DISCOVERY = CONTINUES
DRIVE_WRITE = SKIPPED
FUNDAMENTUM_AUTHORITY = UNCHANGED
```

No Drive outage is negative scientific evidence and no search/ranking result may promote a P=NP claim.
