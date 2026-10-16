"""写庄园未建房间的 v3 生图提示词（10-16）：每张一个 txt，放进各设计包的 prompts/，文件名 <房间>_<视角>-v3.txt。
v3 与 v2 的区别：门窗、楼梯位置按 T-039 v1 平面写死；风格锁定为已建成的客房 / 暗房 / 温室；艾瑞斯的画按 10-15 定的抽象画风。
需求总表见 docs/关卡/补图需求-v3.md。

    python3 tools/art/write_v3_room_prompts.py
"""
import os
ROOT = '/Users/qizhi_dong/Projects/DigitalMedia/assets/2d/'

HEAD = ("Use case: historical-scene interior concept for 3D modeling reference. ONE finished environment painting, landscape 16:9. "
        "Premium tactile painterly realism, fine gouache, coherent architectural perspective, plausible 1926 English Cotswold country manor "
        "(Jacobethan honey-limestone house, thick stone walls). Natural period light with restrained cinematic contrast. "
        "No people, no human reflection, no readable text, no labels, no watermark, no multi-panel sheet, no UI, no film scratches, no modern items, "
        "no saturated red except the darkroom safelight. This is the PRESENT-TIME environment, not archival footage. ")
STYLE = ("STYLE LOCK (must match the already-built rooms of this house): walls warm cream painted plaster above a grey-green painted dado rail "
         "at 0.85 m, grey-green skirting and door/window trim; dark varnished oak floorboards; dark mahogany furniture with brass cup handles; "
         "faded Persian rugs; ALL WINDOWS ARE WHITE-PAINTED SIX-OVER-SIX SASH WINDOWS set deep in thick stone walls with a painted window board "
         "and damask curtains on a brass pole — NEVER leaded diamond-pane casements; interior doors are four-panel grey-green painted doors with "
         "brass knobs; plaster cornice at the ceiling. Every clock is stopped at seven o'clock (hour hand on seven, minute hand on twelve). ")
IRIS = ("Use case: in-game prop artwork, ONE child's drawing on a single sheet, straight-on flat scan, 4:3 landscape, the sheet fills the frame. "
        "Old yellowed paper with a torn edge, creases and a faint stain. Drawn by an 8-year-old girl who SEES the truth but cannot say it: "
        "abstract, unsettling, black graphite and ink scribbles only, fast repeated scratchy lines traced over several times, solid black "
        "scribbled masses where she pressed hard, distorted forms with teeth, spikes and radiating bristles. Her recurring symbol must appear once: "
        "a circle with a grid drawn inside and a dot in the middle (like a camera viewfinder and like a watching eye). No colour, no readable "
        "letters or words, no clean cartoon lines, no adult illustration skill, no horror gore. ")

