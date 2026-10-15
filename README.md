# AWS Network Default Regions Cleanup

Python utility designed to identify and purge default VPCs, Subnets, and Internet Gateways across all default-enabled AWS regions. The tool does detach the Internet Gateway before deleting the resources so the whole clean up can be done in a single execution.

Some AWS Regions cannot be disabled and they are provisioned by Amazon with VPC, Subnets and Internet Gateway. Users can potentially provision resources in this network and expose the environment to breaches or attacks.

This utility should be executed at regular cadence so if new default regions are activated then they cannot be exploited.

Terraform provides a similar functionality and allows deleting default subnets and VPCs, however. The current solution neither detaches Internet Gateway nor deletes it.

---

## High-Risk Warning

> **CRITICAL:** This tool performs destructive actions. Always run `task plan` first and review the resources that will be deleted.
> 
> * Always run a **task plan** first to verify what will be removed.
> * Ensure you are authenticated to the **correct AWS Account** before execution.

---

## Features

- **Automated Discovery:** Automatically scans all AWS regions enabled by default.
- **Resource Dependency Resolution:** Correctly handles cleanup order (Internet Gateways -> Subnets -> VPCs) to prevent dependency conflicts.
- **Safe Mode (task plan):** Evaluates and logs target resources without executing actual deletion calls.

---

## Prerequisites

Before executing the script, ensure your system meets the following requirements:

1. **Python 3.8+** installed.
2. **AWS CLI** configured with administrator/network-management permissions.
3. Access to an environment with valid AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, or an active SSO session).

---

## Usage

---

## Running Tests

This project includes a robust **pytest** unit test suite to validate the orchestration logic and mock API interactions safely.

To run the unit tests and review code coverage:

```bash
task test
```

---

### 1. Preview Mode (plan)
By default, the script should be configured to run safely. Use the `task plan` to print out the target infrastructure without executing deletions:

```bash
task plan
```

**Example Output:**
```text
INFO: Loading (this might take a few minutes)...


INFO: Deleting ....

INFO: Cleaning: ap-northeast-1
INFO: Subnets to be delete: 3
INFO: Deleting Subnet: subnet-09875a531c3e32f9d
INFO: [DRY RUN SUCCESS] Request verified. subnet-09875a531c3e32f9d would be deleted in a live run.
INFO: Deleting Subnet: subnet-033a6a70bfd22dd29
INFO: [DRY RUN SUCCESS] Request verified. subnet-033a6a70bfd22dd29 would be deleted in a live run.
INFO: Deleting Subnet: subnet-0d829d768ad6e5456
INFO: [DRY RUN SUCCESS] Request verified. subnet-0d829d768ad6e5456 would be deleted in a live run.
INFO: VPCs to be deleted count: 1
INFO: Deleting VPC: vpc-0299f5a27d8cd915e
INFO: [DRY RUN SUCCESS] Request verified. vpc-0299f5a27d8cd915e would be deleted in a live run.
```

### 2. Live Purge Execution
When you are completely confident in the target scope, initiate the live cleanup process:

```bash
task apply
```
