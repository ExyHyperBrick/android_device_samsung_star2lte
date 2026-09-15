/*
 * SPDX-FileCopyrightText: 2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */
/*
 * Restore normal -> 60 fps mode after stream reconfiguration.
 * Keep the original frame, FPS adjustment, storage and logging.
 * Only the local cached-FPS comparison changes; vendor exceptions
 * still apply, and an already valid 60 fps mode stays unchanged.
 */
/* Entry: x19=this, w25/w24=cached FPS, w21/w20=requested FPS. */
.text
.global patch_start
.type patch_start, %function
patch_start:
    cmp w20, #60
    b.ne cached_fps
    mov x0, x19
    bl get_config_mode
    cbnz w0, cached_fps
    mov w24, #30
cached_fps:
    cmp w25, w21
    ccmp w24, w20, #0, eq
    b.eq original_exit
    mov w1, #18
    mov x0, x19
    bl get_mode_value
    cmp w0, #20
    b.eq update_fps
    mov w1, #20
    mov x0, x19
    bl get_mode_value
    cmp w0, #5
    b.eq update_fps
    cmp w24, #30
    b.hi check_normal
    cmp w20, #60
    b.ne check_normal
    mov w2, #1
    b apply_mode
check_normal:
    cmp w24, #60
    b.ne update_fps
    cmp w20, #30
    b.hi update_fps
    mov w2, #0
apply_mode:
    mov x0, x19
    mov w1, #8
    bl set_mode_value
    mov x0, x19
    mov w1, #1
    bl set_restart_stream
update_fps:
    cmp w25, w21
    b.ne original_store
    ldr w8, [x19, #0x390]
    cmp w8, w20
    b.eq original_exit
    b original_store
    .fill (172 - (. - patch_start)) / 4, 4, 0xd503201f
.size patch_start, . - patch_start
