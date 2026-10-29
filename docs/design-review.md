# Interface redesign

The user asked to remove the generic AI-generated appearance. The previous page treated a data utility like a marketing landing page. The redesign puts the two working tools first.

## Research

- [SCALR: 20 Signs a Website Was Made by AI](https://scalr.sg/blog/20-signs-a-website-was-made-by-ai/) identifies recurring combinations such as ornamental serif emphasis, grain, headline badges, decorative icons, and repeated three-part layouts. These overlap with the previous interface's decorative typography, globe, numbered captions, and explanatory footer.
- [Nielsen Norman Group: Aesthetic and Minimalist Design](https://www.nngroup.com/articles/aesthetic-minimalist-design/) recommends prioritizing information that helps people complete the task and removing visual noise.
- [NN/g's evaluation of AI design tools](https://www.nngroup.com/articles/ai-design-tools-not-ready/) describes generic layouts that persist even when the product context changes. The relevant correction here is a layout built around generating, inspecting, and exporting data.

## Decisions

- Contacts and Text are separate views with persistent state and working hash links.
- Parameters appear above their result. The main action names the result it generates.
- Titles and descriptions state the tool's purpose directly. Marketing sections and slogans are removed.
- No grain overlay, globe illustration, decorative avatar blocks, numbered section captions, or entrance effects.
- A restrained neutral surface, one action color, readable labels, and consistent spacing support the controls and data.
- Typography follows an application hierarchy: 28px page heading, 14–15px content, 12–13px secondary labels. Monospace is reserved for exact seeds and coordinates.
- Contact rows remain a table on desktop and an expandable list on narrow screens. Physical attributes and coordinates remain available.
- Text is presented in a plain selectable output field. Copying and sample navigation remain adjacent to the output.

The API contracts and SQL generation algorithms are unchanged by this redesign.

## Verification

- All 12 frontend state, CSV, request, and response tests passed.
- TypeScript checking and the Docker production build passed; the web container was updated in place.
- The `#text-generator` deep link opens the Text view and marks the correct navigation link as current.
- Contact batch navigation and exact previous-batch replay passed in the live browser.
- The exported CSV was independently compared with SQL-backed API data: all 10 fields of all 10 records matched.
- Switching between Contacts and Text preserves the generated text.
- Both views were inspected at 1280 × 900 and 390 × 844. Mobile document width stayed within the viewport; contact details remain accessible in expanded rows.
- Browser error logs were empty. Screenshots are saved as `.runtime/redesign-{contacts,text}-{desktop,mobile}.png`.

## Python interface migration

The primary interface now uses FastAPI and Jinja2 at the same port 3000. Its CSS was copied from the approved compact design into `backend/app/static/app.css`; contact and text markup retain the same classes, spacing, typography, controls and responsive layouts. A third navigation item opens the real saved SQL benchmark. HTML forms and pagination links work through Python; the browser script only handles details, draft-setting hints, seed selection and copying.

The superseded frontend source, dependencies, build artifacts and Dockerfile were removed on 2026-10-30. The interface is maintained in `backend/app/templates/` and `backend/app/static/`. New screenshots are `.runtime/python-{contacts,text}-{desktop,mobile}.png`.
