# Folio implementation handover

Objective remains active: finish the personal, free Windows PDF editor/reader following `PERSONAL_PDF_APP_PLAN.md`. The user authorized autonomous implementation while away, free project-scoped tooling, tests and a local installer. Never buy, publish, upload personal documents or silently replace originals. This is implementation work, beyond the plan's original planning-only first brief.

## Current baseline

Tauri 2 desktop host, React/TypeScript interface, local PDF.js 6 viewer resources, PyMuPDF 1.28.2 canonical session engine packaged with PyInstaller. English Tesseract fast data is bundled for persistent offline OCR. All document mutations create validated immutable revisions with undo/redo. Normal PDF save copies exact working bytes. Secure redaction rewrites and sanitizes auxiliary content. Source documents remain intact.

`artifacts/releases/0.16.0` contains the latest fully verified installer and SHA256 receipt. Version 0.10.1 includes staged-value split/image/comparison handling and unusual field-name keys, on-page form controls, draft handling and shared logical values, precise crop/reset/selection and customizable numbers/watermarks, independent duplicate pages, a visual organizer and split outputs, independently validated static PDF/A-2b, offline certificate signing/inspection, ink/stamps, saved presets/batch jobs, signature rewrite checks, Office import, reader links/position/print preview and improved rotated editing; package and actual native WebView2 verification passed. Refer to the latest PROGRESS.md and receipts before choosing a build.

The optional free LibreOffice 26.8.1.1 runtime is extracted under `tools/LibreOffice/SourceDir/LibreOffice`. `scripts/setup_office.py` verifies and configures it in `%APPDATA%/personal.folio.pdf/settings.json`. It uses lessmsi extraction and does not register a Windows application. Keep the project folder available for that configured runtime. Office conversions use isolated profiles and preserve original input files. Linked external content and macros are rejected/disabled.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
npx.cmd playwright test
npm.cmd run package
node scripts/native_smoke.mjs
```

Playwright now starts both the loopback development bridge and Vite. The desktop release runs through stdio and does not expose that HTTP service. Native smoke starts an actual release WebView2 window with a process-local debugging flag, edits a synthetic PDF, verifies cancellation/reconnection, and checks print preview and Office conversion. It does not send anything to a printer.

Core checks include independent PDFium rendering/extraction, encrypted outputs, redaction removal, source hashes, OCR visible-pixel preservation, compression, image/annotation/form workflows, comparison reports and rotated/cropped coordinate placement. Office tests invoke the real free LibreOffice runtime, then verify PDFs independently. Fixtures are synthetic.

## Continue

The 0.15.0 release passed 162 Python tests, 21 browser workflows plus an affected OCR screenshot rerun, packaged-worker checks, standard/draft native checks, synthetic native camera capture, styled editing and mixed-page OCR with independent saved pixel/text checks. Photo scanning adds automatic boundary proposals, manual draggable/keyboard/coordinate corners, perspective crop, enhancement/rotation, page order and PDF review/save. Full photo UI is verified in browser mode; actual native worker commands create/reopen corrected multi-page PDFs. Native OS photo picker remains a manual gate. An attempted native picker test shim stalled and is explicitly excluded from acceptance. Do not stop the user-installed Folio process to test another build.

Next: broaden photo lighting/clutter and corner interaction fixtures, camera capture/physical scanner integration, mixed-page OCR and original roadmap work (fonts/text reflow/extended scripts, form detection/multi-select/choice compatibility, structural Markdown/HTML, visible certificate appearances, compare alignment, qpdf and optional free local models). Use FEATURES.md to preserve the full scope.

Never describe unsupported conversion/layout cases as Acrobat parity. OCR spelling, complex layouts, original-font reuse and semantic comparison need separate evidence. Printing, scanner hardware, native dialogs/installer UI and unusual real PDFs require explicit manual acceptance when the user returns. Maintain PROGRESS.md, FEATURES.md and setup instructions as implementation progresses. Do not mark the full goal complete just because a build passes.

Current continuation: direct text tools use paragraph clicks and click-to-add, with source font reuse where available, measured wrapping/collision checks, a borderless page editor and in-memory drafts applied by save/export preparation. Do not restore rectangle drawing or a sidebar text-entry box for these tools. Mixed-style font/color/relative-size retention is verified after Apply; richer live preview, missing-glyph fallback, opacity/anchors, shaping/reflow/scan reconstruction still need work. Windows package virtualization required exact private-session asset grants; keep the original-file asset denial gate. Native tests have isolated profiles/dynamic ports and own-tree cleanup. Camera starts only through Start camera; keep synthetic-only hardware tests and the real-camera manual gate. Untracked non-source user inputs are preserved outside commits and test evidence.

0.14 continuation: worker/styled_text.py maps unchanged/new characters to source style runs and measures styled wrapping before mutation. Original paragraph style mode is automatic; explicit replacement fonts stay uniform. Keep the plain typing preview limitation visible until rich editing is implemented. Run node scripts/native_camera_smoke.mjs and node scripts/native_styled_text_smoke.mjs after the standard native smoke; the camera fixture comes from create_fixtures.py. Milestone preservation verifies the extra native receipts against the final binaries. Full goal remains active.

0.15 continuation: worker/ocr.py masks existing word rectangles on a recognition-only raster, suppresses overlaps, and imports only invisible text. This preserves source pixels and existing digital words. Mode/resolution settings are available in Convert and batch recipes; OCR reports processed/skipped/added counts. Do not equate hidden OCR editing with changing visible scan words. Run native_mixed_ocr_smoke.mjs after the other native scripts, and keep all receipt hashes current. Next independent work remains rich live text editing/shaping/fallback, more OCR languages/deskew/scan reconstruction, forms/conversion/compare/archival/scanner/local-model tasks. Full scope is unchanged and goal remains active.

## Current 0.16 candidate

Source is at 0.16.0 with bundled English/Malay/Simplified Chinese models and combinations, Convert/batch language selectors, checked model provenance and multilingual test fixtures. Latest verified installer remains 0.15.0. Finish full Python/browser gates, packaging, native_multilingual_ocr_smoke.mjs plus all existing native checks, screenshot review, clean source checkpoint and save_milestone.py. Do not count a model test or frontend build as installer acceptance. Models must pass prepare_assets.py checksum checks and licenses/models.json collection. Preserve the untracked user photo untouched.

## Latest verified checkpoint: 0.16.0

Use artifacts/releases/0.16.0/Folio_0.16.0_x64-setup.exe (114,610,996 bytes; SHA256 be23918060a16f84667c30b1d9dbd2c5fcf448c61d3dad8d513c98b4b99be64e). All 175 Python tests, 23 final browser workflows, packaged worker, frontend/Rust/NSIS and six native receipts passed. Browser/native multilingual screenshots reviewed. English/Malay/Simplified Chinese and combinations are bundled locally; saved batch language and independent output pixels/text/source preservation passed. Model provenance is in worker/ocr-models.json and packaged notices. The current candidate described above is now verified; full original goal remains active.

Continue with OCR deskew/preparation and visible scan reconstruction, rich live text formatting/shaping/fallback and remaining FEATURES.md scope. Keep direct on-page click/edit and click/add, preserve originals, use synthetic fixtures and isolated native profiles, and never stop user-installed Folio. Real printer/scanner/camera, native dialogs/installer UI, high-DPI and unusual personal PDFs remain manual gates. The untracked user root photo is untouched and excluded from tests/commits.
