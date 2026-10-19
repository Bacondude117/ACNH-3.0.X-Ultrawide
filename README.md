# ACNH 3.0.3 | 3440x1440 Ultrawide Mod v4

Adds 3440x1440 ultrawide support to Animal Crossing: New Horizons, so the game world renders across the full 43:18 screen instead of the original 16:9 view.

v4 keeps the v2 projection and the v3 loading, HUD, minimap and menu fixes. It adds a fix for terrain, trees, grass and items popping in at the sides and far corners of the screen. The game's field ranges were sized for a 16:9 view.

**Downloads:** [compiled v4 mod](https://github.com/Bacondude117/ACNH-3.0.X-Ultrawide/releases/download/v4/ACNH-3.0.3-3440x1440-Eden-v4.zip) · [complete v4 source ZIP](https://github.com/Bacondude117/ACNH-3.0.X-Ultrawide/releases/download/v4/ACNH-3440x1440-v4-source.zip). The [v3](https://github.com/Bacondude117/ACNH-3.0.X-Ultrawide/releases/tag/v3) and [v2](https://github.com/Bacondude117/ACNH-3.0.X-Ultrawide/releases/tag/v2) releases remain available for rollback.

Patch SHA-256: `0633440e57dd94ec91f7b053d561e7d42a114e11032e068a70b3ee1c122cbf0a`

## What's new in v4

ACNH 3.0.3 only builds what lies inside a few rectangles of 5-meter island cells around the camera, and their sizes were tuned for 16:9. On a 43:18 screen, the sides and far corners fell outside them. v4 changes four things:

- **Wider field create range** (`mCreateRange*`, function `013A2864`). This range controls which terrain cells are drawn and which field content is created. v4 multiplies only its horizontal terms (Left, Right and the near-edge Tilt) by 1.5. That covers the 1.34375x wider view plus a margin. Depth is unchanged.
- **Wider tree and item areas** (`mTreeArea*` / `mArea*`, function `01125DDC`). These control where trees, weeds and items exist. Their horizontal terms get the same 1.5x factor.
- **Larger ground/grass pool.** Every ground, grass, cliff, river and path piece that is drawn uses a slot in a pool sized by `FieldUnitModelParam.mUnitMax` (default 2000). When the pool runs out, the extra pieces vanish. That was the cause of see-through ground in the far corners. v4 doubles the pool once at load. This uses a little more memory and adds no per-frame work.
- **Correct corner bounds for terrain groups.** Terrain cell groups now use their full 3D half-diagonal as the radius for the game's own sphere/frustum test, so partly visible corner groups are kept.

The v2 aspect getter and matrix hooks were also rewritten as shorter routines to free code space. They produce identical results, confirmed by 64 full-matrix comparisons against the original game code.

## Retained from v2/v3

- Fade and loading backdrops expand from 1920 to 2580 logical units, covering 3440 pixels at 1440p. Travel artwork and centered loading tips retain their size and position.
- Circular transitions scale uniformly in both directions, covering the wider display while keeping the circular opening round.
- The separate DAL visitor/loading wipe now expands its circular mask and surrounding coverage. The DAL logo and decorative stripe artwork keep their original sizes and positions.
- Minimap, clock, NookPhone/camera prompts, save icon, and selected main-screen edge controls move outward. Their existing sizes are retained.
- The regular and cloud-island minimaps no longer apply the extra 16:9 screen-space clipping rectangle that cut off the terrain. Their bounded capture textures, displayed sizes, and edge positions are retained.
- Animated NookPhone/camera and minimap positions receive the same offset as their starting positions. Bottom key-guide alignment areas are widened without scaling their contents.
- The actual NookPhone panel now moves left by 440 display pixels at 1440p. Its background-capture strips sample the corresponding screen area, and its page clip follows the widened projection. Centered phone introduction/install states remain centered.
- ABD and Poki bank backgrounds, sign-off backgrounds, Nook Shopping/Nook Miles catalog layers, related catalogs, and the vacation-home portfolio background/header extend across the wider display. Menu text, buttons, lists and thumbnails keep their original geometry and central layout.
- Decorating curtains cover the wider screen through a uniform enlargement of their masks, while their corner icon keeps its original size. Phone app transition masks retain their small opening/closing endpoint and expand further at the full-cover endpoint; their centered logo remains unchanged.
- UI scissor rectangles now follow the active perspective projection. Clipping remains enabled; capture-local and orthographic clipping pass through unchanged.
- Background-copy rectangles now follow the active UI projection too. This replaces the earlier phone-only resource adjustment and covers other panels using the same game routine. Full-width capture masks also receive matching texture-projection coordinates, addressing repeated or mirrored scene strips around Chat Log, Island Life 101 and Custom Designs.
- DIY, Nook Miles achievements/header, Critterpedia/detail, the full map and passport backgrounds extend to the display edges. Their cards, lists, insects, map content and passport remain at their original sizes.
- Shared dialog backgrounds and 39 embedded background overrides expand together, including Room Sketch's tutorial backdrop, Chat Log, Island Life 101, the bulletin board and related screens. Centered dialog contents remain centered.
- The left Custom Designs panel moves outward without resizing it or moving its centered/right-side modes. Pro Camera's side controls and frame edges move outward; full-screen filters, shutters and transition coverage expand. The portrait/photo capture and central finder remain unchanged.
- Additional reviewed backgrounds cover closet, character creation, selected facility/home/cloud-island editors, crafting/cooking/remake, custom-design editing, room sizing and related shop screens. The exact per-resource changes are recorded in the source manifest; this is not a claim that every game screen has been visually tested.
- Centered dialogue, timer and loading-tip geometry is unchanged. There is no global UI stretch.

The compiled mod contains an ExeFS patch. It adjusts matching resources in memory; it does not replace game assets on disk. A whole-resource fingerprint prevents a changed or unexpected layout from receiving the deltas.

## Compatibility

- **Game:** ACNH 3.0.3, title ID `01006F8002326000`
- **Main build ID:** `FF1D1C05670DB6021C85B624A710B963`
- **Emulator target:** Eden desktop, using its page-aligned NSO loader
- **Display:** 3440x1440 landscape, exactly 43:18 (commonly called 21:9)
- **Other patches:** Static address comparison against the locally audited 3.0.3 60/120 FPS SpeedFix and no-trampled-flowers patches found no write overlap. Mods that change the field range parameters will be multiplied by the same factor. The old v2 ultrawide patches overlap by design; disable them before enabling v4. Static checks do not establish behavioral compatibility.
- **Other game builds/emulators:** Unsupported by this release.

## Installation (Eden)

1. Close the game and extract the compiled archive.
2. In Eden, right-click **Animal Crossing: New Horizons** and select **Open Mod Data Location**.
3. Extract the **ACNH 3.0.3 - 3440x1440 Ultrawide - v4** folder, keeping its `exefs` subfolder. Disable any older ultrawide patch copies so only one version loads.
4. In **Configure Game > Add-Ons**, enable v4. Keep v2's files as a backup. Folder names alone do not identify the patch version.
5. Set the graphics aspect ratio to **Stretch to Window** and use a 3440x1440 display/window. The patch supplies the projection correction.
6. Restart the game so its executable and layout resources reload.

Only one ultrawide version should be enabled. To roll back, close the game, disable v4, re-enable your saved v2, and restart. No saves are modified by the mod.

## Known issues

- **Grass and terrain at the edges:** v4 removes most of the pop-in, including the see-through ground in the far corners. In testing, grass can still pop in at the screen sides, and terrain can still glitch at some camera angles while sprinting. These are being investigated for a future version.
- **Passport rendering artifacts:** Corruption at the top left during opening/closing and damaged buttons at the bottom right also happen with all mods disabled at 16:9, so they are not caused by this patch.
- **Object limits:** The wider ranges keep up to about 50% more island width active, which is inherent to ultrawide. Placed items still use the game's fixed 200-actor furniture pool, so a very dense island could reach that limit. Frame time has not been measured.
- **Menu scope:** 102 layouts/animations are covered, but not every game screen has been visually tested. If another mod changes one of the targeted layouts, that layout is left unchanged and its fix will be missing.

## Source and license

The separate `ACNH-3440x1440-v4-source.zip` contains the complete portable builder, readable assembly, pinned requirements, tests, hashes, and audit report. Game executables/assets, keys, saves, emulator settings, and third-party dependencies are not bundled.

To compile from source, follow [BUILDING.md](BUILDING.md) in the repository or source ZIP. It requires Python 3.11 or later and the pinned dependencies in `requirements.txt`; no game files are required to build.

Project source is MIT-0. Dependencies retain their own licenses; see `THIRD_PARTY.md`. No affiliation with Nintendo or Eden is implied.

## Credits

Developed with assistance from GPT-6 Astra (v2–v3) and Claude (v4).
