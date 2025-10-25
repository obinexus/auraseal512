#!/bin/bash
# -------------------------------------------------------------------
# OBINEXUS / AuraSeal v0.0.1 — Full Thurrock FOI Mail Service
# -------------------------------------------------------------------
# Usage:
#   chmod +x send_thurrock_foi.sh
#   ./send_thurrock_foi.sh
# -------------------------------------------------------------------

PDF_FILE="./FOI_Thurrock_2025.pdf"
APP_PASS="<app_password>"    # set your real Tutanota app password here

# recipient list (comma-separated)
TO_ADDRS="information.matters@thurrock.gov.uk,complaints@thurrock.gov.uk,HousingOptions@thurrock.gov.uk"

python3 auraseal_mailer.py \
  --file "$PDF_FILE" \
  --author-email "obinexus@tuta.com" \
  --recipient-email "information.matters@thurrock.gov.uk" \
  --smtp-server "smtp.mail.tuta.com" \
  --smtp-port 587 \
  --smtp-user "obinexus@tuta.com" \
  --smtp-pass "$APP_PASS" \
  --from "obinexus@tuta.com" \
  --to "$TO_ADDRS" \
  --subject "FOI Request – Housing and Social Care Records (Aura Sealed)" \
  --body "Dear Information Governance Team,

Please find attached my AuraSeal-protected FOI request (Ref: OBINexus/AuraMail/FOI-Thurrock-2025).
Integrity can be verified using the OBINexus public keys published on GitHub.

Kind regards,
Nnamdi M. Okpala
OBINEXUS Computing" \
  --send
