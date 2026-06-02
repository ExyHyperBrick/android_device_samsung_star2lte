#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

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

blob_fixups: blob_fixups_user_type = {
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
