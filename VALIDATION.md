# Corrected v3 validation record - 2026-10-11

## Version and implementation evidence

Revision: `2026-10-11-ui-sweep`. The local ACNH 3.0.3 main NSO matches the build ID and all segment SHA-256 values in `patch.json`. The FLYT hook at `00268EE0` intercepts the header-length read before section iteration with the resource base in X21. The FLAN hook at `00260098` intercepts resource-pointer storage before section iteration with its base in X19. Both replaced instructions are replayed unchanged. All v2 camera patch bytes remain unchanged. Resource table encoding and its writer were compacted to accommodate the expanded manifest. A new background-copy hook complements the existing UI scissor hook.

Resource fields were identified in the user's local merged base/update RomFS, not ported from old offsets. A private scan decoded 960 layout archives and 22,465 pane records. This replacement contains 392 numeric deltas for 81 layouts and 21 animations (99 distinct resource byte sequences). Original resources remain outside the release. The grouped 3452-byte table fits the verified 3584-byte read-only padding area. The resource writer occupies `03F06ED8..03F06FA0`, the scissor hook `03F06FA0..03F06FDC`, and the capture continuation `03F06FDC..03F06FFC`. The capture entry uses the existing gap at `03F06E58..03F06E80`. All ranges are non-overlapping and within verified executable alignment padding; no additional unverified cave is used. The complete patch has 995 four-byte records (3980 payload bytes).

At 1080 logical units high, 3440:1440 output requires 2580 logical units of width. The additional 660 units mean an edge offset of 330 units, or 440 pixels at 1440p. Backdrops use that width; text, buttons, thumbnails and centered-dialogue geometry are not globally resized.

## DAL correction

The original v3 changed LoadGoOut but omitted the separate WipeVisitorDemo. Its texture-name table identifies LogoDAL and LogoDALAnim_00. This revision changes only the X/Y scales of P_Circle_00 and P_MaruS_00 from 1 to 43/32. The circle and its surrounding child borders expand uniformly. N_Logo_00, its 256x256 logo, and decorative stripe panes retain their original size/position. The DAL animation targets width and height, not these scale fields, so it does not overwrite the correction.

At the closed endpoint, each 1098-unit side border extends 1475.4375 units from the center, beyond the ultrawide half-width of 1290. At the open endpoint, the 2210-unit circular aperture has radius 1484.84375 after scaling, exceeding the approximately 1398.46-unit screen-corner radius. Matching border/circle Hermite curves keep the outside edges beyond the screen through the transition. Timing, animation tangents, and shader/texture assets are unchanged.

## Minimap correction

The screenshot showed correctly positioned icons/frame but terrain clipped to a strip on the right. The 3.0.3 ScissorPane rectangle calculation at `03A308C8..03A30A60` uses the global pane matrix and nominal 1920x1080 layout size without the widened UI projection. Executing that original code for a minimap centered at logical X=1076 returns horizontal bounds [1859,1920] in a 1920-wide render target. The projected terrain spans approximately [1629.02,1892.47]. Only 12.7% of its width survives this extra clip, matching the reported symptom.

The regular and cloud-island inner minimap layouts each have a single-entry user-data block on N_Scissor_00 containing ScissorOn. The pane factory at `03A19A4C..03A19A84` selects ScissorPane if property lookup `03A13940` finds the name; it does not check the property's integer value. This revision changes only that user-data entry count from one to zero. Block length, pane hierarchy, positions, dimensions, and all other properties remain intact.

N_Capture_00 still registers DynamicCaptureOn, and P_Capture_00 still references that capture. Their matching sizes remain 354x290 for the regular map and 354x350 for the cloud map. The capture renderer derives its orthographic projection from those dimensions (`03A2C650..03A2C720`) and creates a bounded render target (`03A2E5D0` onward). Removing the redundant screen-space scissor does not remove capture-target clipping, reposition icons, enlarge the terrain target, or disable game-wide clipping/culling.

## Checks performed

