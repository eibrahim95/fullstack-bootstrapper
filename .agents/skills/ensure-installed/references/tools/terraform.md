---
id: terraform
check: terraform --version
preferred: binary
---
binary: v=$(curl -fsSL https://checkpoint-api.hashicorp.com/v1/check/terraform | grep -o '"current_version":"[^"]*"' | cut -d'"' -f4) && os=$(uname -s | tr A-Z a-z) && arch=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/') && d=$(mktemp -d) && curl -fsSL -o "$d/tf.zip" "https://releases.hashicorp.com/terraform/${v}/terraform_${v}_${os}_${arch}.zip" && mkdir -p "$HOME/.local/bin" && unzip -o "$d/tf.zip" terraform -d "$HOME/.local/bin" && rm -rf "$d"
brew: brew tap hashicorp/tap && brew install hashicorp/tap/terraform
winget: winget install --id Hashicorp.Terraform -e
note: binary = latest release zip from releases.hashicorp.com into ~/.local/bin. User-level. Needs curl, unzip. Linux and macOS only. No checksum check.
note: ~/.local/bin must be on PATH.
note: apt, dnf need HashiCorp repo. Use generic.
