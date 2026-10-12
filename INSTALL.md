# ACNH 3.0.3 | 3440x1440 Ultrawide Mod v3

Adds 3440x1440 ultrawide support to Animal Crossing: New Horizons, allowing the game world to render beyond its original 16:9 aspect ratio.

Corrected v3 (`2026-10-11-ui-sweep`) retains v2's working perspective patch and the prior DAL/minimap fixes. This replacement addresses the reported narrow menu backgrounds and mismatched scene captures around UI panels. **It has passed CPU/static checks; its appearance and behavior still need confirmation in Eden gameplay.**

Download the [compiled v3 mod](https://github.com/Bacondude117/ACNH-3.0.X-Ultrawide/releases/download/v3/ACNH-3.0.3-3440x1440-Eden-v3.zip) or the [complete v3 source ZIP](https://github.com/Bacondude117/ACNH-3.0.X-Ultrawide/releases/download/v3/ACNH-3440x1440-v3-source.zip). The [v2 release](https://github.com/Bacondude117/ACNH-3.0.X-Ultrawide/releases/tag/v2) remains available for rollback.

## Changes in v3

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
- **60/120 FPS patches:** No address overlap found with the locally checked 3.0.3 SpeedFix patches. This is a static conflict check, not a new gameplay compatibility confirmation.
- **Other game builds/emulators:** Unsupported by this release.

## Installation (Eden)

1. Close the game and extract the compiled archive.
2. In Eden, right-click **Animal Crossing: New Horizons** and select **Open Mod Data Location**.
3. Replace your existing v3 folder with the extracted **ACNH 3.0.3 - 3440x1440 Ultrawide - v3** folder, keeping its `exefs` subfolder. If you renamed the old v3 folder, remove or disable that copy so both builds cannot load together. The corrected patch header identifies **2026-10-11 ui-sweep**.
4. In **Configure Game > Add-Ons**, disable every previous ultrawide patch, then enable v3. Keep v2's files as a backup. Folder names alone do not identify the patch version.
5. Set the graphics aspect ratio to **Stretch to Window** and use a 3440x1440 display/window. The patch supplies the projection correction.
6. Restart the game so its executable and layout resources reload.

Only one ultrawide version should be enabled. To roll back, close the game, disable v3, re-enable your saved v2, and restart. No saves are modified by the mod.

## Known issues and testing status

- **Passport rendering artifacts:** Top-left corruption during opening/closing and damaged bottom-right buttons were reported in Eden. The tester reproduced both with **all mods disabled at 16:9**, so they also occur without this patch. Their underlying cause and a workaround remain unconfirmed; v3 does not claim to fix them.
- **Object culling:** Tree pop-in near the upper corners is unchanged. Culling has not been disabled or enlarged globally.
- **Gameplay confirmation pending:** Check all ten newly reported views: Room Sketch tutorial, Chat Log, Island Life 101, Critterpedia, Nook Miles achievements, Pro Camera, passport, DIY, Custom Designs and full map. Scroll lists and change tabs/pages, test centered/right Custom Designs modes and camera filters/frames, and recheck both phone pages, DAL, minimaps, banks, catalogs and decorating transitions. CPU tests cannot verify GPU sampling, compositor behavior, or later game-side position changes.
- **Coverage:** Includes Fade, Load, LoadGoOut, WipeCircle, WipeVisitorDemo, WipeDevice/Load and the five WipeInterior variants. Other specialized transitions remain unverified. Travel illustrations, including the wave artwork, stay centered over the widened backdrop.
- **Menu scope:** The resource audit now covers 102 named layouts/animations, including 47 additional layouts in this replacement. Every menu in the game has not been visually audited. Touch/mouse hit testing and unusual UI modes need in-game testing.
- **Other UI mods:** If another mod changes a targeted layout or animation, that resource will be left unchanged by v3. Its corresponding coverage/position fix may therefore be absent.
- **Performance:** Resource checks run at layout/animation loading. Small scissor and background-copy corrections run when those UI operations occur. Six selected transient UI captures become 34.4% wider while active; the scene camera/render targets and culling policy are unchanged. Runtime performance has not been measured.

## Source and license

The separate `ACNH-3440x1440-v3-source.zip` contains the complete portable builder, readable assembly, pinned requirements, tests, hashes, and audit report. Game executables/assets, keys, saves, emulator settings, and third-party dependencies are not bundled.

To compile from source, follow [BUILDING.md](BUILDING.md) in the repository or source ZIP. It requires Python 3.11 or later and the pinned dependencies in `requirements.txt`; no game files are required to build.

Project source is MIT-0. Dependencies retain their own licenses; see `THIRD_PARTY.md`. No affiliation with Nintendo or Eden is implied.

## Credits

Developed with assistance from GPT-6 Astra.
