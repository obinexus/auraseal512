# 🧿 AuraSeal v0.0.01 — Usage & Example (OBINexus)

> _“When systems fail, we build our own.”_ — Motto of OBINexus  

AuraSeal is a lightweight Python utility for **digitally sealing**, **verifying**, and **optionally emailing** sensitive PDF or text documents (such as FOI requests, housing appeals, or legal submissions).  
Each file is packaged into a cryptographically signed `.auraseal.pub.N.zip` archive to ensure **tamper evidence** and **chain-of-custody integrity**.

---

## ⚙️ Requirements

**System:** Linux / WSL / macOS  
**Dependencies:** Python 3.8+  

You can install dependencies with:

```bash
sudo apt install python3 python3-pip -y
pip install --upgrade pip
````

Clone or copy the script to your workspace:

```bash
cd ~/obinexus/workspace/civil-collapse
wget https://raw.githubusercontent.com/obinexus/auraseals514/main/auraseal_mailer.py
chmod +x auraseal_mailer.py
```

---

## 💾 Create an AuraSeal Archive

This command seals your FOI PDF (e.g. *thurrock_foi_request.pdf*) into a tamper-evident archive:

```bash
python3 auraseal_mailer.py \
  --file ./thurrock_foi_request.pdf \
  --author-email obinexus@tuta.com \
  --recipient-email information.matters@thurrock.gov.uk \
  --out-dir ./sealed
```

Output:

```
[+] Created aura archive: ./sealed/.auraseal.pub.1.zip
[*] Archive created; not sent. Use --send with SMTP options to email it.
```

This creates:

```
sealed/.auraseal.pub.1.zip
  ├─ thurrock_foi_request.pdf
  └─ auraseal.metadata.json
```

The metadata includes:

* Author and recipient
* Creation timestamp
* Public key fingerprints
* Signature hash (`_auraseal_signature`)
* AuraSeal version info

---

## 📤 Send via Email (TLS-secured)

Send the sealed archive to Thurrock Council’s Information Governance inbox:

```bash
python3 auraseal_mailer.py \
  --file ./thurrock_foi_request.pdf \
  --send \
  --smtp-server smtp.mail.tuta.com \
  --smtp-port 587 \
  --smtp-user obinexus@tuta.com \
  --smtp-pass '<your_tuta_app_password>' \
  --from obinexus@tuta.com \
  --to information.matters@thurrock.gov.uk \
  --cc complaints@thurrock.gov.uk \
  --subject "FOI Request – Housing and Social Care Records (Aura Sealed)" \
  --body "Dear Information Governance Team,  
Please find attached a digitally sealed copy of my FOI request.  
The AuraSeal archive ensures end-to-end integrity and verifiability.  
Kind regards,  
Nnamdi M. Okpala  
OBINexus Computing"
```

Result:

```
[+] Created aura archive: ./sealed/.auraseal.pub.2.zip
[+] Email sent to information.matters@thurrock.gov.uk via smtp.mail.tuta.com:587
```

---

## 🧠 Verify an Existing Archive

Use this to confirm that an `.auraseal.pub.N.zip` file has not been altered:

```bash
python3 auraseal_mailer.py --verify ./sealed/.auraseal.pub.2.zip
```

Output:

```
[*] Verification result: PASS
```

If the archive has been changed in any way, the verification will fail.

---

## 🛡️ Key Storage & Security

When you first run AuraSeal, it creates your signing key pair in:

```
~/.auraseal/private.key
~/.auraseal/public.keys.json
```

* Keep `private.key` secure.
* Public keys may be published (e.g., `github.com/obinexus/auraseals514/keys`).
* All signatures are locally verifiable via `--verify`.

If you lose your private key, you cannot recreate previous signatures.

---

## 📄 Example Workflow (FOI Request)

### Files:

```
/home/obinexus/workspace/civil-collapse/
 ├─ thurrock_foi_request.pdf
 └─ auraseal_mailer.py
```

### Command:

```bash
python3 auraseal_mailer.py --file ./thurrock_foi_request.pdf --out-dir ./sealed
```

### Archive Created:

```
./sealed/.auraseal.pub.1.zip
```

### Example Email Header:

```
To: information.matters@thurrock.gov.uk
Cc: complaints@thurrock.gov.uk, HousingOptions@thurrock.gov.uk
Subject: Freedom of Information Request – Housing and Social Care Records (AuraSeal Protected)
```

Attachment: `.auraseal.pub.1.zip`

---

## 📬 Verification Instructions (for Recipients)

If Thurrock Council or an investigator receives your sealed archive, they can verify its authenticity using your published public key and the script:

```bash
python3 auraseal_mailer.py --verify .auraseal.pub.1.zip
```

If `PASS`, the document has **not been altered since sealing**.

---

## 🧩 Example Integration Path

```bash
\\wsl.localhost\Debian\home\obinexus\obinexus\workspace\civil-collapse
```

> This WSL path corresponds to your Windows-side working directory.
> You can run the same commands in PowerShell or WSL, as long as Python 3 is installed.

---

## 🧭 Future Upgrades (Roadmap)

| Phase | Feature                | Description                                                 |
| :---- | :--------------------- | :---------------------------------------------------------- |
| 0.1.0 | **Ed25519 Signatures** | Asymmetric keys for public verification                     |
| 0.2.0 | **Auto Key Publish**   | Sync public keys to `github.com/obinexus/auraseals514/keys` |
| 0.3.0 | **TLS Validation API** | Verify seals via HTTPS endpoint                             |
| 0.4.0 | **GUI Frontend**       | Desktop drag-and-drop sealing tool                          |
| 0.5.0 | **AuraMesh Sync**      | Federated proof exchange between OBINexus nodes             |

---

### 🧬 Author

**Nnamdi Michael Okpala**
Founder — OBINexus Computing
📧 [obinexus@tuta.com](mailto:obinexus@tuta.com) | 🌐 [obinexus.org](https://obinexus.org)
🔐 *“No permission needed to breathe and relate.”*

---

> 🕊️ “When systems fail, build your own.
> When trust fades, seal your truth.”
> — OBINexus, *AuraSeal Manifesto*



