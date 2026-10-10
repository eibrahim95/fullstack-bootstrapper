---
id: gcloud
check: gcloud --version
preferred: script
---
script: curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts
brew: brew install --cask gcloud-cli
winget: winget install --id Google.CloudSDK -e
note: apt and dnf need Google repo. Use generic. gcloud auth is not this skill.
