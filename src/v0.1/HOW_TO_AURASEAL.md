## 🧬 Command Example – Seal and Send

```bash
python3 auraseal_mailer.py \
  --file ./FOI_Thurrock_2025.md \
  --author-email obinexus@tuta.com \
  --recipient-email information.matters@thurrock.gov.uk \
  --smtp-server smtp.mail.tuta.com \
  --smtp-port 587 \
  --smtp-user obinexus@tuta.com \
  --smtp-pass '<app_password>' \
  --subject "FOI Request – Housing and Social Care Records (Aura Sealed)" \
  --body "Please find attached my AuraSeal-protected FOI request (Ref: OBINexus/AuraMail/FOI-Thurrock-2025).  
Integrity can be verified using the OBINexus public keys published on GitHub." \
  --send
````

Expected output:

```
[+] AuraSeal archive created: ./sealed/.auraseal.pub.1.zip
[+] Email sent securely via TLS to information.matters@thurrock.gov.uk
[*] Signature hash logged locally and published to OBINexus integrity ledger.
```
