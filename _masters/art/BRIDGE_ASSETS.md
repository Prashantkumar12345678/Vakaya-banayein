# Bridge adventure assets

Generated with the built-in image generation tool for HI02H12_L02_S01. Final runtime assets are in `HI02H12_L02_S01/assets/Images/bridges/`.

## Scene prompt set

Use case illustration-story. Single landscape 16:9 BACKGROUND for a polished children's 2.5D bridge-crossing adventure game, intended 1333x750. High quality stylized game environment, warm illustrated cartoon with dimensional rendered materials, soft ambient shadows and atmospheric depth, bright friendly colors, beautiful lighting, playful Indian countryside. NO people, animals, mascots, text, labels, symbols, buttons, UI or watermark. MAIN SUBJECT A LARGE COMPLETE WALKABLE BRIDGE extending left-to-right horizontally across almost the FULL image, from x=9% to x=91%. Camera side view slightly elevated, see broad TOP deck and front thickness, modest perspective depth. The WALKING PATH along the bridge's rear deck edge is a straight horizontal line at EXACTLY y=62% of image height. Deck occupies y=60% to y=71%, horizontal and level. Left and right banks meet path at same y=62%. Bridge is intact, safe, strong and inviting. Show rich scenic river below deck and both banks, distant scenery behind bridge. Upper 30% relatively calm light sky/distant scenery so game HUD overlays read well. Foreground bottom 20% low detail water/bank for option controls overlay. Do not draw any characters or word tiles. 

Scene variants: `wood.webp` — golden wooden planks, sunny meadow; `bamboo.webp` — bamboo poles and lashings, bamboo grove; `rope.webp` — rope suspension bridge and waterfall; `stone.webp` — sandstone arches and village; `log.webp` — round timber logs and forest creek; `hanging.webp` — suspension cables and school garden at sunset.

## Draggable part prompt set

Single isolated draggable BRIDGE REPAIR SECTION for a children's 2.5D adventure game, wide rectangular horizontal object aspect ratio approximately 3.5:1 centered within transparent canvas. Genuine transparent background, no backdrop, shadows only within object, no words or letters or numbers. View slightly elevated from front to see a broad flat TOP FACE occupying 75 percent of object height and a solid dimensional FRONT EDGE below. Large clean empty central top surface for programmatic Hindi word label. Object fills most of canvas width with 8 percent transparent margin. Polished stylized 3D-rendered cartoon materials, friendly rounded edges, bright warm lighting, rich tactile material detail but calm center for reading. No people, tools, UI, frames, or other objects. 

Material variants: `piece_wood.webp` — honey wood grain, rounded ends, four corner bolts; `piece_bamboo.webp` — five green-gold bamboo poles with two rope lashings; `piece_stone.webp` — one bevelled sandstone slab. Hindi words are live UI text, not painted into the textures.

## Walking character

`swiftee_walk.webp`: eight sequential transparent frames, 256×256 each, packed horizontally (2048×256). Generated from the existing Swiftee mascot reference, facing right with alternating feet and opposing arm swing. White bird, blue eyes, orange beak/feet, yellow hoodie, blue shorts and brown satchel. No background, labels or grid. Original generation used a 4×2 sheet; the frames were cropped to alpha bounds, uniformly scaled and aligned to one foot baseline for runtime playback.

Bridge art is 1333×750. Each bridge has a calibrated walking baseline in `BRIDGE_SCENES`; the walking sprite and fitted parts use that baseline. Question content, answer options and narration remain in `card.json`.
