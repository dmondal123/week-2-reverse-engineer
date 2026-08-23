from rag_compare.identity import chunk_id, document_id, sha256_bytes


def test_same_source_and_bytes_have_stable_document_and_chunk_ids():
    source_id = "travel-wifi-current"
    payload = b"hotel Wi-Fi is reimbursable"
    content_hash = sha256_bytes(payload)

    document = document_id(source_id, content_hash)
    chunk = chunk_id(document, 0, len(payload), payload.decode("utf-8"))

    assert document == document_id(source_id, content_hash)
    assert chunk == chunk_id(document, 0, len(payload), payload.decode("utf-8"))


def test_changed_bytes_change_content_document_and_chunk_ids_but_not_source_id():
    source_id = "travel-wifi-current"

    old_payload = b"limit $25"
    new_payload = b"limit $30"

    old_hash = sha256_bytes(old_payload)
    new_hash = sha256_bytes(new_payload)

    old_document = document_id(source_id, old_hash)
    new_document = document_id(source_id, new_hash)

    assert source_id == "travel-wifi-current"
    assert old_hash != new_hash
    assert old_document != new_document
    assert chunk_id(old_document, 0, len(old_payload), old_payload.decode()) != (
        chunk_id(new_document, 0, len(new_payload), new_payload.decode())
    )


def test_identity_does_not_depend_on_framework_name():
    source_id = "source-a"
    content_hash = sha256_bytes(b"same bytes")

    # Framework labels are metadata only, and intentionally not identity inputs.
    identities_by_framework = {
        framework_name: (document_id(source_id, content_hash),)
        for framework_name in ("haystack", "llamaindex")
    }

    assert identities_by_framework["haystack"] == identities_by_framework["llamaindex"]