- The capture correction was checked independently against the original copy and material-projection routines before the combined release validation.
- Thirteen public regression tests passed, including exact release bytes, unchanged v2 camera bytes, loader formatting, wrong/truncated NSOs, unknown resources, invalid/conflicting deltas, deterministic ZIPs, targeted UI geometry, scissor and capture hooks.
- 128 projection-hook executions across two load bases, eight ratios, and four flag states.
- 64 original-vs-patched full projection-function comparisons using the verified local executable.
- 4896 generated-resource hook executions covering all 102 manifest entries, both hook adapters, two load bases, four flag states, exact write ranges, mismatch rejection, and repeat-load idempotence.
- 408 additional hook executions using the actual 102 local resources, checking before/after SHA-256 values at two load bases and on repeated loads.
- Eight executions of the original ScissorPane calculation reproduced the old clipping bug at two render sizes, two HUD positions, and regular/cloud-map scales. This demonstrates the old bug, not GPU rendering of the corrected build.
- 64 new scissor-hook executions check conversion, GPR/SIMD/stack/NZCV preservation, two relocation bases, and orthographic passthrough.
- 52 executions of the original ScissorPane rectangle routine with the new hook check phone, map, centered catalog and portfolio dimensions, two viewports, native/wide ratios, scaled panes, and unchanged capture-local/orthographic behavior.
- 128 public capture-hook executions check four aspect ratios, perspective/orthographic paths, four capture sizes (including zero height), two relocation bases and two flag states. GPR/SIMD scratch registers, stack and NZCV are preserved.
- 32 executions of the original background-copy setup check source widths/positions for phone strips, a full-width background and a shifted design-panel strip, across native/wide ratios, orthographic/perspective paths and two scales. Vertical copy coordinates remain unchanged.
- Four executions of the original material-projection block at `00279700..002797B8` verify 28 source/display coordinate samples. The Entire Layout mapping divides by projection scale X, establishing why its new value must be 43/32. No GPU copy or shader sampling is simulated.
- Parsed three DAL/minimap layouts plus 19 phone/menu/wipe layouts. Confirmed preserved foreground/material data, curtain width/height and retained icon size, and 60 Hermite interpolation samples across 12 resized mask segments.
- Parsed 47 additional layouts, validating 39 embedded shared-background overrides and eight capture-material projectors. Geometry checks reject unrelated foreground size/rotation changes. Ten screenshot background families have explicit coverage assertions; Custom Designs mode selection and capture projector direction have regression checks.
- No corrected-v3 write-address overlap with the locally present 3.0.3 60 FPS SpeedFix, 120 FPS SpeedFix, or no-trampled-flowers patches. File presence does not establish enablement or full behavioral compatibility.
- Older ultrawide patches were identified by hash. No installation changes were performed by this correction workflow. Only one ultrawide patch should be enabled.
- v2 source/compiled baseline hashes unchanged. Prior v3 output copies retained privately for modification history.

Both actual archives were checked against explicit allowlists and scanned for credentials/private paths. Only original UTF-8 source/docs, numeric patch data, and reports are included: no game executable/assets, keys/saves, emulator files, caches, private extraction tools, or third-party source/binaries. `SOURCE_SHA256.json` identifies source inputs. `RELEASE_AUDIT.json` records source packaging checks. A fresh extraction passes the tests and rebuilds a byte-identical compiled ZIP using the same optional NSO verification mode.

## NookPhone and clipping correction

MenuDevice is the actual phone panel; MainScreenSmartPhone is its separate HUD prompt. P_Base_00 and P_Light_00 move from X=-360 to -690, including normal In/Out keys. Zero-valued DemoStart/DemoInstall positions remain zero. Panel size, page layout, titles and icons stay unchanged.

The phone uses N_CapDown_00/01 to capture background strips and P_CapMaskDown_00/01 to display them. Stock background-copy setup at `03A2EA4C..03A2EB04` derives normalized source coordinates from the nominal layout width, independently of the widened projection. The earlier phone-specific 32/43 resource preprojection is removed. N_Capture_00 now follows the phone at X=-690, while the child source strips retain their original X/width values. The shared hook at `03A2EABC` multiplies normalized copy width by `abs(m00/m11) * layoutWidth/layoutHeight`, so the original subsequent instructions also produce the matching projected source center. Orthographic copies replay the original division. This applies consistently to other UI panels using that routine; capture property registrations remain intact.

Phone N_Scissor_00 must remain active to hide the other app page. Removing it would leak app icons. The hook at `03A308E8` replaces the original `fdiv s3,s0,s2`, then adjusts the horizontal conversion by `abs(m00/m11) * layoutWidth/layoutHeight` using the current DrawInfo projection matrix at +0x10. Its perspective m33 at +0x4c is zero; orthographic matrices bypass the adjustment. The stock capture-local branch bypasses the hook site entirely. The resulting horizontal conversion is viewportWidth/(1080*aspect), matching the pane projection, while the original vertical, origin, bounds and clipping logic continues unchanged. This affects UI rectangles, not scene culling or camera matrices.

## Menu backgrounds and transitions

The exact-resource edits widen full-width picture layers in MenuMobileBank, MenuMobileBankPoki, Catalog, NatteeCatalog, HotelCatalog, CatalogBG, CatalogGiftBG, NatteeCatalogBG, HotelCatalogBG, ClientListBG and WherearenInspect. Width increases by 660; foreground panes and all material/UV data are unchanged. The repeating background materials retain their existing projection mappings; the patch does not rescale menu text, buttons, thumbnails or list roots. These are targeted families, not a claim that every game menu has been audited.

WipeInterior, WipeInteriorStudio, WipeInteriorWherearenIslands, WipeInteriorCloudIsland and WipeInteriorHotelRoom use eight adjacent curtain columns. N_All_00 scales uniformly by 43/32. The icon is counter-scaled and repositioned so it keeps its original displayed size/Y and moves right by 330. Column intervals overlap across the entire [-1290,1290] span; the enlarged mask height exceeds 1080. Rounded mask shapes are enlarged uniformly rather than horizontally stretched.

