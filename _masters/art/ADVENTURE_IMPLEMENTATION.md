# Adventure implementation

Six practice scenes retain the SME questions and existing narration/feedback logic. Approved visual samples are under `_previews/adventure-v3/`; actual screenshots, a touch play-through GIF and side-by-side comparisons are under `_previews/adventure-playtest/`.

Interaction is a single tap: accepted material pieces fly to their destination; no drag gestures or second target tap. Keyboard Enter/Space also work. Map, progress dots and speaker controls are absent in adventure play. Original tutorial/guided content remains available.

Artwork is layered: quiet backgrounds, transparent structural objects, blank wood/key/gear pieces and a matching Swifty character. Gate frames remain static while leaves open; the tunnel uses sliding slabs. Swifty walks using a newly generated eight-phase full-alpha animated WebP; a transparent GIF is included. Assets live in `HI02H12_L02_S01/assets/Images/adventure/`; built-in imagegen prompts and source provenance are in `ADVENTURE_ASSETS.json`.

Run `python3 _tools/test_adventure.py` with Playwright and Chrome for all six touch flows, three wrong-attempt scaffolds, correct placement, automatic progression and celebration. Pillow is optional for the recorded GIF. The test saves current game screenshots for comparison. Smaller landscape bounds, keyboard input, cleanup back to guided, and foot placement at all five stair treads were checked separately.

## Journey map

A full-screen approved route map now appears after Play/greeting, before each practice scene, and after the final home gate. Swifty walks between the bridge, door, fork, cave, stairs and house; completed ground nodes receive green checkmarks. The map advances automatically or accepts a tap/Enter after arrival. It has no top map button, six-dot progress strip or speaker control. Question input and narration are gated until it closes. Manual navigation cancels its timers and animation. Explicit `?still=1` skips practice transition maps for static screenshot capture; reduced-motion settings retain a static map.

`python3 _tools/test_adventure_map.py` checks the real Play-button path, a completed bridge leading to the next landmark, the final completed map leading to celebration, and cancellation when leaving a map.

## Original UI mascot

The game and journey map now use the unchanged `assets/UI/sw_explain_still.webp` as their standing Swifty. The earlier painted reinterpretation is no longer used. A new identity-matched flat 2D eight-frame walk is exported as a 4×2 PNG sprite sheet, horizontal runtime WebP strip, animated WebP and GIF under `assets/UI/`. Runtime movement uses CSS `steps(8)` on the strip. `SWIFTY_UI_WALK.json` records the original image hash and generation prompt; `_tools/build_ui_swifty_walk.py` regenerates export formats from the saved master. `_tools/test_ui_swifty.py` verifies original UI hashes, all six idle sprites, and moving frames in both the map and bridge.

## Map landmark placement revision

The six landmark designs retain the approved art direction. The locked door now sits in a low mound with a visible trail around it to the signpost. The staircase connects the cave-side upper trail to a lower landing, followed by a visible trail outside the house wall to its gate. All six ground pads, checkmarks and Swifty foot positions are aligned to the revised artwork. Runtime route waypoints follow the illustrated bridge deck, bends, staircase treads and house approach; movement timing is proportional to distance. `JOURNEY_MAP_PLACEMENT.json` records the final asset source and stage coordinates. The prior map is preserved as `_masters/art/journey_map_before_placement.webp`.

`python3 _tools/test_map_placement.py` verifies all six animated arrivals and checkpoint centers; screenshots are under `_previews/adventure-playtest/map-stop-*.png`.

The map artwork now uses open grassy areas with sparse plants and fewer decorative rocks. The fourth landmark is a short stone tunnel with a visible daylight exit, replacing the blue crystal cave. Pad centers have been realigned to the simplified asset; the six-stop order and existing game interactions are unchanged. Source: `_masters/art/journey_map_simple_tunnel_source.png`.

## Tunnel traversal and complete trail

The map tunnel now has two visible mouths linked beneath one low rock hill. The signpost approach feeds into the left mouth and the right mouth leads to the staircase; there is no foreground bypass. The previously missing door-to-signpost path is now drawn continuously. All six gold pads and runtime routes match the updated source `_masters/art/journey_map_crossing_source.png`. After the tunnel question, the map animates Swifty into the left portal at a smaller perspective scale, occludes him under the roof, and reveals him at the right portal before he reaches the staircase. Movement, opacity, scale and facing share distance-based timing and map disposal. `_tools/test_tunnel_crossing.py` uses a real answer tap and records the traversal in `_previews/adventure-playtest/tunnel-crossing.gif`.

Railway crossing replaces the P5 staircase. The same authored five-word sentence and eight choices remain. Separate raster assets: railway_bg.webp (empty environment), railway_arm.webp (hinged red-white boom), railway_motor.webp (signal/post), railway_tile.webp (metal word tile), railway_frame.webp (sentence housing). Sources and imagegen prompts are in RAILWAY_ASSETS.json and *_source.png. Word text remains live HTML. Tapping fits one word into the next socket. Wrong/partial sentences keep the boom closed. On completion the word panel rises without rotating, the separate boom raises about its right hinge, the signal changes green and the original UI Swifty walks onto the road then away over the tracks using the existing directional sprite sheets. Animation cleanup remains owned by the slide. No new navigation HUD, drag interaction or baked text.

The journey map replaces only the fifth staircase landmark with a railway crossing. journey_map.webp is closed; journey_map_railway_open.webp is shown after P5 and on final completion. Both use the same six checkpoints and connected path. The crossing-to-home route follows the new level road rather than stair treads.
