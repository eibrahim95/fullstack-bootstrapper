---
name: ensure-gcloud
description: Ensure gcloud ready to deploy. Use after gcloud installed. Picks gcloud config, checks login, ADC, project, billing, APIs.
---
# ensure-gcloud

Need gcloud. Missing: /ensure-installed gcloud.
Check fails: give fix, wait, verify again. Loop until pass. Interactive cmd: tell user run `! <cmd>`.
User gives up: report failed.
Always pass `--configuration <cfg>`. Never switch active config.

## config
`gcloud config configurations list`. Saved `gcloud.config` in `.bootstrap/setup.json` still exists, or only one: use it. Many: ask user which, ask tool, one option per config (show account, project). None: `! gcloud init`.

## checks
1 login: active account, token works. Fix: `! gcloud auth login`.
2 adc: `gcloud auth application-default print-access-token` ok. Terraform needs it. Fix: `! gcloud auth application-default login`. Same account as 1.
3 project: set and accessible. Unset: ask user pick or create, then set.
4 billing: `billingEnabled` True. Else link a billing account. None: user adds one in console.
5 apis: serviceusage, run, artifactregistry, cloudbuild, secretmanager, iam enabled. Else enable.
Ask OK before link, enable, set.

## report
Last line, exactly one:
`ensure-gcloud: done <config> <project>`
`ensure-gcloud: failed <config|login|adc|project|billing|apis|prereq>: <reason>`

## never
Print tokens. Install tools. Write .bootstrap.
