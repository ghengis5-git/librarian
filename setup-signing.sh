#!/bin/bash
# Setup GPG commit signing for Librarian evidence packs
# Run from the librarian project root: ./setup-signing.sh

set -e

echo "=== Librarian Evidence Signing Setup ==="
echo ""

# Check for existing GPG keys
EXISTING_KEY=$(gpg --list-secret-keys --keyid-format long 2>/dev/null | grep -A1 "^sec" | grep -oE "[A-F0-9]{16}" | head -1)

if [ -z "$EXISTING_KEY" ]; then
    echo "No GPG key found. Generating one..."
    echo ""
    gpg --batch --gen-key <<GPGEOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Name-Real: Chris Kahn
Name-Email: research+ai@brokenwire.org
Expire-Date: 0
GPGEOF
    EXISTING_KEY=$(gpg --list-secret-keys --keyid-format long 2>/dev/null | grep -A1 "^sec" | grep -oE "[A-F0-9]{16}" | head -1)
    echo "Generated GPG key: $EXISTING_KEY"
else
    echo "Found existing GPG key: $EXISTING_KEY"
fi

echo ""
echo "Configuring git signing (local to this repo only)..."
git config --local commit.gpgsign true
git config --local user.signingkey "$EXISTING_KEY"
git config --local gpg.program gpg

echo "Done. Git signing configured."
echo ""

# Enable in REGISTRY.yaml
if grep -q "evidence_signing:" docs/REGISTRY.yaml 2>/dev/null; then
    echo "evidence_signing already present in REGISTRY.yaml — verify it says 'gpg'"
else
    # Insert after project_name line (BSD sed on macOS needs -i '')
    sed -i '' '/^  project_name:/a\
  evidence_signing: gpg' docs/REGISTRY.yaml
    echo "Added evidence_signing: gpg to docs/REGISTRY.yaml"
fi

echo ""
echo "=== Verify ==="
echo "GPG key:       $EXISTING_KEY"
echo "gpgsign:       $(git config --local commit.gpgsign)"
echo "signingkey:    $(git config --local user.signingkey)"
echo ""
echo "Next: make a signed commit to test:"
echo "  git commit --allow-empty -m 'test: verify gpg signing'"
echo "  python -m librarian --registry docs/REGISTRY.yaml evidence"
