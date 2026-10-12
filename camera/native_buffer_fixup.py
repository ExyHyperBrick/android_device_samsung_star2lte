# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0

from hashlib import sha256
from pathlib import Path
from struct import unpack_from


_BUILD_ID = bytes.fromhex('cd3ce333517fd51d348d56a9e7203f45')
_FUNCTION = b'_ZN7android12ExynosCamera30m_startPictureBufferThreadFuncEv'
_FUNCTION_SIZE = 316
_ORIGINAL_HASH = 'd6ce0c82996cc8ef8fa087bde30a95fbcf2d4f6965fd689b160c745672f64894'
_PATCHED_HASH = '3c21b8b971e99b7aba0d8dad6c032013d7835c012cbb80508db9737a7a29fe5f'
_CALL_OFFSET = 0x98
_CALL = bytes.fromhex('dbf748f9')
_NOPS = bytes.fromhex('00bf00bf')


def _range(data, offset, size):
    if offset < 0 or size < 0 or offset + size > len(data):
        raise ValueError('Truncated S9+ camera ELF')
    return data[offset:offset + size]


def _camera_callsite(data):
    if _range(data, 0, 7) != b'\x7fELF\x01\x01\x01':
        raise ValueError('Expected a little-endian ELF32 camera HAL')
    header = unpack_from('<HHIIIIIHHHHHH', _range(data, 16, 36))
    if header[:3] != (3, 40, 1) or (header[7], header[8], header[10]) != (52, 32, 40):
        raise ValueError('Expected an ARM shared camera HAL')
    segments = [unpack_from('<IIIIIIII', _range(data, header[4] + i * 32, 32))
                for i in range(header[9])]
    sections = [unpack_from('<IIIIIIIIII', _range(data, header[5] + i * 40, 40))
                for i in range(header[11])]

    build_ids = []
    for segment in segments:
        if segment[0] != 4:
            continue
        notes = _range(data, segment[1], segment[4])
        offset = 0
        while offset < len(notes):
            namesz, descsz, kind = unpack_from('<III', _range(notes, offset, 12))
            offset += 12
            name = _range(notes, offset, namesz)
            offset += (namesz + 3) & ~3
            descriptor = _range(notes, offset, descsz)
            offset += (descsz + 3) & ~3
            if name == b'GNU\0' and kind == 3:
                build_ids.append(descriptor)
    if build_ids != [_BUILD_ID]:
        raise ValueError('Unsupported S9+ camera HAL Build ID')

    symbols = []
    for section in sections:
        if section[1] != 11:
            continue
        if section[9] != 16 or section[5] % 16 or section[6] >= len(sections):
            raise ValueError('Invalid camera dynamic symbol table')
        strings = sections[section[6]]
        if strings[1] != 3:
            raise ValueError('Invalid camera dynamic string table')
        names = _range(data, strings[4], strings[5])
        for offset in range(section[4], section[4] + section[5], 16):
            symbol = unpack_from('<IIIBBH', _range(data, offset, 16))
            if symbol[0] >= len(names):
                raise ValueError('Invalid camera symbol name')
            end = names.find(b'\0', symbol[0])
            if end == -1:
                raise ValueError('Unterminated camera symbol name')
            if names[symbol[0]:end] == _FUNCTION:
                symbols.append(symbol)
    if len(symbols) != 1:
        raise ValueError('Missing or ambiguous camera allocation worker')
    symbol = symbols[0]
    if symbol[2] != _FUNCTION_SIZE or symbol[3] != 0x12 or not symbol[1] & 1:
        raise ValueError('Unexpected camera allocation worker symbol')
    if symbol[5] == 0 or symbol[5] >= len(sections):
        raise ValueError('Invalid camera allocation worker section')
    section = sections[symbol[5]]
    start = symbol[1] & ~1
    if not section[2] & 4 or start < section[3] or start + _FUNCTION_SIZE > section[3] + section[5]:
        raise ValueError('Camera allocation worker is outside executable code')
    offsets = [segment[1] + start - segment[2] for segment in segments
               if segment[0] == 1 and segment[6] & 1 and start >= segment[2]
               and start + _FUNCTION_SIZE <= segment[2] + segment[4]]
    if len(offsets) != 1 or offsets[0] != section[4] + start - section[3]:
        raise ValueError('Invalid camera executable segment mapping')
    offset = offsets[0]
    function = _range(data, offset, _FUNCTION_SIZE)
    digest = sha256(function).hexdigest()
    if digest not in (_ORIGINAL_HASH, _PATCHED_HASH):
        raise ValueError('Unsupported camera allocation worker implementation')
    patched = digest == _PATCHED_HASH
    callsite = offset + _CALL_OFFSET
    if _range(data, callsite, 4) != (_NOPS if patched else _CALL):
        raise ValueError('Unexpected camera supplier cleanup instruction')
    return callsite, patched


def fixup_picture_buffers(ctx, file, file_path, fps_fixup, *, tmp_dir=None):
    """Keep live buffers after picture allocation failure; retain normal cleanup."""
    if tmp_dir is None:
        raise ValueError('Camera fixup requires a temporary directory')
    path = Path(file_path)
    original = path.read_bytes()
    callsite, patched = _camera_callsite(original)
    normalized = bytearray(original)
    if patched:
        normalized[callsite:callsite + 4] = _CALL

    candidate = Path(tmp_dir) / 'native-camera' / file.basename
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(normalized)
    fps_fixup.run(ctx, file, str(candidate))
    result = bytearray(candidate.read_bytes())
    callsite, patched = _camera_callsite(result)
    if patched:
        raise ValueError('FPS fixup unexpectedly changed camera cleanup')
    result[callsite:callsite + 4] = _NOPS
    _camera_callsite(result)
    if result != original:
        path.write_bytes(result)