WipeDevice and WipeDeviceLoad previously stopped at a 2940x2272 rounded mask centered near X=-361. That leaves the far side exposed on ultrawide. Their mask origin shifts left by 330 to match the phone; only full-cover width/height endpoints expand by 1.5 to 4410x3408. The original phone-sized endpoints remain unchanged. Nonzero Hermite tangents scale with the corresponding segment's changed distance, while key times are retained. Even an ellipse inscribed in the new closed rectangle encloses the far screen corners at the shifted center. Centered app logo/effect panes remain unchanged. This is static coverage evidence, not GPU/shader confirmation.

## Limits and gameplay checklist

Passport follow-up, 2026-10-11: the tester reproduced both the top-left opening/closing corruption and the damaged bottom-right buttons with all mods disabled and Eden set to 16:9 after restarting. These artifacts therefore also occur without v3. This isolates their reproduction from the ultrawide mod; it does not identify the underlying emulator/driver/game cause or prove a workaround. No patch bytes were changed for this report.

The user's screenshots establish remaining coverage and capture artifacts in the previous replacement. **This replacement has not been confirmed in Eden gameplay.** CPU/static checks do not establish compositor/GPU behavior, runtime performance, mouse/touch hit testing, or later game-side coordinate changes. Exact fingerprints intentionally skip layout/animation resources modified by another mod. Six selected UI captures are 34.4% wider while active; their performance impact is unmeasured. Scene render targets and culling are unchanged.

Check the corrected build after completely restarting the game:

1. DAL loading and its opening/closing transition: no exposed terrain beyond the overlay; logo keeps its size and position.
2. Regular and cloud-island minimaps: complete terrain within the frame; icons align; repeated show/hide animations remain correct.
3. NookPhone on both pages and page slides: no mirrored scene strips or escaped icons, original panel size at its new left position; centered introduction/install demos.
4. ABD/Poki bank main and sign-off screens; Nook Shopping and Nook Miles lists; HHP vacation-home portfolio and its opening/closing transitions.
5. Phone app loading/closing masks and decorating curtains: closed masks cover all sides, app logos keep their size/center, curtain icon keeps its size.
6. Boot loading, building entry/exit, boat travel, ordinary circular wipes, clock, camera prompts, save icon, dialogue and inventory.
7. Other enabled mods and unusual camera/multiplayer/DLC modes.
8. All newly reported views: Room Sketch tutorial, Chat Log, Island Life 101, Critterpedia/detail, Nook Miles achievements, Pro Camera, passport, DIY, Custom Designs and full map. Recheck scrolling, tab/page changes, camera filters/frames and opening/closing transitions.
9. Custom Designs left, centered and right modes: only the left mode shifts; no leaked tiles at the panel edges. Full capture masks must match the world behind them without mirrored/repeated strips.
10. Related audited background families, including bulletin board, closets, crafting/cooking/remake, character creation, room sizing and selected facility/home/cloud-island editors.

Tree culling at the upper corners is unchanged and remains unresolved. Specialized transitions beyond the listed layouts remain unverified.

## Additional UI sweep and capture mapping

MenuRecipe, MenuPointQuestList/TopBar, MenuBook/Detail, MenuMapFull and MenuProfileBg contain full-screen background layers whose widths did not cover the wide display. These layers gain 660 logical units; foreground content remains unchanged. The LCmnBg shared resource has three background layers, but 13 parent layouts override their widths in embedded `prt1` entries. All 39 reviewed overrides are updated, including those in Chat Log, Island Life 101, bulletin board, profile dialogs and related cloud-island screens. Changing only LCmnBg would leave these screens narrow.

MenuChatLog, MenuLoadTips, MyDesignList, CloudIslandMyDesignList, RoomSizeBg and CameraGuide each have one selected full-screen capture widened by 660. Eight corresponding Entire Layout projectors in the first four layouts use X scale 43/32. The original material code constructs UVx as `0.5 + x / (referenceWidth * projectionScaleX)`; multiplying this denominator makes the widened source and displayed mask sample the same screen position. Other material projection modes are preserved.

MyDesignList and CloudIslandMyDesignList move only their left-mode N_InOut_01 X key from -95 to -425; centered/right-mode keys and the panel's 822x944 shape remain unchanged. The independent tooltip is not shifted. CameraGuide's side control groups and vertical frame edges move by 330; full-screen filter/frame/shutter layers widen. Its round mode-transition mask scales uniformly. Its 350x350 portrait capture, central finder and photo preview geometry remain unchanged.

The remaining reviewed additions are explicitly listed in `layout_deltas.json`. Width edits target background geometry; there is no blanket rule that stretches every pane, no replacement game artwork and no global culling bypass.
