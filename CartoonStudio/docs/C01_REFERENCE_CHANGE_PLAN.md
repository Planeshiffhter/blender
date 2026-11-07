# Character 01 reference and adaptation plan

Status: **design and adaptation plan; Character 01 is not approved or certified as professional quality.**

This document separates the uploaded design references, the inspected fallback asset,
and the preferred Rain asset, which has not yet been obtained or viewed.
Earlier procedural experiments are archived under `prototypes/C01_procedural/`.
They are not the approved character. The canonical
`assets/characters/C01/C01_MASTER.blend` is not present; its path below describes
the intended future deliverable after a suitable base has been obtained and adapted.

## Evidence and limits

- The supplied `reference/C01_CLEAN_MODELING_SHEET.png` and
  `reference/05_FACE_CLOSEUP.png` show the requested visual direction. The other
  cropped views establish front, side, back, and three-quarter design guidance.
  These are 2D references, not proof of a mesh, rig, or rendered result.
- The inspected fallback is
  `/workspace/library-files/Game-Human-Rig/Game_Human_Rig.blend` from
  [ostef/Game-Human-Rig](https://github.com/ostef/Game-Human-Rig).
  Its [published showcase](https://raw.githubusercontent.com/ostef/Game-Human-Rig/main/showcase.png)
  depicts bald, unclothed human prototyping meshes with body control rigs.
  Local Blender inspection found `Female_Prototype` with 11,664 vertices,
  10,764 polygons, an Armature modifier, and no facial shape keys. The asset has
  generic materials and no packed character texture images. The repository's
  README explicitly describes the meshes as prototyping assets.
- **Rain has not been viewed.** The required download destination is blocked by
  the current network policy. Its actual appearance, topology, facial controls,
  dependencies, and Blender compatibility have not been verified. Statements
  below describe what to inspect and change after access is available; they do
  not describe Rain's present design.

The fallback can support investigation of body deformation and locomotion. Those
capabilities do not establish suitability as a finished shopping-cartoon character.
No source is accepted as production ready solely because it contains a rig.

## Target and observed differences

The target is an original adult female character, approximately 20–30 in design,
with stylized proportions of about 6–7 heads in total height. Preserve adult hand,
limb, and torso proportions while using the expressive head treatment in the
uploaded references.

| Area | C01 target | Observed fallback gap |
| --- | --- | --- |
| Face and silhouette | Soft cheeks, short rounded chin, warm approachable expression, stylized adult proportions | Neutral realistic head with narrower eyes and a different jaw/cheek treatment; requires sculptural adaptation |
| Eyes and expression | Large brown eyes, shaped upper/lower lids, brows, controlled eye movement, blink, speech, smile, surprise, sadness, anger | No facial shape keys found; a suitable expressive face rig has not been demonstrated |
| Hair | Shoulder-length chestnut waves, side part, continuous grouped hair silhouette, restrained directional highlights | Bald prototype; requires a complete hairstyle |
| Top | Fitted light-blue short-sleeve crewneck T-shirt with finished collar and sleeve/hem details | Unclothed body; requires fitted garment geometry and deformation tests |
| Jeans | Indigo straight jeans with waistband, pockets, seams, subtle denim weave | No finished jeans or garment materials |
| Footwear | White low-top sneakers, readable sole, toe shape, and lacing | No finished footwear |
| Surface treatment | Warm skin with subtle subsurface scattering, soft cheek color, linen-like fabric roughness on the tee, restrained denim weave, coherent hair/eye materials | Generic prototype materials without the required finished surface design |
| Presentation | Soft studio key, fill, and rim lights on a neutral ground; consistent exposure and color management | Published viewport showcase demonstrates the prototype and rig, not a polished C01 studio render |

Changing colors and lighting will not close the facial, hair, clothing, or facial-rig
gaps. Their geometry and deformation behavior must be addressed explicitly.

## Adapt the preferred asset after Rain becomes accessible

1. **Preserve and inspect the source.** Keep the original download unchanged,
   record its source URL, version, checksum, and license, and retain attribution
   and dependency documentation. Open with automatic script execution disabled
   for the initial audit. Check Blender-version requirements, missing libraries
   and images, geometry, UVs, materials, armatures, constraints, drivers, shape
   keys, and included actions. Record what is actually present before selecting
   an adaptation strategy.
2. **Create a separate working copy.** Make a C01 adaptation file while preserving
   the source asset and its existing rigs. Use the current checkout; do not create
   an extra branch or PR for this work. Keep temporary experiments separate from
   the reusable master. Do not overwrite an existing approved character.
3. **Establish proportions and face design.** Compare neutral front, side, back,
   and three-quarter views against the supplied references. Sculpt cheeks, chin,
   brow area, nose, and eye proportions toward the C01 target. Preserve vertex
   count/order where shape keys or rig dependencies require it. If retopology is
   necessary, treat it as a deliberate rig-transfer task and revalidate the full
   facial setup; do not assume existing drivers or weights survive.
4. **Develop hair and wardrobe.** Build the side-parted shoulder-length waves with
   connected visual masses and finer directional detailing. Fit the light-blue
   tee, indigo straight jeans, and white sneakers to the adapted body. Check
   layers, thickness, seam details, hair/shoulder contact, and garment clearance.
   Transfer or refine weights and add corrective deformation where needed.
5. **Preserve and verify animation controls.** Check head, neck, spine, limb, hand,
   and finger controls, including walking, sitting, pointing, and waving. Verify
   eye aim, upper/lower eyelids, blink, mouth/viseme controls, and the requested
   emotional expressions. Review driver targets, constraint spaces, bone names,
   weights, and joint behavior after every structural edit. Existing controls
   are reusable only after their resulting mesh deformation has been observed.
6. **Refine materials and lighting.** Use subtle skin subsurface scattering and
   cheek variation; brown irises with readable pupils and corneal highlights;
   soft fabric roughness on the tee; fine denim weave; and restrained hair
   highlights. Set a large soft key, a weaker fill, and a rim light. Avoid lighting
   that hides topology problems or washes out the clothing and facial forms.

## Validation and approval gate

- Save the complete editable master at
  `assets/characters/C01/C01_MASTER.blend`, including the character, rig, facial
  controls, materials, hair, and reusable actions. Pack external dependencies or
  use tested relative paths. Reopen the saved file in a fresh Blender process.
- CPU-render genuine front, side, back, and three-quarter views, plus close facial
  expression images. Inspect silhouette, eye/lid contact, hair continuity, clothing
  intersections, hands, and bent joints. Use reduced-resolution previews first;
  retain enough resolution to judge the facial and material work.
- Verify reusable `IDLE`, `WALK`, `WAVE`, `POINT`, `TALK`, `SURPRISED`, and `BLINK`
  Actions. Confirm nonzero mesh deformation through the relevant frame ranges;
  action names or keyframe counts alone are insufficient evidence.
- Render a true full 360-degree turntable and at least five seconds of actual
  walking, blinking, smiling, speech-related mouth movement, and a hand gesture.
  Inspect the frames and verify the encoded MP4 files with FFprobe. A camera move
  around static reference images does not validate the character.
- Build a separate episode test that links the master and uses Library Overrides
  where needed. Animate that instance independently, reopen the episode, and
  verify the library link, controls, deformation, and dependency paths. Confirm
  the source master remains unchanged.
- Present the rendered views, expression images, videos, validation results, and
  remaining artistic/technical gaps for user approval. **Do not begin Characters
  02–04 before Character 01 is approved.** A useful prototype or a successful
  render is not, by itself, successful completion of the professional-quality
  requirement.

No paid GPU resources are authorized by this plan. Continue CPU work where useful;
if rendering becomes a concrete resource blocker, report the measured limitation
and request authorization before connecting or provisioning AWS resources.
