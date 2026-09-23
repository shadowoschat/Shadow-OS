# TODO - SHADOWAI SketchAnimator Upgrade

- [x] Replace contour-based sketch generation with edge+gradient intensity stroke generation.

- [ ] Implement 5-stage multi-layer shading (outline → light → medium → dark → cross-hatching).
- [ ] Add stroke-based smooth point-by-point animation (no contour jumping).
- [ ] Replace red dot cursor with `Frontend/static/pencil_cursor.jpg` cursor PNG-style overlay (rotate along stroke + shadow).
- [ ] Ensure blank white paper start; preserve realistic pencil look using grayscale intensity + texture overlays.
- [ ] Optimize for PyQt5: precompute stroke list once; incremental draw; avoid UI freezing.
- [ ] Update `Backend/SketchAnimator.py` with clear comments.
- [ ] Run quick local test: execute `python Backend/SketchAnimator.py`.

