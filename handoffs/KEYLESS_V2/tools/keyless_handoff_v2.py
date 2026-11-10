#!/usr/bin/env python3
"""TWF/P0-D keyless-to-owner handoff, version 2.

There is NO per-artifact secret for the OWNER to paste. One-time local Windows
X25519 private identity stays inside the Windows user profile. Authors use only
its public identity to encrypt new ZIPs posted to a PUBLIC repo. If a verified
PRIVATE repo is available, prefer direct ZIP delivery instead.

Requires Python cryptography, but not GitHub tokens or a network connection.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import zipfile

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

FORMAT = "TWF_KEYLESS_X25519_AES256GCM_V2"
PUBLIC_FORMAT = "TWF_KEYLESS_RECIPIENT_V2"
PRIVATE_FORMAT = "TWF_LOCAL_ONLY_IDENTITY_V2"
MAX_ZIP_BYTES = 64 * 1024 * 1024
MAX_UNCOMPRESSED = 256 * 1024 * 1024
MAX_MEMBERS = 5000


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def b64(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def unb64(s):
    if not isinstance(s, str) or not s or len(s)>MAX_ZIP_BYTES*2:
        raise ValueError("Invalid base64")
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fp(public_bytes):
    return sha(b"TWF/recipient/V2\x00"+public_bytes)[:32]


def read_json(path, limit=MAX_ZIP_BYTES*2):
    p=Path(path)
    if p.stat().st_size > limit:
        raise ValueError("JSON too large")
    value=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be object")
    return value


def atomic_new(path, payload, secret=False):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd=os.open(str(path), os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600 if secret else 0o644)
    try:
        with os.fdopen(fd,"wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        if secret:
            if os.name == "nt":
                who=subprocess.run(["whoami"], capture_output=True, text=True, check=True).stdout.strip()
                if not who or '\n' in who:
                    raise ValueError("Unable to establish Windows owner")
                subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", who+":(F)"], check=True, capture_output=True)
            else:
                os.chmod(path, 0o600)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def default_identity_path():
    if os.name == "nt":
        root=os.getenv("LOCALAPPDATA")
        if not root:
            raise ValueError("LOCALAPPDATA not set")
        return Path(root)/"TRAP_RAIDERS"/"handoff-v2"/"owner-identity.local.json"
    return Path.home()/".local"/"share"/"trap-raiders"/"handoff-v2"/"owner-identity.local.json"


def verify_zip(zip_bytes):
    import io
    if len(zip_bytes)>MAX_ZIP_BYTES:
        raise ValueError("ZIP size cap exceeded")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        members=z.infolist()
        if len(members)>MAX_MEMBERS:
            raise ValueError("Too many ZIP members")
        names=set()
        total=0
        for f in members:
            name=f.filename
            parts=name[:-1].split("/") if f.is_dir() and name.endswith("/") else name.split("/")
            if (not name or name.startswith("/") or "\\" in name or ":" in name or
                any(p in ("", ".", "..") for p in parts)):
                raise ValueError("ZIP unsafe member path")
            if name in names:
                raise ValueError("Duplicate ZIP member")
            names.add(name)
            if (f.external_attr >> 16) & 0o170000 == stat.S_IFLNK:
                raise ValueError("Symlink ZIP member")
            if f.flag_bits & 1:
                raise ValueError("Encrypted ZIP member")
            if f.file_size>MAX_UNCOMPRESSED:
                raise ValueError("ZIP member too large")
            total+=f.file_size
            if total>MAX_UNCOMPRESSED:
                raise ValueError("Expanded ZIP too large")
            # ZipFile.read validates member CRC. Digest covers raw ZIP bytes.
            z.read(f)
        return {"members":len(members),"expanded_bytes":total}


def enroll(identity, public_out):
    priv=X25519PrivateKey.generate()
    priv_raw=priv.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
    pub_raw=priv.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    key_id=fp(pub_raw)
    private={"format":PRIVATE_FORMAT,"private_key_b64":b64(priv_raw),"recipient_key_id":key_id}
    public={"format":PUBLIC_FORMAT,"recipient_public_key_b64":b64(pub_raw),"recipient_key_id":key_id,
            "intended_repo":"kk051780/toy-wars-factory","purpose":"TRAP_RAIDERS source handoff"}
    identity=Path(identity)
    public_out=Path(public_out)
    if identity.exists() or public_out.exists():
        raise FileExistsError("Identity/public file already exists. Do not rotate silently.")
    atomic_new(identity, canonical(private)+b"\n",secret=True)
    try:
        atomic_new(public_out, canonical(public)+b"\n")
    except BaseException:
        identity.unlink(missing_ok=True)
        raise
    return key_id


def _derive(shared, recipient_pub, ephemeral_pub):
    salt=hashlib.sha256(b"TWF/V2 salt"+recipient_pub+ephemeral_pub).digest()
    return HKDF(algorithm=hashes.SHA256(),length=32,salt=salt,info=b"TWF-X25519-ZIP-HANDOFF-V2").derive(shared)


def seal(zip_path, recipient_path, packet_id, output, *, work_id="p0d-siege-v19"):
    r=read_json(recipient_path,limit=2048)
    if r.get("format")!=PUBLIC_FORMAT:
        raise ValueError("Not a V2 recipient")
    recipient_pub_raw=unb64(r.get("recipient_public_key_b64"))
    if len(recipient_pub_raw)!=32 or r.get("recipient_key_id")!=fp(recipient_pub_raw):
        raise ValueError("Recipient ID mismatch")
    if not packet_id or len(packet_id)>128 or not all(c.isalnum() or c in '._-' for c in packet_id):
        raise ValueError("Invalid packet_id")
    zip_bytes=Path(zip_path).read_bytes()
    analysis=verify_zip(zip_bytes)
    ephemeral=X25519PrivateKey.generate()
    eph_pub=ephemeral.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    recipient=X25519PublicKey.from_public_bytes(recipient_pub_raw)
    shared=ephemeral.exchange(recipient)
    key=_derive(shared,recipient_pub_raw,eph_pub)
    meta={"game_id":"TRAP_RAIDERS","work_id":work_id,"packet_id":packet_id,
          "recipient_key_id":r["recipient_key_id"],"zip_sha256":sha(zip_bytes),
          "zip_bytes":len(zip_bytes),"manifest_entries":analysis["members"]}
    nonce=secrets.token_bytes(12)
    ciphertext=AESGCM(key).encrypt(nonce,zip_bytes,canonical(meta))
    envelope={"format":FORMAT,"meta":meta,"ephemeral_public_key_b64":b64(eph_pub),
              "nonce_b64":b64(nonce),"ciphertext_b64":b64(ciphertext)}
    atomic_new(output,canonical(envelope)+b"\n")
    return meta


def restore(envelope_path, identity_path, output, *, expected_zip_sha=None, expected_packet_id=None):
    e=read_json(envelope_path)
    i=read_json(identity_path,limit=2048)
    if e.get("format")!=FORMAT or i.get("format")!=PRIVATE_FORMAT:
        raise ValueError("Invalid envelope/identity format")
    m=e.get("meta")
    if not isinstance(m,dict) or m.get("game_id")!="TRAP_RAIDERS" or m.get("work_id")!="p0d-siege-v19":
        raise ValueError("Invalid game/work scope")
    if expected_packet_id is not None and m.get("packet_id")!=expected_packet_id:
        raise ValueError("Packet identity mismatch")
    if expected_zip_sha is not None and m.get("zip_sha256")!=expected_zip_sha:
        raise ValueError("Expected archive hash mismatch")
    priv_bytes=unb64(i.get("private_key_b64"))
    if len(priv_bytes)!=32:raise ValueError("Invalid local identity")
    priv=X25519PrivateKey.from_private_bytes(priv_bytes)
    pub_raw=priv.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)
    if i.get("recipient_key_id")!=fp(pub_raw) or m.get("recipient_key_id")!=fp(pub_raw):
        raise ValueError("Wrong recipient identity")
    eph_pub_raw=unb64(e.get("ephemeral_public_key_b64"))
    nonce=unb64(e.get("nonce_b64"))
    if len(eph_pub_raw)!=32 or len(nonce)!=12:raise ValueError("Invalid envelope parameters")
    key=_derive(priv.exchange(X25519PublicKey.from_public_bytes(eph_pub_raw)),pub_raw,eph_pub_raw)
    zip_bytes=AESGCM(key).decrypt(nonce,unb64(e.get("ciphertext_b64")),canonical(m))
    if len(zip_bytes)!=m.get("zip_bytes") or sha(zip_bytes)!=m.get("zip_sha256"):
        raise ValueError("Decrypted archive digest mismatch")
    analysis=verify_zip(zip_bytes)
    if analysis["members"]!=m.get("manifest_entries"):
        raise ValueError("Archive member count mismatch")
    atomic_new(output,zip_bytes,secret=True)
    return m


def main(argv=None):
    ap=argparse.ArgumentParser(description="No pasted keys: one-time local identity, public recipient, encrypted GitHub files")
    sp=ap.add_subparsers(dest="command",required=True)
    p=sp.add_parser("enroll");p.add_argument("--identity",default=str(default_identity_path()));p.add_argument("--public-out",required=True)
    p=sp.add_parser("seal");p.add_argument("--zip",required=True);p.add_argument("--recipient",required=True);p.add_argument("--packet-id",required=True);p.add_argument("--out",required=True)
    p=sp.add_parser("restore");p.add_argument("--in-file",required=True);p.add_argument("--identity",default=str(default_identity_path()));p.add_argument("--out",required=True);p.add_argument("--expected-sha256",required=True);p.add_argument("--packet-id",required=True)
    a=ap.parse_args(argv)
    try:
        if a.command=="enroll":
            print("PUBLIC_RECIPIENT_ID="+enroll(a.identity,a.public_out));print("PUBLIC_RECIPIENT_FILE="+a.public_out)
            print("Private identity saved to local user profile. NEVER upload it.")
        elif a.command=="seal":
            x=seal(a.zip,a.recipient,a.packet_id,a.out);print("SEALED_PACKET="+x["packet_id"]);print("ZIP_SHA256="+x["zip_sha256"])
        else:
            x=restore(a.in_file,a.identity,a.out,expected_zip_sha=a.expected_sha256,expected_packet_id=a.packet_id)
            print("RESTORED_AND_VERIFIED_PACKET="+x["packet_id"]);print("ZIP_SHA256="+x["zip_sha256"])
        return 0
    except Exception as e:
        # Avoid printing any secret or sensitive path content; report error type.
        print("HANDOFF_BLOCKED="+type(e).__name__+": "+str(e)[:180],file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
