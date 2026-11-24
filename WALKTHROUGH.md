# Atrium walkthrough

Double-click `Start Atrium Tour.cmd` to start at the main entrance on Windows. Alternatively, run `npm run dev` in this folder and open the local address printed by Vite. Choose **Walk inside**, or add `?tour=1` to the address.

- **Desktop:** WASD moves, dragging looks around, and the left/right arrows turn. Escape returns to the cutaway.
- **Fullscreen:** Choose **Fullscreen** in the top toolbar. Choose **Exit fullscreen** to return to the window while staying in the tour. If the embedded viewer does not support fullscreen, open the local tour address in your browser.
- **Display quality:** Walking, orbiting and fullscreen use the display's native pixel density up to the GPU's buffer limits. Movement reuses the last floor reflection instead of reducing the resolution of the scene. The glossy reflection refreshes when you stop.
- **Touch:** Hold a directional button and drag elsewhere on the scene to look.
- **Elevator:** Approach the bronze doors in the front-right corner. Press **E** or choose **Use elevator**, then choose a destination. The tour resumes on that landing. The floor selector also allows direct visits.
- **Locker gallery:** On the third floor, choose **Locker gallery** (under **Views** on smaller screens), or add `?visit=lockers` to the tour address. Walk through the gallery entrance, face a locker, and press **E** or tap the action button to open or close it. The editable building and gallery render are in `models/Atrium/Gallery/`.
- **Bedrooms:** On the third floor, explore either wing through its open room doors, or use **Visit a bedroom…** to go straight inside a numbered room. `Start Bedroom Tour.cmd` opens room G06 on Windows.
- **Furnished source:** `models/Atrium/Furnished/Atrium_Residences.blend` supplies the bedroom interiors; its bedroom ceilings have their own toggleable collection. Run `furnish_suites.py` in Blender after generating the Atrium source files.
- **Current viewer:** `models/Atrium/Architectural/Atrium_Architectural.blend` contains the fitted workstations, text-only reception counter, tailored seating, ceiling fixtures and polished porcelain. The entrance and workstation renders are saved alongside it. Walking mode adds view-dependent floor reflections and adjusts resolution to the device's frame time.
- **Studio source:** `models/Atrium/Studio/Atrium_Studio.blend` contains the detailed plants and toys used in the architectural edition.
- **Blender:** `models/Atrium/Atrium_Finished.blend` contains the assembled building, procedural finishes, and three cameras in the **Walkthrough | eye-level cameras** collection.

## Updating the furnished models

Run Blender in background mode with `--python finish_atrium.py` to regenerate the finished Blender file, adjusted café GLB, and entrance render. Then run `node build-walkmaps.mjs` to bake pedestrian obstacles and check that the floor routes are connected. Run `npm run build` to package the viewer.

For the current architectural exports, generate the furnished edition first, run `make-console-art.ps1`, then run Blender with `--python studio_details.py` and `--python architectural_finish.py` in that order. Finally run `node build-walkmaps.mjs` and `npm run build`. The optional `stats` query parameter exposes the last frame's draw calls, triangles, camera position and pixel ratio in `window.atriumStats`.