P = {
  'T-034-门厅': [
    ('hall_hall_mid-v3', HEAD + STYLE +
     "Entrance hall of the manor, 5.4 m wide x 4.5 m deep, ceiling about 3.3 m, NO windows in this room. Camera stands near the back (north) "
     "door at eye height 1.6 m and looks south at the main front door: a heavy oak double door set in a Tudor four-centred pointed stone arch "
     "with iron studs, standing half open INWARD onto a wet rainy night (blue), gravel and lanterns beyond. Floor of honey limestone flags with a "
     "large worn Persian rug. Left wall (east): a four-panel door to the dining room in the middle; between it and the front door a narrow tall "
     "walnut-framed mirror that reflects ONLY the front door, a hat stand and the lamp. Right wall (west): a four-panel door to the drawing room "
     "in the middle; between it and the front door a tall grandfather clock stopped at seven. One brass hanging lantern, oak hall table with a "
     "silver card tray, umbrella stand. There is NO staircase in this room. Warm amber lamplight against cold blue night in the doorway."),
    ('hall_north-v3', HEAD + STYLE +
     "Same entrance hall (5.4 m x 4.5 m, no windows), reverse view: camera stands just inside the front door looking north. The back wall has a "
     "single four-panel door standing open in its middle; through it you see a 1.5 m wide cross corridor and, beyond it, the foot of the main "
     "oak staircase rising to the left. Side walls each have one four-panel door in the middle (left = drawing room, right = dining room). "
     "Grandfather clock (stopped at seven) on the left wall near camera, narrow walnut mirror on the right wall near camera, seen at a glancing "
     "angle with no reflection of anyone. Limestone flags, Persian rug, brass lantern. Readable depth: hall, doorway, corridor, stair."),
    ('hall_stair-v3', HEAD + STYLE +
     "Main staircase of the manor, in a stair hall NORTH of the entrance hall (not inside it). Dog-leg oak staircase: first flight of 10 steps "
     "rises away from camera on the LEFT side, a half landing 1.2 m deep against the back (north) wall, second flight of 10 steps returns "
     "above on the RIGHT side to the upper floor; each flight 1.2 m wide, turned oak balusters, square newel posts with ball finials, wine-red carpet "
     "runner with brass stair rods. The back wall is a blank panelled wall (it is a retaining wall against the higher garden, NO window). Lit by "
     "one brass lantern hanging in the stairwell and light spilling from the corridor. Camera at the foot of the stair, eye height 1.6 m, looking "
     "up the first flight toward the landing."),
    ('hall_landing_darkroom-v3', HEAD + STYLE +
     "Upper floor, night. Camera stands at the head of the main stair and looks EAST along the upper cross corridor (1.5 m wide, ceiling 2.9 m, "
     "oak boards with a long runner, closed four-panel doors along the right/south side). The corridor runs about 7 m and then widens to "
     "2.2 m at its far east end. There, on the LEFT (north) side, is the darkroom door: closed, ordinary four-panel door, and a thin line of "
     "DEEP RED safelight glows in the gap under it and along its edges — the only saturated colour in the image. Halfway along, an opening on the "
     "left leads to a short passage going north to the garden door. One dim wall sconce, the rest dark. Quiet, tense, no people."),
  ],
  'T-028-照片档案室': [
    ('archive_archive_mid-v3b', HEAD + STYLE +
     "Study and photographic archive on the upper floor, 5.4 m wide x 4.5 m deep, ceiling 2.9 m. Camera stands near the door in the middle of "
     "the north wall and looks SOUTH. The whole middle of the south wall is a projecting canted BAY WINDOW (oriel) 3.0 m wide and 1.1 m deep: "
     "stone mullions, white six-over-six sash lights, a cushioned window seat, looking out over the front lawn and the drive in grey autumn "
     "light. In front of the bay a large mahogany partner desk with an open negative album, a magnifying glass, a brass desk lamp and a folded "
     "newspaper cutting. East and west walls: floor-to-ceiling bookcases and glazed cabinets holding dated photograph albums and boxes of glass "
     "negatives, a library ladder. On the west wall, rows of framed group photographs hung in chronological order (small standing groups on a "
     "lawn, faces tiny and indistinct). Persian rug, oak boards."),
    ('archive_doorframe-v3', HEAD + STYLE +
     "Same study / photographic archive, reverse view: camera stands inside the bay window and looks NORTH at the four-panel door in the middle "
     "of the north wall. The painted door frame (left jamb) carries a column of children's height marks: short pencil and knife lines at "
     "different heights, each with a tiny illegible scratched initial; one mark is noticeably older and stops partway up. Either side of the door: "
     "a plan chest of shallow drawers for negatives and a tall glazed cabinet of albums; on the desk in the foreground, a photography manual "
     "with a dog-eared page, and a 1926 group photograph lying face down. Afternoon light from the bay behind camera, warm lamp on the desk."),
  ],
  'T-029-餐厅': [
    ('dining_dining_mid-v3', HEAD + STYLE +
     "Dining room on the ground floor, main part 6.3 m wide x 4.5 m deep, ceiling about 3.3 m. Camera stands at the north end (in the open "
     "opening to the snug) and looks SOUTH. South wall: THREE evenly spaced white six-over-six sash windows with damask curtains, rainy autumn "
     "garden outside. East wall (left of camera): a carved limestone fireplace near the windows, and nearer to camera a four-panel door to the "
     "kitchen passage. West wall (right): a four-panel door to the entrance hall. Long mahogany table for eight with candlesticks, a sideboard "
     "with silver, landscape paintings in gilt frames, a brass chandelier. Persian rug on oak boards."),
    ('dining_snug-v3', HEAD + STYLE +
     "Ground-floor dining snug that opens directly (no wall, no door) off the north side of the dining room. It is 3.8 m wide and 6 m deep and "
     "lies directly under an upstairs room; it has NO windows at all — its far north wall is a blank panelled retaining wall against the higher "
     "garden outside. Camera stands in the dining room at the opening and looks NORTH into the snug: a smaller round breakfast table with four "
     "chairs, a glazed china cabinet, a long-case barometer, panelled walls in grey-green below and cream above, two brass wall sconces and a "
     "low ceiling lamp, timber ceiling beams. Slightly enclosed and quiet; you feel there is a room just above."),
    ('dining_table_close-v3', HEAD + STYLE +
     "Close view of the dining table laid for dinner for the household, candles lit, rain on the window behind. At the end of the table one "
     "EXTRA place setting has been laid at an empty chair — complete with plate, cutlery, glass and napkin, exactly like the others — and "
     "nobody remarks on it. Calm, orderly, faintly wrong. No people."),
  ],
  'T-031-艾瑞斯的房间': [
    ('child_room_child_mid-v3', HEAD + STYLE +
     "Bedroom of an 8-year-old girl on the upper floor, 4.0 m wide x 4.2 m deep, ceiling 2.9 m. Walls: faded blue floral wallpaper above the "
     "grey-green dado. Camera stands near the door (south wall) and looks NORTH at the only window: one white six-over-six sash window in the "
     "middle of the north wall, looking out onto the back garden lawn and the green iron roof of the greenhouse in rain. Under the window a small "
     "low writing table with black pencils, a pen and ink, and a few sheets of yellowed paper. Small brass bed with a powder-blue blanket on the "
     "left, toy chest, rocking horse, wooden blocks, a cloth doll on a chair. On the left (west) wall a small cast-iron fireplace with a fireguard. "
     "Slightly too orderly and quiet, never horror. No child."),
    ('child_room_child_wall-v3', HEAD + STYLE +
     "Same girl's bedroom, reverse view: camera stands by the north window and looks SOUTH. The south wall has the four-panel door LEFT of "
     "centre; right of the door a large area of wallpaper where 6 to 8 children's drawings are pinned up with brass drawing pins: torn yellowed "
     "sheets covered in abstract black pencil-and-ink scribbles (spiky masses, a circle with a grid inside it), unreadable at this distance. "
     "Wardrobe, chest of drawers with a small wooden music box (lid closed, brass key), the bed foot in the foreground. Lamplight, grey evening."),
    ('iris_drawing_black_cloth-v3', IRIS +
     "Subject (abstract, never literal): the outside wall of a house drawn as a big rough rectangle of stone; low on the wall an EYE or a "
     "mouth-like opening (her grid-circle symbol) that has been stuffed and smothered by a heavy black scribbled mass, like cloth pressed over it."),
    ('iris_drawing_red_light_asleep-v3', IRIS +
     "Subject (abstract): a tall door drawn as a dark vertical shape; along the crack under the door a long closed EYE with spiky eyelashes, "
     "sleeping. Above it a small round lamp drawn as her grid-circle. Everything black graphite; the 'light' is just pressure and scratches."),
    ('iris_drawing_family_portrait-v3', IRIS +
     "Subject (abstract): a family portrait gone wrong — ONE long body with many arms holding hands, and on top of it the same face repeated "
     "six times, each face drawn as her grid-circle with a dot. Under the figures, where names would go, one long scribbled-out black bar."),
    ('iris_drawing_hat_man-v3', IRIS +
     "Subject (abstract): a standing figure with NO face — the head is an empty circle with a grid inside — wearing a clearly drawn tall hat; "
     "one hand drawn large, with a curved crescent-shaped scar mark on it. Around the figure, dense radiating scratches like light from a lamp."),
  ],
  'T-033-客厅·降灵会': [
    ('seance_seance_mid-v3', HEAD + STYLE +
     "Drawing room on the ground floor, 6.3 m wide x 4.5 m deep, ceiling about 3.3 m, everyday afternoon. Camera stands near the door in the "
     "east wall and looks WEST. South wall (left of camera): THREE white six-over-six sash windows with damask curtains open, grey autumn light. "
     "West wall (ahead): a chimney breast with a carved limestone fireplace on its left (south) part, and one white sash window on its right "
     "(north) part. North wall (right): a four-panel door to the corridor. Furniture: two sofas and armchairs around the fireplace, a writing "
     "bureau, a piano, potted palm, and a round mahogany table near the middle of the room with chairs around it. Persian rugs on oak boards."),
    ('seance_table_candle-v3', HEAD + STYLE +
     "Same drawing room prepared for a seance at night: all curtains drawn, the room dark except one cluster of candles in the middle of the "
     "round mahogany table. Five chairs around the table and one more chair set slightly apart, empty. On the table: a small handbell, a sheet "
     "of seance cards face down, a tumbler, gloves. The fireplace is out. Long candle shadows on the cream walls; calm, hushed, not theatrical."),
  ],
}

n = 0
for pack, items in P.items():
    d = os.path.join(ROOT, pack, 'prompts'); os.makedirs(d, exist_ok=True)
    for name, text in items:
        open(os.path.join(d, name + '.txt'), 'w', encoding='utf-8').write(text + '\n'); n += 1
print('written', n)
