import base64

import pytest
from app.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from app.schemas.vault import VaultItemCreate
from pydantic import ValidationError

b64 = lambda s: base64.b64encode(s).decode()

HASH = "a" * 64              # имитация hex-хеша
KEY = b64(b"\x01" * 32)      # имитация зашифрованного vault key
SALT = b64(b"\x02" * 16)     # имитация crypto_salt


# --- auth --------------------------------------------------------

def test_register_ok_and_email_normalized():
    req = RegisterRequest(email="  USER@Example.COM ", master_password_hash=HASH,
                          encrypted_vault_key=KEY, crypto_salt=SALT)
    assert req.email == "user@example.com"


def test_register_rejects_bad_email():
    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", master_password_hash=HASH,
                        encrypted_vault_key=KEY, crypto_salt=SALT)


def test_register_rejects_hash_with_whitespace():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@b.co",
                        master_password_hash="a" * 30 + " " + "a" * 30,
                        encrypted_vault_key=KEY, crypto_salt=SALT)


def test_register_rejects_unknown_fields():
    with pytest.raises(ValidationError) as info:
        RegisterRequest.model_validate({
            "email": "a@b.co",
            "master_password_hash": HASH,
            "encrypted_vault_key": KEY,
            "crypto_salt": SALT,
            "nope": 1,
        })
    assert info.value.errors()[0]["type"] == "extra_forbidden"


def test_login_ok():
    LoginRequest(email="a@b.co", master_password_hash=HASH)


def test_change_password_ok():
    ChangePasswordRequest(old_password_hash=HASH, new_password_hash="b" * 64,
                          new_encrypted_vault_key=b64(b"\x03" * 32))


# --- vault -------------------------------------------------------

def test_vault_item_ok():
    item = VaultItemCreate(encrypted_title=b64(b"Gmail"),
                           encrypted_password=b64(b"s3cret"),
                           encrypted_login=b64(b"me@gmail.com"))
    assert item.encrypted_login == b64(b"me@gmail.com")
    assert item.encrypted_url is None
    assert item.title_blind_index is None


def test_vault_item_rejects_non_base64_password():
    with pytest.raises(ValidationError):
        VaultItemCreate(encrypted_title=b64(b"Gmail"),
                        encrypted_password="НЕ base64!")


def test_vault_item_rejects_empty_title_ciphertext():
    with pytest.raises(ValidationError):
        VaultItemCreate(encrypted_title="", encrypted_password=b64(b"p"))


def test_vault_item_rejects_unknown_fields():
    with pytest.raises(ValidationError) as info:
        VaultItemCreate.model_validate({
            "encrypted_title": b64(b"Gmail"),
            "encrypted_password": b64(b"p"),
            "id": 5,
        })
    assert info.value.errors()[0]["type"] == "extra_forbidden"


def test_blind_index_validated_as_hex():
    item = VaultItemCreate(encrypted_title=b64(b"Gmail"),
                           encrypted_password=b64(b"p"),
                           title_blind_index="a" * 64)
    assert item.title_blind_index == "a" * 64
    with pytest.raises(ValidationError):
        VaultItemCreate(encrypted_title=b64(b"Gmail"),
                        encrypted_password=b64(b"p"),
                        title_blind_index="не-hex-строка")
