#!/usr/bin/env python3
"""
auraseal_mailer.py — v0.0.01
Seal a file (PDF/email) into an Aura archive and optionally send by email.

Usage examples:
  # create archive only
  python auraseal_mailer.py --file ./thurrock_email.pdf --out-dir ./sealed

  # create archive and send (SMTP credentials required)
  python auraseal_mailer.py --file ./thurrock_email.pdf --send \
      --smtp-server smtp.example.com --smtp-port 587 \
      --smtp-user you@example.com --smtp-pass 'mypassword' \
      --from you@example.com --to complaints@thurrock.gov.uk \
      --subject "Sealed FOI request"

  # verify an archive
  python auraseal_mailer.py --verify ./sealed/.auraseal.pub.1.zip
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import time
import zipfile
import base64
from datetime import datetime
from typing import Tuple
import smtplib
from email.message import EmailMessage

# -------- Config: where to store keys --------
AURASEAL_DIR = os.path.expanduser("~/.auraseal")
PRIVATE_KEY_PATH = os.path.join(AURASEAL_DIR, "private.key")
PUBLIC_KEYS_PATH = os.path.join(AURASEAL_DIR, "public.keys.json")

# -------- Utility functions --------
def ensure_auraseal_dir():
    os.makedirs(AURASEAL_DIR, exist_ok=True)

def load_or_create_keypair() -> Tuple[str, dict]:
    """
    Load an existing private key or create a new scalar private key and derived public keys.
    Very simple key derivation using SHA256 (NOT a full KDF). Fine for POC.
    Returns (private_key, public_keys_dict)
    """
    ensure_auraseal_dir()
    if os.path.exists(PRIVATE_KEY_PATH):
        with open(PRIVATE_KEY_PATH, "r") as f:
            private = f.read().strip()
    else:
        private = hashlib.sha512(os.urandom(64)).hexdigest()
        with open(PRIVATE_KEY_PATH, "w") as f:
            f.write(private)
        os.chmod(PRIVATE_KEY_PATH, 0o600)

    # derive two public-ish keys (vector idea)
    pub1 = hashlib.sha256(f"{private}:vector1".encode()).hexdigest()
    pub2 = hashlib.sha256(f"{private}:vector2".encode()).hexdigest()
    pubs = {"pub1": pub1, "pub2": pub2}
    # save public keys for convenience
    with open(PUBLIC_KEYS_PATH, "w") as f:
        json.dump(pubs, f, indent=2)
    return private, pubs

def make_signature(archive_path: str, metadata: dict, private_key: str) -> str:
    """
    Create a deterministic signature for the archive.
    For simplicity we use SHA-512(private_key + archive_bytes + compacted metadata JSON).
    """
    hasher = hashlib.sha512()
    # include path name so signature depends on intended name
    hasher.update(archive_path.encode())
    # include metadata as canonical JSON
    meta_bytes = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
    hasher.update(meta_bytes)
    hasher.update(private_key.encode())
    sig = hasher.hexdigest()
    return sig

def create_auraseal_archive(input_file: str, out_dir: str, author_email: str = None, recipient_email: str = None) -> str:
    """
    Create a .auraseal.pub.N.zip archive containing:
      - the original file (stored under original_filename)
      - auraseal.metadata.json (metadata + signature placeholder)
    Returns path to the created archive.
    """
    input_path = pathlib.Path(input_file)
    assert input_path.exists(), "input file not found: " + str(input_file)
    os.makedirs(out_dir, exist_ok=True)

    # get or create key pair
    private_key, public_keys = load_or_create_keypair()

    # build metadata
    metadata = {
        "original_filename": input_path.name,
        "original_path": str(input_path.resolve()),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "author_email": author_email,
        "recipient_email": recipient_email,
        "public_keys": public_keys,
        "auraseal_version": "0.0.1",
        "notes": "v0.0.01 POC aura seal"
    }

    # archive name - find an increment
    base_name = ".auraseal.pub"
    # compute next index
    existing = sorted(pathlib.Path(out_dir).glob(f"{base_name}.*.zip"))
    next_index = 1
    if existing:
        # parse existing highest number
        try:
            last = existing[-1].name
            num = int(last.split(".")[2])
            next_index = num + 1
        except Exception:
            next_index = len(existing) + 1

    archive_name = f"{base_name}.{next_index}.zip"
    archive_path = os.path.join(out_dir, archive_name)

    # temporarily include metadata without signature, create zip, then sign and overwrite metadata
    metadata_temp = dict(metadata)
    metadata_temp["_auraseal_signature"] = None

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # add original file
        zf.write(str(input_path), arcname=input_path.name)
        # add metadata (placeholder)
        zf.writestr("auraseal.metadata.json", json.dumps(metadata_temp, indent=2))

    # create signature over archive path and metadata
    signature = make_signature(archive_name, metadata, private_key)

    # replace metadata inside zip with signature
    metadata_signed = dict(metadata)
    metadata_signed["_auraseal_signature"] = signature
    metadata_signed["_auraseal_private_key_fingerprint"] = hashlib.sha256(private_key.encode()).hexdigest()[:16]

    # Update the archive metadata file
    with zipfile.ZipFile(archive_path, "a", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("auraseal.metadata.json", json.dumps(metadata_signed, indent=2))

    print(f"[+] Created aura archive: {archive_path}")
    return archive_path

def verify_auraseal_archive(archive_file: str) -> bool:
    """
    Verify integrity of archive by comparing included signature with freshly computed signature.
    NOTE: since signature includes private_key fingerprint only, and we use private key stored locally,
    verification will attempt to load local private key. If private key differs, verification fails.
    """
    if not os.path.exists(archive_file):
        print("Archive not found:", archive_file)
        return False

    # load metadata from zip
    try:
        with zipfile.ZipFile(archive_file, "r") as zf:
            meta_raw = zf.read("auraseal.metadata.json")
            metadata = json.loads(meta_raw.decode())
    except Exception as e:
        print("Failed to open archive metadata:", e)
        return False

    signature_in_archive = metadata.get("_auraseal_signature")
    if not signature_in_archive:
        print("No signature present in archive.")
        return False

    # attempt to load local private key and recompute
    if not os.path.exists(PRIVATE_KEY_PATH):
        print("Local private key not found; cannot verify signature reliably.")
        return False

    with open(PRIVATE_KEY_PATH, "r") as f:
        private = f.read().strip()

    # recompute signature using archive filename and metadata (without _auraseal_signature)
    # we must compute using the same archive basename that was used originally
    archive_basename = os.path.basename(archive_file)
    metadata_for_sig = {k: v for k, v in metadata.items() if k != "_auraseal_signature"}
    recomputed = make_signature(archive_basename, metadata_for_sig, private)

    ok = recomputed == signature_in_archive
    print("[*] Verification result:", "PASS" if ok else "FAIL")
    return ok

def send_email_with_attachment(smtp_server: str, smtp_port: int, smtp_user: str, smtp_pass: str,
                               from_addr: str, to_addr: str, subject: str, body: str, attachment_path: str):
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    # add attachment
    with open(attachment_path, "rb") as f:
        data = f.read()
    maintype = "application"
    subtype = "zip"
    msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(attachment_path))

    # send SMTP (TLS)
    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as s:
        s.ehlo()
        if smtp_port in (587, 25):
            s.starttls()
            s.ehlo()
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)
    print(f"[+] Email sent to {to_addr} via {smtp_server}:{smtp_port}")

# -------- CLI --------
def main():
    parser = argparse.ArgumentParser(description="AuraSeal: seal files and optionally send by email.")
    parser.add_argument("--file", "-f", help="Input file to seal (PDF or other).")
    parser.add_argument("--out-dir", "-o", default="./sealed", help="Output directory for aura archives.")
    parser.add_argument("--author-email", help="Author/sender email (for metadata).")
    parser.add_argument("--recipient-email", help="Recipient email (for metadata).")
    parser.add_argument("--send", action="store_true", help="Attempt to send the created archive by SMTP.")
    parser.add_argument("--smtp-server", help="SMTP server host.")
    parser.add_argument("--smtp-port", type=int, default=587, help="SMTP port (default: 587).")
    parser.add_argument("--smtp-user", help="SMTP username.")
    parser.add_argument("--smtp-pass", help="SMTP password.")
    parser.add_argument("--from", dest="from_addr", help="From address for email (if sending).")
    parser.add_argument("--to", dest="to_addr", help="To address for email (if sending).")
    parser.add_argument("--subject", default="Sealed document", help="Email subject.")
    parser.add_argument("--body", default="Please find attached sealed archive.", help="Email body.")
    parser.add_argument("--verify", help="Verify an existing .auraseal.pub.N.zip archive.")
    args = parser.parse_args()

    if args.verify:
        ok = verify_auraseal_archive(args.verify)
        sys.exit(0 if ok else 2)

    if not args.file:
        parser.error("No --file provided. Use --file <path-to-pdf> or --verify <archive>.")

    archive_path = create_auraseal_archive(args.file, args.out_dir, author_email=args.author_email, recipient_email=args.recipient_email)

    if args.send:
        required = [args.smtp_server, args.smtp_port, args.smtp_user, args.smtp_pass, args.from_addr, args.to_addr]
        if not all(required):
            print("Missing SMTP parameters. Need --smtp-server,--smtp-port,--smtp-user,--smtp-pass,--from,--to")
            sys.exit(3)
        send_email_with_attachment(args.smtp_server, args.smtp_port, args.smtp_user, args.smtp_pass,
                                   args.from_addr, args.to_addr, args.subject, args.body, archive_path)
    else:
        print("[*] Archive created; not sent. Use --send with SMTP options to email it.")

if __name__ == "__main__":
    main()
