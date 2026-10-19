# ACNH 3.0.3 | 3440x1440 Ultrawide Mod v4

Adds 3440x1440 ultrawide support to Animal Crossing: New Horizons, allowing the game world to render beyond its original 16:9 aspect ratio.

v4 retains the working v2 projection and v3 loading, HUD, minimap, and menu corrections, and fixes the cause of terrain, tree, grass and item pop-in at the sides and far corners of the screen: the game's field ranges were sized for a 16:9 view. **The assembly, CPU checks and runs of the original 3.0.3 functions pass; the in-game result and performance still need confirmation in Eden.**

The v4 compiled archive and portable source ZIP are delivered as local output files; v4 has not been published to GitHub.

## v4 pop-in fix: wider field ranges

ACNH 3.0.3 decides what exists around the camera using rectangles of 5-meter island cells, centered on the camera focus. The sizes come from the game's own field parameters, which are tuned for a 16:9 view:

- **Create range** (`mCreateRangeLeft/Right/Near/Far/Tilt`, function `013A2864`): terrain cells are only tested and drawn inside it, and field content is created inside it.
- **Tree and item areas** (`mTreeArea*` and `mArea*`, function `01125DDC`, built four times per update): trees, weeds and items are kept only inside these.

Each rectangle narrows toward the bottom of the screen (the Tilt term). Outside them, objects simply do not exist yet, so on a 43:18 display they popped in at both sides and, with the camera tilted toward the horizon, in the far corners.

The normal camera always faces north, so world X is screen-horizontal. v4 multiplies only the horizontal terms (Left, Right and Tilt) of all three rectangles by **1.5**: the 43:18 / 16:9 ratio (1.34375) plus a margin for cell rounding and object footprints. Near/Far depth, the frustum tests, curvature and LOD checks are unchanged.

Revision 3 has two more fixes. Testing revision 2 still showed see-through ground in the far corner and grass popping in at the sides:

- **Field-unit pool:** each ground, grass, cliff, river and path piece that is drawn takes a slot from one pool, which the game sizes at load from `FieldUnitModelParam.mUnitMax` (code default 2000). When the pool runs out, the extra pieces all reuse slot 0, so they vanish. A 43:18 view shows about 1.34x as many pieces as 16:9, so the far corners ran out of slots. v4 doubles the pool once at load time (`01462BB4`). This costs a little extra memory and no per-frame work.
- **Terrain cell groups:** these are now bounded by their full 3D half-diagonal before the game's sphere/frustum test (`013A37B4`), so partly visible corner groups are kept. The test itself still runs.

- Earlier v4 attempts (actor category bounds, and widening only the create range) are superseded. In-game tests showed the create range alone left trees and items popping in the back corners.
- To make room in the executable's free space, the v2 aspect getter and matrix hooks were rewritten as shorter routines. They produce the same aspect values and matrices; CPU tests and 64 full-matrix comparisons against the original game code confirm this.
- Tests run every hook on its own at two load addresses. Optional checks run the original 3.0.3 create-range and tree/item-area functions end to end, unpatched and patched. The patched results equal the original functions given 1.5x Left/Right/Tilt parameters, and every depth bound is unchanged.

## Retained v2/v3 features

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

## Known issues and testing status

- **Passport rendering artifacts:** Top-left corruption during opening/closing and damaged bottom-right buttons were reproduced with all mods disabled at 16:9. They occur without this patch; the cause remains unconfirmed.
- **Outdoor object visibility:** side-edge and back-corner pop-in should now be covered, including see-through ground and grass, with the camera tilted toward the horizon. Please confirm in Eden on a busy part of the island. If anything still pops in, note whether it is terrain, grass, trees, or items.
- **Gameplay confirmation pending:** Check outdoor tree visibility with the normal camera, then recheck Room Sketch, Chat Log, Island Life 101, Critterpedia, Nook Miles achievements, Pro Camera, passport, DIY, Custom Designs, full map, phone pages, DAL, minimaps, banks, catalogs and decorating transitions. CPU tests cannot verify GPU sampling, compositor behavior or later game-side position changes.
- **Coverage:** Includes Fade, Load, LoadGoOut, WipeCircle, WipeVisitorDemo, WipeDevice/Load and the five WipeInterior variants. Other specialized transitions remain unverified. Travel illustrations, including the wave artwork, stay centered over the widened backdrop.
- **Menu scope:** The resource audit now covers 102 named layouts/animations, including 47 additional layouts in this replacement. Every menu in the game has not been visually audited. Touch/mouse hit testing and unusual UI modes need in-game testing.
- **Other UI mods:** If another mod changes a targeted layout or animation, that resource will be left unchanged. Its corresponding coverage/position fix may therefore be absent.
- **Performance and object count:** the widened ranges keep up to about 50% more island width active, so more terrain cells, trees and items exist at once. That is inherent to ultrawide. Ground and grass now get twice the stock pool. Placed items still use the game's fixed 200-actor furniture pool (`FtrActorMgr`), so a very dense island could still reach that limit. Frame time and dense-area behavior have not been measured. Six selected transient UI captures become 34.4% wider while active.

## Source and license

The separate `ACNH-3440x1440-v4-source.zip` contains the complete portable builder, readable assembly, pinned requirements, tests, hashes, and audit report. Game executables/assets, keys, saves, emulator settings, and third-party dependencies are not bundled.

To compile from source, follow [BUILDING.md](BUILDING.md) in the repository or source ZIP. It requires Python 3.11 or later and the pinned dependencies in `requirements.txt`; no game files are required to build.

Project source is MIT-0. Dependencies retain their own licenses; see `THIRD_PARTY.md`. No affiliation with Nintendo or Eden is implied.

## Credits

Developed with assistance from GPT-6 Astra.
