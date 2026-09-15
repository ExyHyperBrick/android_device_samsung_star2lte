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
/* Entry: r4=this, r7/r6=cached FPS, r5/r10=requested FPS. */
.syntax unified
.arch armv7-a
.thumb
.text
.global patch_start
.type patch_start, %function
.thumb_func
patch_start:
    cmp.w r10, #60
    bne cached_fps
    mov r0, r4
    bl get_config_mode
    cbnz r0, cached_fps
    movs r6, #30
cached_fps:
    cmp r7, r5
    it eq
    cmpeq r6, r10
    beq.w original_exit
    mov r0, r4
    movs r1, #18
    bl get_mode_value
    cmp r0, #20
    beq update_fps
    mov r0, r4
    movs r1, #20
    bl get_mode_value
    cmp r0, #5
    beq update_fps
    cmp r6, #30
    bhi check_normal
    cmp.w r10, #60
    bne check_normal
    movs r2, #1
    b apply_mode
check_normal:
    cmp r6, #60
    bne update_fps
    cmp.w r10, #30
    bhi update_fps
    movs r2, #0
apply_mode:
    mov r0, r4
    movs r1, #8
    bl set_mode_value
    mov r0, r4
    movs r1, #1
    bl set_restart_stream
update_fps:
    cmp r7, r5
    bne.w original_store
    ldr.w r0, [r4, #0x338]
    cmp r0, r10
    beq.w original_exit
    b.w original_store
    .fill (112 - (. - patch_start)) / 2, 2, 0xbf00
.size patch_start, . - patch_start
