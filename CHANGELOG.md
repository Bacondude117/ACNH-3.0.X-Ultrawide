# Changes

## v3 publication documentation - 2026-10-11

- Documented the remaining passport transition/button artifacts and the tester's reproduction with every mod disabled at 16:9. Their underlying cause is unresolved, and this release does not claim a fix.
- Prepared the current UI-sweep source and compiled package for GitHub publication with the existing MIT-0 license and provenance. The executable patch is unchanged: `b68345823fe8af80b52413309814bfd6c313cb26410821b5d95104050d11a052`.
- Rebuilt and audited the source/compiled archives, including fresh-source extraction and byte-for-byte reproduction. v2 remains available as the previous release.

## v3 UI sweep replacement - 2026-10-11

- Added a verified background-copy hook at `03A2EABC`, matching horizontal source coordinates to the actual perspective UI projection while preserving orthographic behavior. Removed the previous phone-only resource preprojection so the correction is applied once.
- Expanded selected full-screen UI captures and corrected eight Entire Layout material projectors. Executed the original 3.0.3 copy and material routines to verify coordinate direction and scale, addressing the reported mirrored/repeated strips without disabling masking.
- Expanded backgrounds for DIY, Nook Miles achievements, Critterpedia/detail, full map, passport, Room Sketch/shared dialogs, Chat Log and Island Life 101. Updated 39 embedded background overrides in 13 parent layouts; widening only the shared resource does not cover those instances.
- Moved only the left Custom Designs mode outward; preserved centered/right modes, floating panel size and its independent tooltip. Moved Pro Camera edge groups/frame edges and expanded filters/shutters while retaining the central finder and portrait capture.
- Audited related 3.0.3 background families beyond the screenshots, including closet, character creation, crafting/cooking/remake, room sizing and selected facility/home/cloud-island screens. No blanket UI stretch or global culling change.
- Now 392 numeric deltas across 102 resource names: 81 layouts and 21 animations, with 99 unique byte identities. Grouped replacements reduce the table to 3452 bytes. The complete patch has 995 records and 3980 payload bytes; all code/data remains inside verified padding and v2 camera bytes are unchanged.
- Added 128 capture-hook executions, 32 original copy-coordinate executions, four original material executions/28 samples and independent parsing of 47 additional layouts. Thirteen public tests pass; the fresh source extraction rebuilds the same compiled ZIP.
- Replaced the v3 source/compiled folders and ZIPs after actual-archive audits. Previous v3 retained privately and v2 unchanged. No installed-mod changes or publication performed.
- Status: CPU/static validation passed; new Eden gameplay and performance confirmation are pending. Six transient UI captures become wider while active. Tree culling remains unresolved.

The entries below describe earlier revisions. Their phone-specific capture preprojection is superseded by the shared capture hook above.

## v3 phone/menu replacement - 2026-10-11

- Moved the actual MenuDevice phone panel and its light left by 330 logical units. Previous changes only moved the main-screen phone prompt. Centered demo keys remain centered.
- Corrected phone capture-source X positions and widths by 32/43 so its edge masks sample the scene underneath them. Retained the capture masks and phone page clipping.
- Added a verified hook at `03A308E8` to match perspective UI scissor rectangles to their projected panes. Preserved local/orthographic capture clipping and all v2 camera bytes. This fixes the phone page leak without removing clipping from scrollable lists.
- Expanded only background picture widths in the bank, Poki bank, Catalog/NatteeCatalog/HotelCatalog, associated catalog backgrounds, ClientListBG and WherearenInspect layouts. Foreground geometry and material data stay unchanged.
- Enlarged the five decorating curtain variants uniformly while keeping the corner icon's displayed size. Expanded full-cover WipeDevice/Load mask endpoints to 4410x3408; retained small endpoints and rescaled affected Hermite tangents. Moved these masks to follow the phone; centered app icons remain unchanged.
- Now 232 numeric deltas across 53 resource names (34 layouts, 19 animations, 51 unique byte identities). Resource table: 2656 bytes. Complete patch: 773 records, 3092 payload bytes.
- Built the phone correction separately, then the menu/transition correction. Added 64 public scissor-hook executions, 52 local original-code clipping checks, eight capture-coordinate executions, and parsed geometry/animation checks. Eleven public tests pass.
- Replaced v3 source/compiled folders and ZIPs after fresh-extraction rebuild and actual-archive audit. Previous v3 retained privately; v2 unchanged. No installation or publication performed.
- Status: CPU/static checks passed; the new replacement needs Eden gameplay confirmation. Tree culling remains unresolved.

## v3 correction - 2026-10-11

- Addressed user-reported terrain showing beside the DAL screen. The separate `WipeVisitorDemo` layout was missing from the original v3 list. Uniformly scale only `P_Circle_00` and `P_MaruS_00` by 43/32, expanding their mask coverage and child borders without changing the DAL logo or stripe artwork. The existing animated widths/heights retain their timing and tangents.
- Addressed missing minimap terrain after moving the HUD right. The original screen-space scissor calculation ignores the widened UI projection. Reproduced with the verified 3.0.3 routine: only about 12.7% of the regular minimap's displayed terrain width survived that clip at the tested resting position.
- Remove the single `ScissorOn` property registration only from the regular and cloud-island minimap layouts. Retain the bounded dynamic capture targets (354x290 and 354x350 logical units) and matching display rectangles. No global scissor/culling change.
- Six additional 32-bit deltas across three additional layouts; 57 total deltas across 23 named resources (21 distinct byte sequences). Projection and resource-hook assembly are unchanged.
- Added geometry/property checks and eight optional executions of the original scissor calculation. Rebuilt the DAL correction separately before the combined minimap correction. Rebuilt final archives from a fresh source extraction and audited the actual archive contents.
- Replaced the existing v3 output folders and ZIPs. Preserved the previous v3 privately for rollback/history and left v2 untouched. No installed-mod changes or publication performed.
- Status: corrected build compiles and passes CPU/static checks; corrected DAL/minimap appearance needs in-game confirmation.

## v3 - 2026-10-10

- Retained all four v2 projection records byte-for-byte.
- Added a FLYT load hook at `00268EE0` and FLAN initialization hook at `00260098`, verified against the 3.0.3 executable.
- Added 51 numeric field/keyframe edits across 20 named resources (18 distinct byte sequences).
- Loading: widened three backdrops; uniformly enlarged the two circular-wipe groups; moved edge loading icons right.
- HUD: shifted main-screen edge groups, clock, phone/camera prompts, minimaps, and save icon; widened two key-guide alignment areas. Shifted animated X key values without changing animation times or tangents.
- Used whole-resource fingerprints to avoid applying deltas to unexpected files. Added CPU tests for exact writes, mismatches, repeated loads, register preservation, and relocated code.
- Kept culling unchanged. No global UI scaling, game-asset redistribution, installed-mod changes, or GitHub upload.
- Status: compiled and CPU/static checked; gameplay confirmation pending.

This v3 supersedes the earlier private experimental global UI-camera bypass. That bypass is not present in this release. The original v2 source and compiled archive remain unchanged.
