from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path

import test_candidate_b_target0034_archived as archived

HERE = Path(__file__).resolve().parent
PARTS = tuple(
    HERE / 'fixtures' / f'g101_target0034_capsule_v1.part{i:02d}'
    for i in range(1, 7)
)
EXPECTED_PART_SHA256 = (
    '5ef927e1b70d2c07d2919691a52dc79d8928e78fa5a4c3a46f5a99a16f1af18f',
    '3c7022ff829792be3a2c5540e6dd8cd158eaa7af8ec82b788300977d05c70385',
    'f773d3e8640e661b8939e0008b2bc4b005c29cda4941f24287a491538f7478c0',
    '838e404d4010242059c62025af2cf8f4fd1b75613a7cee2ef1a59f7bdd516d8c',
    '9638067f45e8f4838d50a65912aecde85c77524931e1d9e9ed3514edbf74cd10',
    '3123e1b8e76b35895f404770d37843815d795a340b9ec4ab3dcb3ceea42d0ef3',
)
EXPECTED_CONCAT_LENGTH = 16428
EXPECTED_CONCAT_SHA256 = 'bc8c59b9f449dea0ab7ca9f13a7a731816066d1a5b831318ce2a8019c3c94b22'


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('ascii')).hexdigest()


def assemble_capsule() -> Path:
    chunks = []
    for path, expected_sha in zip(PARTS, EXPECTED_PART_SHA256, strict=True):
        text = path.read_text(encoding='ascii').strip()
        if _sha(text) != expected_sha:
            raise AssertionError(f'TARGET0034_CAPSULE_PART_INTEGRITY_FAILED:{path.name}')
        chunks.append(text)

    text = ''.join(chunks)
    if len(text) != EXPECTED_CONCAT_LENGTH:
        raise AssertionError('TARGET0034_CAPSULE_CONCAT_LENGTH_FAILED')
    if _sha(text) != EXPECTED_CONCAT_SHA256:
        raise AssertionError('TARGET0034_CAPSULE_CONCAT_INTEGRITY_FAILED')

    temp_root = Path(os.environ.get('RUNNER_TEMP', tempfile.gettempdir()))
    assembled = temp_root / 'g101_target0034_capsule_v1.assembled.b64'
    assembled.write_text(text, encoding='ascii')
    return assembled


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out')
    args = parser.parse_args()
    archived.CAPSULE = assemble_capsule()
    archived.run(args.out)


if __name__ == '__main__':
    main()
