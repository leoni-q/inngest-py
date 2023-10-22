from .transforms import hash_signing_key


def test_hash_signing_key() -> None:
    signing_key = "signkey-prod-568c4116828e6e8384a554153722df93022e5cd29a6c2d1b0444a19a807ff315"
    expectation = (
        "2e64ca0edc850db32ff684f967822c828f99cf57862e43205fdcf2eff8d95180"
    )
    assert hash_signing_key(signing_key) == expectation
