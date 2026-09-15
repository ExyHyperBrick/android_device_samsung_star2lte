#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#
"""Assemble both FPS fixes and verify the validated payload hashes."""

from hashlib import sha256
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
SPECS = {
    'arm': ('thumbv7-linux-android', 0xff580,
            '1990c6dd4128d5bcaa78a99f6a64a929'
            '0cbb5bd987971f3f908687167f796850', {
        'get_config_mode': 0xff431,
        'get_mode_value': 0x1436e5,
        'set_mode_value': 0x143051,
        'set_restart_stream': 0xff373,
        'original_store': 0xff5f1,
        'original_exit': 0xff62f,
    }),
    'arm64': ('aarch64-linux-android', 0x164b18,
            '2f8ea1866aaa47b608dac1aa85f6bc7d'
            '433add078531ec0eecc85aa61709241c', {
        'get_config_mode': 0x1648d8,
        'get_mode_value': 0x1c7178,
        'set_mode_value': 0x1c6918,
        'set_restart_stream': 0x164760,
        'original_store': 0x164bc4,
        'original_exit': 0x164c14,
    }),
}


def main():
    with TemporaryDirectory(prefix='starlte-camera-fps-') as directory:
        for arch, (target, offset, expected, symbols) in SPECS.items():
            stem = 'restore_fps_mode_' + arch
            output = Path(directory) / stem
            subprocess.run([
                'clang', '--target=' + target, '-c',
                str(ROOT / (stem + '.S')),
                '-o', str(output.with_suffix('.o')),
            ], check=True)
            subprocess.run([
                'ld.lld', '--entry=patch_start', '--image-base=0',
                '--section-start=.text=' + hex(offset),
                '-o', str(output.with_suffix('.elf')),
                str(output.with_suffix('.o')),
                *['--defsym=' + k + '=' + hex(v)
                  for k, v in symbols.items()],
            ], check=True)
            subprocess.run([
                'llvm-objcopy', '--only-section=.text', '-O', 'binary',
                str(output.with_suffix('.elf')),
                str(output.with_suffix('.bin')),
            ], check=True)
            result = output.with_suffix('.bin').read_bytes()
            if sha256(result).hexdigest() != expected:
                raise RuntimeError(f'{arch}: FPS payload mismatch')
            print(f'{arch}: {len(result)} bytes match')


if __name__ == '__main__':
    main()
