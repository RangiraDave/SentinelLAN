# SentinelLAN

SentinelLAN is a local network monitoring tool that discovers connected devices, separates known devices from unfamiliar ones, and alerts operators when something new appears.

## Security scanning

SentinelLAN uses [Trivy](https://trivy.dev/) to check the repository for known dependency vulnerabilities, exposed secrets, and infrastructure misconfigurations. The same policy in `trivy.yaml` runs on pull requests, pushes to `main`, every Monday, and manual GitHub Actions runs.

Install Trivy using one of its [official installation methods](https://trivy.dev/docs/latest/getting-started/installation/), then run the project policy from the repository root:

```bash
trivy fs --config trivy.yaml .
```

The command exits unsuccessfully when it finds a `HIGH` or `CRITICAL` result. Do not suppress a finding without documenting why it does not affect SentinelLAN. Never commit `.env`.

To create a CycloneDX software bill of materials for a release without committing the generated file:

```bash
trivy fs --format cyclonedx --output sentinel-lan-sbom.json .
```

## Flowchart

```mermaid
graph TD

    A([Start])

    A --> B[Scan Manager / Scheduler]

    B --> C[Network Info Collector]
    C --> D[Detect Active Interface]
    D --> E[Calculate Network Range]

    E --> F[ARP Scanner]

    F --> G[Discovery Service]

    G --> H{Known Device?}

    H -- Yes --> I[Update Device<br/>IP, Last Seen, Online]

    H -- No --> J[Create Device]

    J --> K[Generate NEW_DEVICE Alert]

    I --> L[(Database)]
    K --> L
    J --> L

    L --> M[Devices App]
    L --> N[Alerts App]

    M --> O[Dashboard / UI]
    N --> O

    O --> P([End])
```
