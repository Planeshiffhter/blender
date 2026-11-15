# Maya face v2 — original character facial-animation prototype

This folder adds cartoon facial performance to the **existing, original Maya mesh** in A Second Taj. It does not replace the character, change the source 20-second movie, or modify `main`. Work stays on draft PR #1 for review.

## Deliverables

- [Maya_Cartoon_Face_Test.blend](Maya_Cartoon_Face_Test.blend) — editable Blender 4.3.2 scene, 84 frames at 24 fps; includes animated facial shape keys, head acting, a closeup portrait camera, and revised lighting
- [Maya_expression_contact.jpg](previews/Maya_expression_contact.jpg) — six new Blender renders: neutral, smile, surprised, curious, blink, talking
- [Maya_Face_Demo_3_5s.mp4](final/Maya_Face_Demo_3_5s.mp4) — 3.5-second face-performance sample of Maya's “Yes! It looks like a palace in the sky” line using improved Kokoro voice `af_bella`
- [face_rig_report.json](face_rig_report.json) — vertex counts for all new facial shape keys
- [build_maya_face_demo.py](build_maya_face_demo.py) and [render_face_demo.py](render_face_demo.py) — reproducible source scripts

## New controls on existing character

**Maya • character** gets six shape keys: `BlinkLeft`, `BlinkRight`, `BrowLiftLeft`, `BrowLiftRight`, `EyesWide`, `CheekSmile`.

**Maya • mouth** retains the original `Rest` and `Speech` and adds four more: `VisemeWide_E`, `VisemeRound_O`, `SmileCorners`, `VisemeClosed_MBP`.

The sample animates expressions and head motion together. The eye and face shape keys modify *existing mesh vertices*, not a painted picture or a replacement character. The skin texture is preserved, with gentler shading and portrait depth of field.

## Rebuild from the original .blend

Run from `CartoonStudio/episodes/a_second_taj`:

```bash
blender --background A_Second_Taj.blend --python extension_review/face_v2/build_maya_face_demo.py

blender --background extension_review/face_v2/Maya_Cartoon_Face_Test.blend \
  --python extension_review/face_v2/render_face_demo.py -- \
  --mode portraits --output /tmp/maya-portrait-frames
```

GitHub Actions workflow [maya-face-v2-demo.yml](../../../../../.github/workflows/maya-face-v2-demo.yml) also renders six portraits and 42 animation-on-twos frames, then creates the MP4 and verifies duration, resolution and frames. It **does not merge to main**. The workflow checks decoded image pixel hashes to prevent six identical pose previews from passing as six expressions.

## Validation performed

- 10 new actual mesh shape keys created and verified to affect original mesh vertices
- Six distinct face-expression images rendered and visually inspected
- 3.5-second MP4 confirmed at 960×540, 24 fps, 84 frames with AAC audio
- Kokoro audio compared against the MP4: waveform correlation **0.99972**, measured time shift **0 milliseconds** for Maya's spoken line
- Original 20-second film and Part 2 video on `main` unchanged

## Remaining quality limits

This is an initial rigging improvement, not a full studio-grade facial remodel. The original eyes/brows are combined in one textured mesh, so eyelid deformation is a geometric approximation rather than fully modeled anatomically separate eyelids; mouth visemes are approximate, not phoneme-level performance capture. Hair, shaders and acting may still need detailed artistic cleanup.

**Next development gate:** review Maya's facial expression sheet and speaking sample. Once approved, develop separate custom controls for Tara and integrate the approved faces into the standalone 20-second Part 2 animation. Do not rerender the entire story or publish on `main` before a visual review.
