# Scout OSS Maintenance Policy

**Effective:** 2026-08-04  
**Baseline:** v1.0.0-rc3  
**Branch:** `scout-oss/rc3-maintenance`

## Freeze Status

Scout OSS is now in **maintenance mode**.

From this point forward, the `scout-oss/rc3-maintenance` branch accepts only:

- **P0/P1 bug fixes** — Critical functionality that is broken or unusable
- **Security updates** — Vulnerabilities in dependencies or runtime behavior
- **AIFME-required changes** — Changes explicitly required by the AIFME platform team

No new features, enhancements, or refactoring will be accepted unless they are required by AIFME.

## Engineering Focus

Primary engineering focus has shifted back to the **AIFME roadmap**.

Scout OSS will receive minimal maintenance attention. Community contributions are still welcome but will be reviewed against the criteria above.

## Reporting Issues

- **Bugs:** Use the GitHub issue tracker with the `bug` label
- **Security:** Use the security policy in `SECURITY.md` — do not open public issues for vulnerabilities
- **Feature requests:** Will not be prioritized unless required by AIFME

## Versioning

- Maintenance releases will use patch versions: `1.0.0rc3`, `1.0.0rc4`, etc.
- The `1.0.0rc3` baseline is frozen as of 2026-08-04
