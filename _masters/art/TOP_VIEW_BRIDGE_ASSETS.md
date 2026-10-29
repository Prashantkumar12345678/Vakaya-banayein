# Top-view bridge adventure assets

All assets were generated with the built-in image generation tool and saved under `HI02H12_L02_S01/assets/Images/bridges_top/`.

The camera is strictly overhead throughout: environment maps, transparent deck layers, repair panels and an eight-frame character walk cycle. Live Hindi labels are rendered by the game so the asset text remains readable and matches the questions.

## Environment prompt

Use case illustration-story. Production BACKGROUND ONLY for a polished children's 2.5D bridge repair game. Wide 16:9 landscape 1333x750. STRICT DIRECTLY OVERHEAD TOP-DOWN camera looking straight down at ground and water, orthographic game map. NO sky, horizon, mountains in elevation, side-view buildings or perspective vanishing point. No bridge, walkway, people, animals, UI, words, letters, numbers or watermark. A broad beautiful river runs VERTICALLY from top to bottom through the central 60 percent of canvas, left bank at x=22 percent and right bank at x=82 percent. Both banks are solid walkable ground at far left and right with simple paths reaching the water edge around y=52 percent. Leave the horizontal central strip y=38 to 66 percent open water and quiet bank landings: a separate horizontal bridge asset will be overlaid here. Detailed but readable premium stylized 3D game-map materials, soft ambient occlusion, rounded forms, warm sunlight from top-left, rich water reflections, 2D cartoon-friendly color palette. Gentle foam, ripples and submerged stones. Keep top 24 percent and bottom 18 percent relatively calm for interface overlays. Plants cluster mainly in corners, avoid clutter in central gameplay area. 

Variants: meadow, bamboo grove, rocky canyon, village, forest creek and school courtyard destination. Files: `bg_meadow.webp`, `bg_bamboo.webp`, `bg_canyon.webp`, `bg_village.webp`, `bg_forest.webp`, `bg_school.webp` (1333×750).

## Bridge deck prompt

Use case game-asset. ONE isolated complete HORIZONTAL BRIDGE DECK for a premium children's 2.5D game. GENUINELY TRANSPARENT background. STRICT 90-degree overhead orthographic TOP VIEW, looking STRAIGHT DOWN onto the WALKING SURFACE. NO side view, front elevation, vertical pillars, undersides, arches underneath, vanishing point or isometric angle. Long horizontal rectangle overall 5:1 width:height, running left-to-right, centered in a wide landscape canvas. A BROAD FLAT WALKWAY fills the center 70 percent of deck height. Thin low railings/parapets ONLY along the upper and lower long edges, visible as top-facing strips. Clear flat approach ends on left and right. The full bridge deck is one continuous intact rectangle with NO holes. Entire object visible with transparent margin. Soft bevels, fine material detail, ambient occlusion and subtle dimensional shadows matching TOP-DOWN game-map assets. No background scene, river, banks, rocks, foliage, people, mascots, text, labels, letters, numbers, arrows, UI or watermark. Surface must be calm and readable, no objects on walking path. 

Variants: golden wooden cross-planks, bamboo poles and lashings, wooden slats with rope edges, sandstone paving and parapets, parallel timber logs, golden planks with teal suspension ropes. Files: `deck_wood.webp`, `deck_bamboo.webp`, `deck_rope.webp`, `deck_stone.webp`, `deck_log.webp`, `deck_hanging.webp` (1120×220, transparent). Low-alpha generator margins are trimmed using an alpha threshold of 32 before sizing.

## Repair panel prompt

Use case game-asset. A single wide RECTANGULAR BRIDGE REPAIR PANEL viewed STRICTLY FROM DIRECTLY ABOVE, 90-degree overhead orthographic. GENUINE TRANSPARENT background. Approximately 3:1 width:height object, square corners with slight rounded bevel, long axis horizontal. Only the TOP FACE is visible, no front edge, no side thickness, no isometric or slanted perspective. Centered, entire object visible with a small transparent margin. Fine premium stylized 3D top-down material texture and soft bevel highlights, clean calm blank center for a Hindi word to be overlaid in code. No words, letters, numbers, labels, UI, tools, people, shadows outside object or other objects. 

Variants: three wooden boards and corner screws; six bamboo poles with rope lashings; one sandstone slab. Files: `part_wood.webp`, `part_bamboo.webp`, `part_stone.webp` (600×240, transparent).

## Character animation

`swiftee_walk.webp` (2048×256, eight 256×256 transparent frames). Prompt: strict directly overhead view of the reference white bird, yellow hoodie, blue shorts, orange feet and brown satchel, walking screen-right with alternating feet and opposite arm/wing swings. Eight equal cells, no labels, consistent orientation and scale. The generation sheet was 4×2, then uniformly normalized and packed horizontally.

## Sketch layout and camera sequence

An establishing side-view illustration from `assets/Images/bridges/` is shown first. A 2.4-second perspective-transform and blend transition then reveals the overhead play scene. Narration and fitting controls start after that transition; reduced-motion mode opens the overhead layout directly.

The deck rails are at x=146, y=310, width=1120, height=220. The sentence itself forms the walkway at y=335, height=170. Every sentence word gets a vertical panel. A two-word cloze option such as “सो रही” spans two connected panels while retaining its original answer option and narration timings. Empty panels remain transparent, revealing the environment beneath. The picture is inside a thought bubble above Swiftee. Options below use the same material and vertical panel design.

The overhead walking centerline is y=420. Swiftee uses a standing illustration while thinking and the overhead walk-cycle atlas during crossing.

## Vertical panel additions

`part_wood_vertical.webp` and `part_bamboo_vertical.webp` are 320×360 transparent assets, generated with the built-in image tool. Prompt: one square bridge-word panel viewed directly overhead, made of three long boards/poles running vertically top-to-bottom, fine game material detail, calm blank center, no text or background. Wood uses honey-golden grain and four corner nails; bamboo uses golden-green poles and tan lashings at the upper/lower ends.
