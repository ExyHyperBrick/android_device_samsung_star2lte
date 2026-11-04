#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-FileCopyrightText: 2026 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from camera.native_buffer_fixup import fixup_picture_buffers

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = [
    'device/samsung/exynos9810-common',
    'hardware/samsung_slsi-linaro/exynos',
    'hardware/samsung_slsi-linaro/graphics',
    'vendor/samsung/exynos9810-common',
]

_camera_fence_spec = spec_from_file_location(
    'exynos9810_camera_fence',
    Path(__file__).parent.parent / 'exynos9810-common' / 'camera' / 'fixups'
        / 'patch_camera_fence.py',
)
_camera_fence_fixup = module_from_spec(_camera_fence_spec)
_camera_fence_spec.loader.exec_module(_camera_fence_fixup)

blob_fixups: blob_fixups_user_type = {
    'vendor/lib/lib_SoundBooster_ver900.so': blob_fixup()
        .add_needed('libcompiler_rt.so')
        .add_needed('libc++.so'),
    'vendor/lib64/lib_SoundBooster_ver900.so': blob_fixup()
        .add_needed('libc++.so'),
    'vendor/lib/libexynoscamera3.so': blob_fixup()
        .call(
            fixup_picture_buffers,
            blob_fixup().patch_file('camera/fhd60-arm'),
        )
        .call(_camera_fence_fixup.fixup, need_tmp_dir=False)
        .add_needed('libshim_camera_fence.so'),
    'vendor/lib64/libexynoscamera3.so': blob_fixup()
        .patch_file('camera/fhd60-arm64')
        .call(_camera_fence_fixup.fixup, need_tmp_dir=False)
        .add_needed('libshim_camera_fence.so'),
    (
        'vendor/lib/libwrappergps.so',
        'vendor/lib64/libwrappergps.so',
    ): blob_fixup()
        .replace_needed('libvndsecril-client.so', 'libsecril-client.so'),
    'vendor/lib64/libkeymaster_helper_vendor.so': blob_fixup()
        .replace_needed('libcrypto.so', 'libcrypto-v33.so'),
}

module = ExtractUtilsModule(
    'star2lte',
    'samsung',
    namespace_imports=namespace_imports,
    add_firmware_proprietary_file=False,
    blob_fixups=blob_fixups,
)

if __name__ == '__main__':
    utils = ExtractUtils.device_with_common(
        module, 'exynos9810-common', module.vendor
    )
    utils.run()
