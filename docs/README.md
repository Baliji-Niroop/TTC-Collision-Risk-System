# Documentation Index

This folder contains the official user and developer documentation for TTC.

## Start Here (Reading Order)

1. [Root README](../README.md)
2. [Project Map](PROJECT_MAP.md)
3. [Serial Telemetry Protocol](serial_protocol.md)
4. [Wokwi Bridge Smoke Test](wokwi_bridge_smoke_test.md)
5. [Simulation Validation Checklist](simulation-validation-checklist.md)
6. [Naming and Folder Policy](naming-and-structure-policy.md)

## Hardware and Assembly

- [Hardware Folder Index](../hardware/README.md)
- [Hardware Wiring Guide](../hardware/wiring_guide.md)
- [Hardware Assembly Checklist](../hardware/assembly_checklist.md)

## Quality Automation

- Use VS Code tasks from `.vscode/tasks.json`:
  - `Quality: Ensure Dev Dependencies`
  - `Quality: Lint`
  - `Quality: Unit Tests`
  - `Quality: Protocol Contract`
  - `Quality: Synthetic Validation`
  - `Wokwi: Smoke Test`
  - `Quality: Full Gate`

## Folder Coverage

- Runtime code: `src/`
- Firmware code: `firmware/`
- Bridge integration: `bridge/`
- Validation scripts: `validation/`
- Hardware docs: `hardware/`
