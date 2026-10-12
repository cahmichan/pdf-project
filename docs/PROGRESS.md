# Folio progress

Active goal: implement PERSONAL_PDF_APP_PLAN.md using free local components. The user's goal authorizes implementation beyond the plan's original Phase 0-only brief.

## 11 October 2026 - Foundation in progress

- Workspace initially contained only the plan. No existing app to preserve.
- Confirmed Windows 11 x64, approximately 15.4 GB RAM, Node 24, Rust/Cargo, and bundled Python 3.12.
- Created desktop/front-end configuration and a supervised local stdio worker boundary.
- Preparing project-local Python dependencies and the canonical document/session engine.

## Verification

- 20 Python document tests passed after correcting text-fit placement and image DPI expectations.
- Independent PDFium checks cover rendering, form appearances, encrypted open, and redaction text removal on synthetic fixtures.
- 2 browser end-to-end tests passed in headless Edge: open/render/search, add text, undo/redo, safe export, form update, bookmark navigation.
- Home and reader screenshots were visually inspected; layout and PDF rendering are readable without clipping at 1440x1000.
- Frontend production build and Rust cargo check passed.
- Upgraded PDF.js to the current patched version after npm audit identified an advisory. Current npm audit: zero reported vulnerabilities.
- Python worker packaged successfully. Windows release and NSIS installer 0.1.0 built successfully. A preserved copy and SHA256 receipt are in artifacts/releases/0.1.0.
- These are browser/engine/build results; native dialogs, printing, scanner, and installed-app acceptance are not yet established.

## Next

Finish the installer and packaged-worker verification, then continue pending features in FEATURES.md. Goal remains active; no full-scope completion claim.

## Native milestone and next feature set

- Packaged-worker smoke passed with developer Python absent from PATH: open, add text, PDF save/reopen and DOCX export.
- Actual release WebView2 smoke passed: opening via command-line path, local PDF rendering, thumbnails, packaged worker edit, no captured page errors. Reader screenshot visually inspected. Receipts and screenshots: artifacts/native-smoke and artifacts/packaged-smoke.
- Implemented English offline OCR using bundled Tesseract fast data and PyMuPDF's linked OCR engine. Tests cover normal/rotated scans, independent PDFium search, exact before/after rendered pixels, and skipping digital text pages. The original page image/vector content stays intact; only invisible recognized text is added.
- Implemented JPG page export, embedded image extraction, replace/remove embedded image, quad-based text markup, underline/strikeout, annotation comment edit/delete, checkbox/dropdown/list field creation and field-value controls.
- Added screen/print lossy image compression presets. Tested substantial size reduction on a synthetic image PDF with searchable digital text retained. No universal size or quality guarantee.
- Added positional PDF text/render comparison and self-contained HTML report. Tests distinguish identical PDFs, changed text and extra pages.
- Added worker cancellation and a five-minute inactivity timeout in the native host; actual native cancellation/reconnection passed on a 40-page synthetic scan. The canceled operation retained the original revision.
- 20 core engine tests and all 3 browser UI tests pass. Version 0.2.0 installer and packaged offline OCR passed; native WebView2 rendering/edit/cancellation passed. Hash receipt: artifacts/releases/0.2.0/receipt.json.
- The 0.1.0 installer predates these new features. Do not infer their packaged acceptance from the earlier release receipt.

Next: finish updated UI/native/installer verification; continue free Office import, print/link handling, batch recipes, signature/archival evaluation and remaining feature tracker items. Scanner checks require available hardware. Full goal remains active.

- Free LibreOffice 26.8.1.1 runtime prepared by verified MSI download plus lessmsi file extraction. Office import source adapter/UI added after the 0.2.0 release; actual DOCX/XLSX/PPTX conversion verification is running. Runtime receipt: artifacts/office/runtime.json. Setup: docs/SETUP.md.

## 0.3.0 candidate verification

- Free Office import passed real LibreOffice conversions for DOCX, XLSX and PPTX; independent PDFium opened/rendered the PDFs and extracted expected text. Office sources retained exact hashes.
- Added safe HTTP/HTTPS/mailto reader links, internal page links, remembered position/zoom, selected-page print preparation and preview. Up to 100 pages per print job, raster output at up to 150 DPI. Actual native printing remains a manual gate.
- Rotated/cropped rectangle placement passes at 90/180/270 degrees. Redaction and added text pass independent extraction checks at 90/270 degrees. Visual selections are mapped through page derotation; crop and rotation properties stay intact. A rotation-normalization approach was rejected after it changed cropped dimensions.
- Current core document suite: 26 passing tests. Office/import suite: 4 passing tests (last full run preceded the final rotated-page additions).
- All 4 browser UI tests pass, including page links, restored reading position and selected-page print preview. Screenshot visually inspected.
- Fixed development watch exclusions: generated sessions, licenses, native artifacts and the large optional runtime no longer trigger excess Vite scanning/reloads. Latest full browser run: 15.8 seconds.
- Version 0.3.0 packaging is running. The 0.2.0 installer remains the latest fully verified native milestone until the new native receipt passes.

## 0.3.0 verified native milestone

- Package script completed end to end: 30 tests passed, bundled-worker English OCR and configured free Office import passed with developer Python absent from PATH, frontend/Rust release and NSIS installer built, installer copied and SHA256 recorded.
- Installer: artifacts/releases/0.3.0/Folio_0.3.0_x64-setup.exe (49,628,195 bytes). SHA256: f05afb6fa8a407529370ff412001ce2c9ac6463d3e922eb9d639d51564c973c0.
- Actual native WebView2 smoke passed: local PDF render, editing, internal page link, selected-page print preview asset loading, OCR cancellation/reconnection, and configured LibreOffice import. No captured page errors. Native print preview screenshot visually inspected.
- 500-page synthetic digital PDF benchmark: engine open 0.068s; first thumbnail 0.017s; full search 0.529s. This excludes native cold startup and peak memory; it is not a broad performance guarantee. Receipt: artifacts/benchmark/receipt.json.
- Native dialogs, actual printing, scanner, installer UI and unusual real PDFs remain manual checks. No physical print/scan job was submitted.
- A separate shaping experiment rendered Chinese and Arabic with the free engine. Chinese extraction was correct; Arabic extraction included incorrect mapped/presentation characters. Extended-script editing is still unsupported until search/copy quality passes. Do not turn visual rendering alone into acceptance.

Next independent implementation: saved workflows and batch jobs, then remaining annotation/form/conversion/signature/archival tools. Goal stays active.

## 0.4.0 workflow candidate

- Added preset creation/deletion, built-in searchable-scan/numbered-handout/smaller-PDF presets, sequential multi-file processing, unique output names, per-file failure continuation, durable batch receipts and interrupted-job history.
- Presets support rotation, crop, numbering, watermark, OCR, metadata and form flattening plus supported export formats. Passwords/file-execution arguments cannot be persisted as preset settings.
- Batch operations skip signature-field PDFs that would be edited/rewritten. Individual rewritten PDF exports now require explicit signature-change confirmation; exact-byte plain PDF copies preserve signatures.
- Fixed rotated-page numbers/watermarks. Tests cover footer placement at 90/180/270 degrees.
- Current core/workflow suite: 32 passing tests; full suite includes 4 real Office tests. All 5 browser UI tests passed before the final singular-label correction; batch screenshot visually inspected.
- Version 0.4.0 packaging and native batch verification are next. Latest fully verified installer remains 0.3.0, source checkpoint e8ceef6c14838a45b136aaad205e2500d5aef082. Its evidence is preserved under artifacts/releases/0.3.0/verification.

## 0.4.0 verified native milestone

- Full package gate passed: 36 Python tests, frozen-worker OCR/Office/batch smoke, frontend/Rust release and NSIS installer. All 5 browser UI tests passed (18.46s, no failures or skips).
- Actual native WebView2 smoke passed render/edit/internal link/print preview/cancellation/reconnection/Office import and batch processing, with no captured page errors.
- Installer: artifacts/releases/0.4.0/Folio_0.4.0_x64-setup.exe (49,635,918 bytes). SHA256: 9e0dde815ab08c424afdee8a9a86c4b9d3b3425acb9944bac6db612f86defea6.
- Installer UI, physical printing/scanning and unusual real documents remain manual gates.

Next: ink/stamp annotation tools and remaining feature tracker items. Full goal remains active.

## 0.5.0 annotation candidate

- Added multi-stroke freehand ink preview, width/color controls, discard-last/clear controls and standard approved/draft/confidential/final/not-approved PDF stamps. Annotations remain removable/comment-editable after save/reopen.
- Cropped/rotated ink/stamp tests passed at 0/90/180/270 degrees with independent PDFium rendering, exact vertex coordinate checks and source hash preservation. Invalid/non-finite points fail without a revision change.
- Fixed page selection support for underline and strikeout. Frontend production build passed; ink/stamp browser create/save/reopen/delete passed. Full packaging/native gates are next.

## 0.5.0 verified milestone

- All 41 Python tests and 6 UI tests passed. Frozen-worker OCR/Office/batch passed. Frontend/Rust release and NSIS bundling passed after closing a prematurely launched smoke app that locked the executable.
- Final bundled native smoke passed editing, ink/stamp annotations, links, print preview, cancellation/reconnection, Office and batch, with no captured page errors. The harness now waits for the ink revision before placing a stamp.
- Installer: artifacts/releases/0.5.0/Folio_0.5.0_x64-setup.exe (49,634,392 bytes). SHA256: 16948f5bf0e10ddf14d94ade95587e70826566ecff310530a20ae71612989940.
- Ink and final annotation UI screenshots visually inspected. Physical print/scanner and installed UI gates remain pending.

Next: free offline certificate signing/verification using pyHanko. The 0.5.0 worker does not include that new dependency or feature. Goal remains active.

## Certificate signing candidate

- Added pyHanko 0.37.0 (MIT) and free cryptographic dependencies; exact requirements refreshed. Signing creates an incrementally appended separate PDF and verifies its integrity before publishing it. It never goes through the ordinary rewrite commit.
- Added PKCS#12 identity selection, encrypted RSA-3072 personal identity creation, public certificate export, and explicit-trust offline inspection. Passwords are not recorded in sessions, receipts or localStorage and are cleared after operations. No Windows trust-store changes or network requests are used.
- Synthetic tests passed byte-prefix preservation, PDFium render/extraction, two consecutive signatures, tamper detection, exact-byte save, edit guard, explicit trust, wrong passwords and identity-overwrite refusal. External sockets are blocked in the test (local asyncio socket pairs allowed).
- Browser create/sign/export-certificate/reopen/inspect flow passed. Revocation assurance, trusted timestamps, visible certificate appearances and broader third-party signatures remain unsupported/pending. Full package/native checks are next.

## 0.6.0 verified milestone

- All 43 Python tests and 7 UI tests passed. Frozen worker passed offline signing with developer Python absent from PATH; current dependency notices cover 124 installed packages. Frontend/Rust/NSIS packaging passed.
- Actual bundled desktop smoke passed render/edit/ink/stamps/link/preview/cancel/reconnect/Office/batch and offline certificate signing/inspection, with no captured page errors. Signature UI screenshot visually inspected.
- Installer: artifacts/releases/0.6.0/Folio_0.6.0_x64-setup.exe (57,307,532 bytes). SHA256: 677a239a338cf39d50282c50a63ce4fb119bf014db48a705fb16848639fad3d6.
- Certificates in automated evidence are explicitly synthetic. Revocation/trusted timestamp guarantees, broader real-world signatures and visible certificate appearances remain pending. No actual private identity was inspected or generated for the user.

Next: archival conversion plus independent conformance validation with free local tools. Official Ghostscript 10.08.0, 7-Zip 26.04 MSI and Temurin 21.0.12.1 JRE downloads have pinned SHA256 verification; not yet extracted/configured. Full goal stays active.

## 0.7.0 archival candidate

- Prepared project-local Ghostscript 10.08.0, 7-Zip 26.04, Temurin 21.0.12.1 JRE and veraPDF 1.30.3. Official binary hashes are pinned; veraPDF ZIP is pinned and its detached GPG signature verified against documented publisher fingerprint 13DD102B4DD69354D12DE5A83184863278B17FE7. No Windows app registration or system PATH changes. Setup merges optional runtime paths into Folio's settings. Receipt: artifacts/archival/runtime.json.
- Added static PDF/A-2b export gated by independent veraPDF rules, current-PDF conformance inspection and session-scoped XML report export. Forms/annotations are baked; links/attachments/JavaScript removed. Source and working revision remain intact.
- Five archival tests pass: real conformance on cropped/rotated forms with transparent graphics, independent PDFium text/render dimensions, ordinary-PDF rejection, forged-report-path rejection and failed-validation rollback preserving an existing output.
- Browser export/inspect/reopen/report save passes, and conformance dialog screenshot visually inspected. Corrected test waiting to use the report output path rather than the prior PDF's Saved status.
- Full package and native configured-runtime verification are next. Latest verified milestone remains 0.6.0.

## 0.7.0 verified milestone

- All 48 Python tests and 8 UI tests passed. Frozen-worker archival conversion and independent validator passed with developer Python absent from PATH. Frontend/Rust/NSIS packaging passed.
- Actual bundled desktop smoke passed all prior operations plus configured Ghostscript/veraPDF PDF/A-2b export, with no captured page errors.
- Installer: artifacts/releases/0.7.0/Folio_0.7.0_x64-setup.exe (57,317,853 bytes). SHA256: 3175c2e829a0e23f14f5954a6db3316a70611dfa7aedc37483bac59667ac281a. Optional archival tools remain external configured files under tools; core installer does not embed them.
- Manual native dialogs/installed UI/physical print/scanner and unusual real documents remain acceptance gates.

Next preservation fix: a direct source probe found doc.select with duplicate page numbers shares page objects/widgets. An edit can affect another duplicate. Independent-copy insertion plus unique copied field names preserves separate editing; links/bookmarks need explicit fixtures before release. This is a known limitation of the 0.7.0 duplicate workflow until fixed. Continue with visual page organization and split tools after the preservation fix. Full goal remains active.

## 0.8.0 page organization candidate

- Fixed shared-object duplication: inserted copies have independent page objects and uniquely named copied form fields. Original links/bookmarks retain destination references; copied internal links target the first retained destination copy. Cropped/rotated links preserve their PDF rectangle and destination coordinates.
- Added thumbnail organizer with drag movement, accessible move controls, staged duplicate/remove/reset/cancel and one undoable Apply. Browser independent-copy edit/save/reopen passed.
- Added split exports: individual pages, fixed-size groups and custom semicolon-separated ranges. All ranges validate before any outputs; filenames are unique, output PDFs are reopened before publication, and per-file receipts preserve failures/interrupted jobs. Working revision and originals remain intact.
- Core candidate suite: 51 passed, including four duplication orders, eight cropped/rotated duplication/extraction cases and five split grouping/rollback/recovery cases. Independent PDFium rendering used. Full browser/package/native gates pending. Latest fully verified installer remains 0.7.0.

## 0.8.0 verified milestone

- All 65 Python tests and 10 browser UI tests passed (47.7s). Frozen worker passed independent page-copy/split checks plus OCR/Office/batch/signatures/archival with developer Python absent from PATH. Frontend/Rust/NSIS packaging passed.
- Actual bundled WebView2 smoke passed visual organizer apply/undo and split/reopen alongside all prior smoke workflows, with no captured page errors. Organizer and split screenshots visually inspected.
- Installer: artifacts/releases/0.8.0/Folio_0.8.0_x64-setup.exe (57,322,245 bytes). SHA256: 624fab20b0d7c572889360a8120987cea8d5d474581e57317a009a7b5d597c8b.
- This milestone fixes the shared-object duplicate-page limitation of 0.7.0. Duplicate links point at the first retained destination copy; copied form names are distinct. Complex shared/radio fields and named destinations need broader compatibility fixtures.
- Physical print/scanner, native file dialogs, installed UI and unusual personal PDFs remain manual acceptance gates. No personal documents or hardware jobs were used.

Next: exact visual crop controls and page-number/watermark customization, then remaining form/font/conversion/OCR/scanner/local-model work in the original roadmap. The full goal remains active; this milestone does not establish full feature parity.

## 0.9.0 geometry and numbering candidate

- Added independent visual left/top/right/bottom crop margins, point/mm/inch controls, drag-to-crop on the current page, size readout and reset to full MediaBox. Offset MediaBox origins are handled explicitly. Cropping hides rather than removes content.
- Added page-number starting value, format tokens ({n}, {total}, {page}, {pages}), top/middle/bottom position, left/center/right alignment, size/color/opacity and spacing. Watermarks share position/alignment/opacity/spacing controls. Duplicate page selections are deduplicated for these decorations. Preset whitelist supports the new settings.
- Core suite: 101 passed. Twenty-four crop cases compare exact retained pixels with PDFium across rotations and positive/negative origins, then repeat trim/reset/save/reopen. Twenty-four numbering cases check visual bounds and independent extraction after export. Invalid inputs leave the revision unchanged.
- New browser crop/reset/selection/unit/number/watermark/save/reopen workflow passed. Added explicit Text aria label after a locator failed during tool switching. Production frontend build passed before that final label change; full browser/package/native gates are next. Latest verified installer remains 0.8.0.

## 0.9.0 verified milestone

- All 115 Python tests and 11 browser UI tests passed (51.0s). Frozen-worker crop/reset/custom numbering and all prior smoke workflows passed with developer Python absent from PATH. Frontend/Rust/NSIS packaging passed.
- Actual bundled WebView2 smoke passed precise crop/apply/undo and custom number/apply/undo alongside all prior native workflows, with no captured page errors. Crop selection and decoration screenshots visually inspected. A saved-PDF text-trace probe confirmed watermark opacity 0.25 and number/watermark bounds; receipt copied with UI evidence.
- Installer: artifacts/releases/0.9.0/Folio_0.9.0_x64-setup.exe (57,327,765 bytes). SHA256: 207df31d16c7396d6f09af7511af84fcd51cbe5ca0151064c70a16ba5f8e3078.
- New page decoration supports one line of Latin text and standard Helvetica. Diagonal/image watermarks, richer font support and paragraph layouts remain separate work. Exact crop is a visibility change, not content removal.
- Installer UI/native dialogs, physical printing/scanning, high-DPI and unusual personal PDFs remain manual gates. No personal documents or hardware jobs were used.

Next: on-page form interaction, radio groups/detection and remaining text/font/OCR/conversion/structural Markdown/scanner/local-model work from the original roadmap. The full goal remains active.

## 0.10.0 on-page form candidate (12 October 2026)

- Added direct on-page text, multiline, checkbox, dropdown and single-select list controls. Their bounds follow crop/rotation; the controls rotate with the field. Read-only fields are disabled and maximum lengths are reflected in the UI and enforced by the engine. Unsupported signature/radio/multi-select overlays remain explicit limitations.
- Form drafts survive page/tab changes in memory, including logical shared-name synchronization. Apply includes edits from visited pages; Save applies pending values before exporting a separate copy. Print preparation, certificate signing and other working edits apply current staged values first. Closing/undo with pending values gives a specific warning. Ctrl+Z/Y inside inputs uses native input editing history.
- Four new backend cases passed geometry/flags/fill/export/reopen/undo/source preservation at all rotations with independent PDFium rendering. The existing 101 core cases passed before those additions.
- Three targeted browser tests passed: original sidebar form filling, direct controls at all rotations, and page/tab drafts plus Save without separate Apply. The old locator was scoped to the sidebar to distinguish the new on-page control, and the maxlength fixture expected values were corrected to fit 8 characters. Production frontend build passed before final lookup/checkbox refinements; full gates are next.
- Latest fully verified installer remains 0.9.0. Radio group creation/detection, multi-select/export-label choices, richer field appearance and unusual real forms still need work. Full goal stays active.

### Form candidate preservation refinement

- Page/tab draft, auto-save and all rotated control browser cases passed. Screenshot review refined multiline sidebar controls and listbox presentation; three affected browser paths passed again.
- A same-named widget fixture exposed independent values/appearances despite the shared logical name. Fill now gathers changed logical names, synchronizes supported widgets on all pages, rejects conflicting new values, and rejects unknown widget IDs. Read-only/length protections apply to every affected widget. Radio widgets remain outside this synchronization path.
- All 106 current core tests passed, including shared-field appearance extraction on both pages after flattening with PDFium. Full package/native gates pending. Latest verified installer remains 0.9.0.

## 0.10.0 verified milestone (12 October 2026)

- All 120 Python tests passed (75.20s). All 13 browser workflows passed before the final multiline/list/shared-value refinements; the three affected form workflows passed again after those refinements (22.2s). Frontend/Rust/NSIS packaging passed.
- Frozen worker passed form fill/export/reopen plus all prior smoke workflows without developer Python on PATH. Actual bundled WebView2 passed direct on-page text fill/apply/undo alongside all prior native checks, with no captured page errors.
- Synthetic cropped/rotated form control screenshots visually inspected. Unknown/conflicting-value development probes reject requests without changing the source or revision; receipt is preserved with UI evidence. Shared field appearance is verified independently after flattening.
- Installer: artifacts/releases/0.10.0/Folio_0.10.0_x64-setup.exe (57,326,840 bytes). SHA256: 3d7d0622480e5d8b489687094be6aafbf69f665a2f4992d9649d692d3958d264.
- Drafts remain in memory until applied or saved; browser/app shutdown recovery of unapplied values is not implemented. Advanced radio/multi-select/export-label choices, scripted calculations, richer fonts and unusual forms remain compatibility work. Native dialogs, installed UI, physical printer/scanner and high-DPI acceptance remain manual gates.

Next: exercise unusual field-name keys and ensure split/image/comparison exports include staged form values, then radio groups/detection and the remaining original text/OCR/conversion/scanner/local-model roadmap. Full goal remains active.

## 0.10.1 form-output candidate (12 October 2026)

- Draft name/ID maps now have null prototypes, and membership checks use own properties. Fields named __proto__, constructor and toString can be staged and saved normally; history clearing keeps the same representation.
- Split, image export and comparison now apply pending form values before processing the current document. Existing save/print/sign/working-edit handling remains in place.
- New browser test passed unusual-name values in independently reopened split PDFs, OCR recognition of the changed value in an exported PNG, a changed comparison against the pre-edit PDF and a final reopened saved value. Original hash stayed unchanged. Frontend build passed before the last history-clearing refinement; full release gates are next.
- Latest fully verified installer remains 0.10.0. Radio/multi-select/detection/font/script compatibility and the full original roadmap remain active work.

## 0.10.1 verified milestone (12 October 2026)

- All 120 Python tests passed (72.85s); all 14 browser workflows passed, including reopened unusual-name split values, OCR recognition of staged content in PNG output and pixel comparison of staged form changes. Frontend/Rust/NSIS packaging and frozen-worker gates passed.
- Actual bundled WebView2 passed the standard native smoke plus a separate unusual-name draft/print-preparation/undo check. Both receipts match the same application/worker hashes and report no captured page errors. No physical print job was submitted. Milestone preservation now verifies the additional native receipt's binary hashes too.
- Installer: artifacts/releases/0.10.1/Folio_0.10.1_x64-setup.exe (57,325,854 bytes). SHA256: b55e3708fb342445b515fb01e288d7175667406c520f70b1e7bda7917e9157e9.
- Resolves the 0.10.0 staged-value gaps for split/image/comparison and unusual name keys. Drafts are still memory-only until applied or saved. Advanced form compatibility and all original roadmap items remain separate work.

Next: radio groups and field detection, followed by remaining font/text/OCR/conversion/scanner/local-model work. Native installed UI/dialogs, physical printing/scanning, high-DPI and unusual personal documents remain manual acceptance gates. Full goal remains active.

## 0.11.0 radio-group candidate (12 October 2026)

- Added real AcroForm radio group creation with one parent field, distinct O1/O2/... appearance states, option labels and exclusive selection. Existing normal fields remain in the AcroForm catalog. Added radio choices to Create form field and direct on-page radio controls.
- Fill updates parent values and widget appearances together, validates option states/conflicts, honors read-only/no-toggle-to-off flags, and rejects unsupported mixed-name hierarchies. Radio widgets use their dedicated path rather than the ordinary widget updater.
- Duplicate-page tests exposed copied children being renamed independently. Copied radio parents now receive one unique group name without regenerating their appearance streams; copied selections stay independent of the original.
- All 113 core tests passed. Seven radio cases cover all rotations, independent PDFium checked-button rendering, source/form preservation, save/reopen/undo, invalid values/creation, restriction flags and independent copies. Browser create/select/undo/save/reopen passed (8.6s on the final stable run); frontend build passed before the final field-type accessibility label. Full package/native gates pending. Latest verified installer remains 0.10.1.

### Radio candidate render refinement

- The first candidate package passed 127 Python cases and frozen radio creation/fill/reopen, but is not the final verified release. Printed-output review centered option captions beside their buttons and made field creation honor the color control; radio creation no longer shows an unused default-text field. Caption bounds pass at all rotations.
- A screenshot caught a transient canvas between revisions. The viewer now owns loaded PDFs by path/revision, records completed rendering, and enables page editing controls only for the current completed render. The initial regression run passed 14 workflows but the stamp harness drew before the newly enforced render readiness and timed out with Apply disabled. Drawing harnesses now wait for page loading to finish; all gates will be refreshed before release.

### Radio PDF.js compatibility fix

- A canvas pixel assertion proved that the generated radio PDF could render blank in PDF.js while PDFium showed its content. Diagnostic annotation parsing traced this to explicit null child field entries (especially /T null), which PDF.js tried to decode as field-name strings.
- New radio widgets now omit inherited field entries entirely instead of storing nulls. Parent field/value inheritance and appearances remain intact. The seven radio backend cases and browser create/select/undo/save/reopen now pass, including a non-white canvas assertion after undo. Annotation rendering was restored after an isolation probe; it is not disabled in the product.
- Refreshing final full/browser/package/native gates is still required. Earlier 0.11 candidate installers are not the verified baseline; latest verified remains 0.10.1.

## Photo scanning request (12 October 2026)

User requested a CamScanner-style scan image function. Add a local photo-to-document workflow with image import, automatic corner proposal plus editable four-corner crop, perspective correction, color/grayscale/document enhancement, preview, page ordering and multi-page PDF output. Preserve source images and review output before saving. Offline OCR integrates with the existing PDF pipeline. Camera capture and physical scanner acceptance remain separate from photo import; do not substitute plain image-to-PDF for document scanning. Prioritize this after the in-flight 0.11 verification.

## 0.11.0 verified milestone (12 October 2026)

- All 127 Python tests passed (76.99s), all 15 browser workflows passed (80.49s), frozen-worker radio/create/fill/export/reopen and frontend/Rust/NSIS packaging passed. Browser pixel checks verify painted PDF content, beyond HTML form overlays.
- Native bundled WebView2 passed radio creation/exclusive fill/undo and prior workflows, plus unusual-name draft/print-preparation/undo verification. Both receipts match current application/worker hashes and captured no page errors. Browser/native form screenshots reviewed.
- Installer: artifacts/releases/0.11.0/Folio_0.11.0_x64-setup.exe, 57,336,897 bytes, SHA256 9f0b3c4138be0d871880dd7b3de936b56530f7a5688ea04c043a53e2bde13780.
- Standard radio groups are supported; advanced hierarchical/multi-select/export-label compatibility, persistent unapplied drafts, physical printer/scanner and installed/high-DPI acceptance remain separate work. Full goal remains active.
- Next priority: requested photo document scanning with perspective crop and enhancement, followed by remaining roadmap.

## 0.12.0 photo scanner candidate (12 October 2026)

- Added local photo import with EXIF orientation/transparency handling, automatic quadrilateral boundary proposal and full-photo fallback. Review/drag or keyboard-adjust all four corners; crossed/outside/tiny crops reject. Perspective warp preserves document proportions, with rotation, original color, grayscale, background-normalized document and adaptive black/white previews.
- Ordered multi-photo output opens an unsaved PDF session for review, existing offline OCR and Save a copy. Inputs remain intact and hash checks reject changed source photos. Failed creation does not publish a partial session. 40 MP input/16 MP corrected output/100 page limits keep processing bounded. Multi-frame TIFF is explicitly rejected; individual photos supported.
- Six backend tests passed detection/perspective/filter/rotation/EXIF/fallback/rejection/source-preservation and independent PDFium save/reopen. Initial browser workflow passed corner validation, enhancement preview, ordering, save and independent reopen; screenshot review prompted smaller image display and sticky actions, with final gates still pending.
- Uses project-local Apache-licensed OpenCV and NumPy; license collection and packaging need refresh. Camera capture, scanner hardware, curved-book dewarping and unusually lit/cluttered photos remain separate compatibility work. Latest verified installer remains 0.11.0.

## 0.12.0 verified milestone (12 October 2026)

- All 133 Python tests passed (71.00s), all 16 browser workflows passed (93.27s), frozen-worker photo detection/perspective/enhancement/create/export/reopen passed without developer Python, and frontend/Rust/NSIS packaging passed. License resources include OpenCV/NumPy and bundled third-party notices (126 packages).
- Actual bundled WebView2 passed photo scanning commands with corrected portrait/landscape page order and PDF reopen, alongside the full standard native suite and separate form draft suite. Both receipts match the same application/worker hashes and report no page errors. Browser scanner UI screenshot reviewed; end-to-end corner validation, preview, page ordering and Save/reopen are automated in browser mode.
- An additional native UI probe attempted a fixture file-picker shim but stalled before image import; Tauri invoke cannot be replaced by that approach. The probe is not acceptance evidence. Native OS photo picker, installed UI, high-DPI and representative personal photos remain manual gates. No user-installed Folio process was stopped.
- Installer: artifacts/releases/0.12.0/Folio_0.12.0_x64-setup.exe, 111,630,348 bytes; SHA256 9e9ef7765ffa861ff98a1e17744b250f31ce96aa69eac96d9fd761e895775626.
- Photo scanning is implemented locally; camera capture, physical scanner control, curved-book dewarping and broader lighting/clutter fixtures remain work. Original roadmap and goal remain active.

## 0.13 direct text and camera candidate (12 October 2026)

- User requested direct text selection/editing and click-to-add text, replacing the rectangle-drawing workflow. Added paragraph hit testing, a borderless on-page editor with caret/word selection, font/size/color toolbar, Apply/Ctrl+Enter and Escape cancellation. Edit mode now defaults to existing text. Typing measures and expands into available space; paragraph fitting/collision checks protect neighboring content. Save/export preparation applies staged text; drafts survive page navigation in memory, with close/undo warnings.
- Engine identifies the selected source paragraph by content and position rather than a user rectangle, removes its original text, reuses embedded fonts when glyph coverage permits, preserves baseline/style for supported uniform paragraphs, and validates layout on a scratch page before committing. All ten direct-engine cases passed: crop/rotation, source/font/baseline/neighbor preservation, extended characters in an embedded font, wrapping, insertion, independent reopen, undo and atomic rejection.
- Source text-layer scale variables were missing, which misaligned PDF.js text hit targets on rotated pages. Added the viewer scale/rounding variables; all rotation UI gates pending after this fix. Initial direct-edit browser workflow passed stage/navigation/save/cancel/click-add. Legacy add-text browser checks now use actual click-and-type interaction.
- Camera candidate adds explicit Start/Stop, device selection, video-only preview, repeated capture into private app-data photos and the scanner pipeline. Twelve scanner/backend cases and synthetic-camera capture/denial/pending-close/track-stop browser checks passed. No real camera was activated automatically. Native tests now use isolated project-local WebView profiles to avoid conflicts with a user-open Folio. Full combined gates and packaging remain pending; latest verified installer stays 0.12.0.

## 0.13.0 verified milestone (12 October 2026)

- All 149 Python tests passed (83.95s); all 19 browser workflows passed (113.94s). Word-level keyboard selection/replacement passed separately, then both direct-text workflows passed again (18.92s) after the unchanged-draft refinement. Receipts are preserved separately so the final affected rerun and full regression scope remain clear. Frontend, frozen-worker, Rust and NSIS gates passed. The final frontend refinement and native asset fix were rebuilt before native acceptance.
- Actual bundled WebView2 passed direct existing-text editing, click-to-add, Ctrl+Enter, undo, all prior standard native workflows and the separate unusual-name form draft/print-preview/undo fixture. Both receipts match the final application/worker hashes and report no page errors. Browser/native editor screenshots reviewed.
- Actual bundled WebView2 also passed two synthetic-video captures, PDF creation/export/reopen and released video tracks when closed. The test first verifies that the device inventory identifies the fake video fixture, so it never requests a real camera stream. No actual printer/scanner/camera operation was performed. Real camera permission/capture and native file dialogs remain manual acceptance gates.
- Native diagnostics exposed Windows package virtualization: the app-data root canonicalized to ordinary Roaming while new session PDFs resolved under the Codex package LocalCache. Session-owned PDF/image paths returned by the worker now receive exact asset permission before the frontend loads them. Scope extension is restricted to existing PDF/PNG/JPG/JPEG files under sessions, with parent traversal rejected. Native rendering/thumbnails/print preview passed and direct asset access to the original source fixture outside app-data still returns 403. Debug-only path diagnostics retain observability.
- Native harnesses now allocate free debugging ports, isolate WebView profiles under project artifacts and stop their own process trees. No current native test processes remain; user-installed instances are not stopped. The old sidebar Text locator was updated to the new click-and-type interaction.
- Installer: artifacts/releases/0.13.0/Folio_0.13.0_x64-setup.exe, 111,645,476 bytes; SHA256 d36729c4ded38bcce1d6fd41854b5fc8c333f028c680c54b6b3cf3816a9cf9a3.
- Mixed-style paragraphs require an explicit uniform replacement font. Angled baselines, advanced shaping, moving surrounding layout, scan reconstruction, persistent unapplied drafts and unusual real PDFs remain work. Camera photos are retained privately until a cleanup policy is implemented. No Acrobat/iLovePDF parity claim. Full original goal stays active.
- A user-supplied untracked root image remains untouched, unread by automated tests and excluded from the source commit/release. Milestone preservation now enforces clean tracked source and committed untracked source while permitting unrelated non-source inputs.

## 0.14 styled paragraph candidate (12 October 2026)

- Direct Original-style edits now map unchanged characters to their source font/size/color/baseline-offset runs. Replacement text inherits the replaced run; inserted text inherits the adjacent run. Styled word wrapping is measured before publication, preserving neighboring content and atomic failure. Size changes scale relative sizes, and explicit color changes apply to the paragraph. Choosing another font continues to deliberately use a uniform style.
- Four rotated mixed-font/size/color cases plus styled wrapping/atomic overflow passed with independent PDFium extraction/rendering and original hashes preserved. The existing ten direct-engine cases passed. Browser mixed-amount edit/save/undo passed alongside the two existing direct workflows; relative-size/color and final full gates are next.
- Styled paragraphs are currently limited to 5,000 characters and available source glyphs. Ambiguous replacements inherit a deterministic adjacent/replaced style and need review. The borderless typing control still previews the first style; saved/applied PDF formatting is preserved. Rich live preview, shaping/angled baselines, surrounding-layout movement and original-font fallback remain further work. Latest verified installer stays 0.13.0; full goal remains active.

## 0.14.0 verified milestone (12 October 2026)

- All 155 Python tests passed (66.02s), all 20 browser workflows passed (103.61s), frozen-worker original mixed-style editing passed without developer Python, and frontend/Rust/NSIS packaging passed. Styled tests cover all page rotations, font/color/relative-size preservation, insertion inheritance, wrapping, explicit paragraph scaling/color and atomic overflow rejection.
- Actual bundled WebView2 passed standard/draft native checks, synthetic camera capture and a separate styled-edit/save/undo check. Saved font/size/color runs were checked with PyMuPDF and independently reopened/extracted/rendered with PDFium. All four receipts match current application/worker hashes and report no page errors. Native styled screenshot reviewed. Physical printer/scanner/real camera and installed dialogs remain manual gates.
- Installer: artifacts/releases/0.14.0/Folio_0.14.0_x64-setup.exe, 111,655,281 bytes; SHA256 e38ff0c7443721a5fb62dd35b34926d5788ef90d7b6957e5ac919c515ed6c7f9.
- Original paragraph styles now preserve mixed fonts, relative sizes and colors after applying. The live typing control remains a first-style preview. Style inheritance across ambiguous replacements, missing source glyphs, opacity/decorations/semantic anchors, advanced shaping and moving surrounding layout need further work. Styled edits are bounded to 5,000 characters. Full original goal remains active; no broad compatibility/parity claim.
- Next: richer live editing/formatting, shaping/glyph fallback and remaining text/OCR/conversion/forms/scanner/archival/local-model roadmap. User non-source inputs remain untouched and excluded from tests/commits.

## 0.15 mixed-page OCR candidate (12 October 2026)

- Added persistent missing-text OCR for mixed digital/raster pages. Recognition-only rasters mask existing searchable words; overlapping recognized words are discarded, and only invisible text is imported. Actual images/vectors/digital text remain intact. Pure digital pages skip, while vector-only textless pages retain full-page recognition.
- Added missing-text/legacy skip-text mode and 100-400 DPI controls in Convert and saved batch recipes, plus processed/skipped/added-word feedback. A preallocation 40 MP guard rejects oversized rendering before committing.
- Four rotation/crop fixtures passed independent PDFium exact-pixel preservation, digital-text preservation, scanned-region word geometry, repeat-count stability, saved reopen, undo and original hashes. Legacy skip and atomic oversized rejection passed. Hidden OCR edits now explain that changing invisible text is not visible scan reconstruction; the page UI rejects that misleading workflow before staging an edit. The browser mode/repeat/save/independent pixel/unsupported-edit path passed. Batch mode persistence and final gates are next.
- English remains the only bundled OCR language. Recognition accuracy, overlapping/touching text, tiled complex images, deskew and further languages remain work. Latest verified installer stays 0.14.0; full original goal remains active.

## 0.15.0 verified milestone (12 October 2026)

- All 162 Python tests passed (70.61s); all 21 browser workflows passed (108.31s). The OCR workflow passed again (12.1s) after its screenshot wait was aligned with completed revision rendering. Full/affected receipts are preserved separately. Frozen-worker mixed OCR/repeat checks passed without developer Python, and frontend/Rust/NSIS packaging passed. Final dependency lock differences are the Folio version only.
- Actual bundled WebView2 passed standard/draft, synthetic camera, styled text and a new mixed-OCR workflow. The saved OCR PDF was independently reopened with PDFium: recognized scan text is searchable, digital words occur once, and rendered bytes exactly equal the original page. All five receipts match the final application/worker hashes and report no page errors. Native/browser completed OCR screenshots reviewed.
- Added OCR mode/DPI controls and processed/skipped/word feedback, including saved batch settings. Mixed scanned/digital pages now receive missing text, repeated recognition does not duplicate tested words, and pure digital pages skip. Oversized raster dimensions reject before allocation. A hidden OCR word cannot be misleadingly edited as visible scan text; both UI and backend explain the reconstruction limitation without changing the revision.
- Installer: artifacts/releases/0.15.0/Folio_0.15.0_x64-setup.exe, 111,689,832 bytes; SHA256 c73f7ce8ec81b58abf5fc17bdd3d55513497c1b3d98acf12b5548b5fc6105d98.
- English-only OCR, spelling/complex layouts, touching or overlapping content, tiled images, deskew, further languages and visible scan reconstruction remain work. Real printer/scanner/camera, installed dialogs, high-DPI and representative personal PDFs remain manual acceptance gates. User non-source image remains untouched and excluded from tests/source commit. Full original goal stays active.

## 0.16 multilingual OCR candidate (12 October 2026)

- Added bundled offline English, Malay and Simplified Chinese recognition, including supported combinations, with language selection in Convert and saved batch recipes. The official tessdata_fast models are pinned to commit 87416418657359cb625c412a48b6e1d6d41c29bd; worker/ocr-models.json records sizes, SHA256 and official Git blob identities. Asset preparation verifies model hashes; packaging retains model provenance and Apache-2.0 notices.
- Eleven initial model checks passed: Malay/Chinese/combined recognition, independent saved PDFium text and exact-pixel preservation, source hashes, malformed/unsupported language rejection, missing-model rejection and available language reporting. Added restart/batch recognition and validation before preset persistence; full suite running.
- Added browser language selection/save/reopen coverage, frozen-worker multilingual checks and an isolated native WebView2 combined-language workflow. Packaging and native acceptance remain pending. Latest verified installer remains 0.15.0. Language accuracy on real scans, deskew, complex/touching text and visible scan reconstruction remain work; full original goal stays active.

- Full candidate source gates passed: 175 Python tests (100.04s), 22 browser workflows (2.2m), frontend TypeScript/Vite build and git diff whitespace checks. Language UI/save/reopen and independent exact-pixel/text checks passed. Lockfile differences are the Folio version only. Packaging is running; release acceptance is not yet claimed.

- Final browser regression with durable JSON evidence passed all 23 workflows (2.3m), including saved multilingual batch language after dialog reopening and independent recognition/pixel/source checks. artifacts/ui/full-regression-0.16.0.json preserves the full receipt. Packaging repeated all 175 Python tests successfully (80.25s). Frozen worker recognized Malay, Chinese and all-three combination with developer Python removed from PATH; frontend build passed. Browser multilingual screenshot reviewed. Rust/NSIS and native gates remain pending.

## 0.16.0 verified milestone (12 October 2026)

- All 175 Python tests passed; the package repeated them successfully in 80.25s. All 23 final browser workflows passed in 137.74s, with full JSON evidence preserved. TypeScript/Vite, frozen worker, Rust and NSIS gates passed. The frozen worker recognizes bundled Malay, Simplified Chinese and combined languages without developer Python.
- Actual bundled WebView2 passed standard/draft native workflows, synthetic camera capture, styled direct editing, mixed-page OCR and multilingual OCR. All six native receipts match app SHA256 a05e4f88b79ca9963eeb0cfe6afc3c3cd2781ce41a75a538bd238dfe411a87d4 and worker SHA256 51e75df9fdaf40f06c21d192d47403d1ff22157b3a9243e6fd2a41c97050fd61, with no page errors. Browser/native multilingual screenshots reviewed. Independent PDFium saved-output checks verify recognized Chinese text and exact visible pixels; source hashes stay unchanged. Existing direct click-and-type editing remains verified.
- Installer: artifacts/releases/0.16.0/Folio_0.16.0_x64-setup.exe, 114,610,996 bytes; SHA256 be23918060a16f84667c30b1d9dbd2c5fcf448c61d3dad8d513c98b4b99be64e. Earlier verified releases remain preserved.
- Language selection is available in Convert and saved batch recipes. Model provenance and Apache-2.0 notices accompany packaging; downloaded assets are pinned and SHA256 checked. Invalid language combinations reject before preset persistence or document processing. No account, paid service or personal-document upload is required.
- Recognition accuracy on difficult scans, deskew, further languages, rich live text formatting, complex shaping and visible scan reconstruction remain work. Real printer/scanner/camera, native dialogs/installer UI, high-DPI and representative personal PDFs remain manual gates. The untracked user photo remains untouched and excluded from automated tests/source commits. Full original goal remains active.
- Next: improve recognition preparation/deskew and visible scan editing, then continue the remaining full roadmap. Preserve direct on-page text editing rather than reintroducing drawn text rectangles.

## 0.17 scan straightening candidate (12 October 2026)

- Added fine-angle straightening before enhancement and quarter-turn rotation. Expanded white margins preserve edge content; bounded output dimensions retain the scanner's image limits. Manual angles are limited to -15 through 15 degrees, and invalid/nonfinite values reject without partial sessions. Black-and-white enhancement remains binary after straightening.
- Added a local baseline-alignment suggestion using bounded image projections, ignoring outer page borders and leaving blank/low-confidence pages at zero. The UI provides a suggested preview, manual angle, reset and per-photo review message. Suggestions are proposals to review, not automatic document-orientation acceptance.
- Initial affected backend gates passed 24 tests covering independent tilted text fixtures in both directions, saved PDFium reopen, original hashes, edge retention, quarter-turn/filter behavior and invalid-angle atomicity. Frontend build passed before the 0.17 version bump. Browser proposal/reset/manual/save workflow is running. Full regression, packaged/native gates and installer remain pending; latest verified release is 0.16.0. Full original goal stays active.

- Full candidate source regression passed: 187 Python tests (113.37s), all 24 browser workflows (2.4m) including straightening proposal/reset/manual/save and camera/direct-text/OCR regressions. Full browser JSON is preserved at artifacts/ui/full-regression-0.17.0.json. Lockfiles change only the Folio version; whitespace checks passed. Frozen/native straightening gates are added. Packaging is starting; latest verified release remains 0.16.0.

- Packaging repeated all 187 Python tests successfully (77.98s). Frozen-worker straightening suggestion/preview/create/export and independent reopen passed without developer Python, alongside multilingual OCR and existing tools. Final frontend and Rust release compilation passed. Browser straightening screenshot reviewed. NSIS and native acceptance remain pending.

## 0.17.0 verified milestone (12 October 2026)

- All 187 Python tests passed (113.37s); packaging repeated them successfully (77.98s). All 24 browser workflows passed (145.85s), with full JSON preserved. Frontend, frozen worker, Rust and NSIS gates passed. Straightening tests cover both tilt directions, preview/reset/manual adjustment, expanded margins, edge-content retention, binary enhancement, quarter turns, invalid-angle atomicity, saved PDFium reopening and original hashes.
- Actual bundled WebView2 passed standard/draft native workflows, synthetic camera capture with fine-angle preview/reset controls, original styled editing, mixed-page OCR and multilingual OCR. Native scanner commands proposed the known tilted fixture angle, created/exported a corrected PDF, and independent PDFium reopening checked expanded dimensions and retained visible content. All six native receipts match app SHA256 71e168ef6a6a98f576409ed27a267448c2595432e5f4f41deb940db140a05587 and worker SHA256 6033f87968f1aaedd66fd776e93732b72cd8a5e4b53f4980f9509d88fd60a86f; no page errors. Browser and native straightening screenshots reviewed. No real camera/printer/scanner was activated automatically.
- Installer: artifacts/releases/0.17.0/Folio_0.17.0_x64-setup.exe, 114,617,538 bytes; SHA256 d524590b5f18e73192538713d89aa2c5c207a78ff1a733a6f3f4661489bcf55b. Older milestones remain preserved.
- Fine-angle correction is applied to scanned photo output before enhancement and quarter-turn rotation. Suggested angles require review; manual correction/reset is available per photo. Blank/low-confidence pages keep zero. Diagrams, columns, uneven backgrounds and curved text can confuse alignment; broader fixtures and curved-page reconstruction remain work. This is not recognition-only deskew of existing PDF pages.
- Real hardware, native photo picker/installer dialogs, high-DPI and representative personal PDFs remain manual gates. The user photo remains untouched and excluded from tests/source checkpoints. Full original goal stays active; no Acrobat/iLovePDF parity claim.
- Next: richer live on-page text formatting and visible scan-text reconstruction, followed by the remaining full FEATURES.md roadmap. Keep direct click/edit and click/add without drawn text boxes.

## 0.18 rich live text candidate (12 October 2026)

- Replaced the single-style textarea with a borderless on-page rich text surface. Source inspection includes font/size/color/flags/baseline-offset runs; live replacements inherit source styles using a browser port of the engine's no-junk SequenceMatcher rules. Changed size scales relative sizes and explicit color overrides all runs. Browser standard serif/sans/monospace representations retain bold/italic/color variation; exact custom embedded-font rendering and line metrics remain further work.
- Added in-editor draft undo/redo, plain-text paste (no pasted HTML execution), explicit newline insertion, selection restoration across styling, composition-event protection and normal Tab navigation. A trailing-newline caret issue found during browser testing was fixed with a terminal break. Source preservation and final PDF placement/neighbor collision safeguards remain in the worker.
- Eighteen affected Python checks passed, including 160 deterministic Unicode/repetition/tie edit comparisons between browser and PDF style mapping. Initial direct browser workflows passed; affected rich typing/undo/redo/newline/paste/relative-size/save/independent reopen passed after the newline fix. Added synthetic composition and keyboard Tab coverage; full regression is running. A 5,000-character repeated-text mapping probe took 140 ms locally; broader performance and actual OS IME acceptance remain work.
- Styled edits retain the existing 5,000-character limit. Undo history in the active editor is memory-only and resets when its editor remounts; drafts still survive page/tab navigation. Browser font substitution, exact live wrapping/spacing, bidi/complex shaping, selected-run formatting controls and visible scan-text reconstruction remain work. Latest verified installer stays 0.17.0; packaging/native gates and full original goal remain active.

- Full source regression passed: 189 Python tests (103.74s) and all 25 browser workflows (2.4m). Rich typing/undo/redo/newline/plain-paste/relative-size/save/independent reopen passed, including synthetic composition and Tab-to-toolbar behavior. Full JSON is preserved at artifacts/ui/full-regression-0.18.0.json. Frozen source-run and native live-style/draft-history checks are added. Packaging is starting; latest verified installer remains 0.17.0.

- Packaging repeated all 189 Python tests successfully (74.45s). Frozen source-run inspection and existing direct/mixed-style PDF edits passed without developer Python; final frontend build passed. An additional affected rich-editor check passed (11.5s), covering formatting undo/redo as well as typing/IME-event/Tab/newline/paste/save/reopen. The full regression JSON remains separate and unchanged. Browser live-style screenshot reviewed. Rust/NSIS and native acceptance remain pending.

## 0.18.0 verified milestone (12 October 2026)

- All 189 Python tests passed (103.74s); packaging repeated them successfully (74.45s). All 25 browser workflows passed (146.14s), followed by the enhanced affected rich-editor check (11.5s) covering formatting undo/redo. Full JSON is preserved separately; the affected rerun changed test coverage only. Frontend, frozen worker, Rust and NSIS gates passed. Independent browser/PDF style mapping matches across 160 Unicode/repetition/tie edits; saved output retains fonts, colors and relative sizes with PDFium reopen/render/text verification and original hashes.
- Actual bundled WebView2 passed standard/draft native workflows, synthetic camera/straightening, live mixed-style editing/draft undo/redo/apply/save/document undo, mixed-page OCR and multilingual OCR. All six receipts match app SHA256 c82c9d02b1528575057f72281d11353e606ae22ddebb81a7eee028e5d5f92f51 and worker SHA256 75d1a8fd9e8608117aa5daacf1d3ff628f7e577b9232ff0128bf65d72f558822, with no page errors. Browser/native live-style screenshots reviewed. No real hardware or OS IME was activated automatically.
- Installer: artifacts/releases/0.18.0/Folio_0.18.0_x64-setup.exe, 114,621,643 bytes; SHA256 f82aac1f3ec64324166d9d5b09081c872b5dcdfcea27723673ae0d5e1bf58c34. Earlier milestones remain preserved.
- The on-page editor now visibly retains mixed weight/italic/size/color/baseline-offset runs while typing. It supports caret/word selection, draft undo/redo, explicit newlines, literal-text paste, synthetic composition-event handling, Tab-to-toolbar navigation and automatic application before saving. Original fonts remain reused in supported saved outputs. Draft undo history is limited to the active editor and is memory-only.
- Exact embedded-font live faces/metrics, complex shaping/bidi, selected-run formatting, style-inheritance ambiguity, decoration/opacity/semantic anchors, surrounding-layout movement and visible scan reconstruction remain work. Color currently overrides runs when different from the first source color; resetting to that source color restores original run colors. A dedicated uniform-color override is still needed for that same first color. Styled paragraphs remain bounded to 5,000 characters; the repeated-text mapping probe is evidence for one fixture, not a general performance claim.
- Real printer/scanner/camera, native dialogs/installer UI, high-DPI, actual Windows IME and representative personal PDFs remain manual gates. The user photo remains untouched and excluded from tests/source checkpoints. Full original goal stays active; no parity claim.
- Next: exact live font resources/metrics and clearer run/paragraph color controls, followed by visible scan text reconstruction and the remaining full roadmap.

## 0.19 explicit paragraph colors candidate (12 October 2026)

- Added Original colors / One color controls for mixed original-style paragraphs. Changing the color picker explicitly selects One color, including the first source color. Original colors restores source run colors. Client and engine share explicit color-mode semantics; old API callers retain auto mode. Font/size retention and scratch-fit/source-preservation guards remain intact. Selecting a uniform color already present in all source runs clears an unchanged draft without creating a revision.
- Floating toolbar wraps within the page and positions above/below actual edited text bounds. Added matching inspection keys/readiness so edit tools wait for the correct document/revision/page metadata. A reopen test initially clicked the old page before asynchronous Open completed; the test now waits for a new session plus text readiness instead of interpreting that ignored busy-state click as a metadata failure.
- Twenty-three affected Python tests passed; expanded browser/engine mapping parity includes mixed colors and explicit color modes. The focused UI test passed one-color preview, draft undo/redo, toolbar bounds, same-source-color-only save/reopen, source hash and no-op revision behavior. Full regression including 30-percent zoom is running; frozen/native color checks are added. Latest verified installer remains 0.18.0. Full original goal stays active; exact live fonts/shaping/selected-run formatting and scan reconstruction remain work.

- Full source gates passed: 194 Python tests (123.56s) and all 26 browser workflows (2.7m), including original/one-color draft undo/redo, source-first-color-only save/reopen, no-op revision preservation, toolbar bounds at 100 and 30 percent zoom, direct editing, camera/scanning and OCR regressions. Full browser JSON is preserved at artifacts/ui/full-regression-0.19.0.json. Browser paragraph-color screenshot reviewed. Packaging is starting; latest verified installer remains 0.18.0.

- Packaging repeated all 194 Python tests successfully (74.68s). Frozen worker passed explicit same-source-color override with retained fonts and saved output; final frontend and Rust release compilation passed. Lockfile differences are the Folio version only. NSIS/native acceptance remains pending.

## 0.19.0 verified milestone (12 October 2026)

- All 194 Python tests passed (123.56s); packaging repeated them successfully (74.68s). All 26 browser workflows passed (163.43s), with full JSON preserved. Frontend, frozen worker, Rust and NSIS gates passed. Color tests preserve fonts/relative sizes/source hashes, independently reopen/render saved PDFs, reject invalid modes atomically, compare browser/engine mapping with mixed source colors, and cover original/uniform mode selection/draft undo/redo/no-op revision behavior.
- Actual bundled WebView2 passed standard/draft native workflows, mixed live styled editing, original/one-color save/reopen and unchanged-color no-revision checks, synthetic camera/straightening, mixed-page OCR and multilingual OCR. All six receipts match app SHA256 93ab4a15840a68c3a0bb593d8bd60e7452dd6ee79bb15fefa79389a1d88b0aac and worker SHA256 30afeb12ad9ce28188b6024cec8eaf51bb9bca5157591f382d29172ba460c97e, with no page errors. Browser/native paragraph-color screenshots reviewed. No real hardware or Windows IME was activated automatically.
- Installer: artifacts/releases/0.19.0/Folio_0.19.0_x64-setup.exe, 114,617,756 bytes; SHA256 1327e9800c347b854434c91fd9a02188525fcbeb7c437da4f6155a6d54229387. Earlier releases remain preserved.
- Original colors / One color now express paragraph color intent separately from the picker value. Uniform overrides work even when the chosen color equals the first source color. Matching source colors leave an unchanged draft without an extra revision. The floating toolbar wraps within the page and stays above/below edited text; browser bounds were checked at 100 and 30 percent zoom. Edit-mode readiness matches the active document/revision/page metadata. Reopen tests wait for the new session because Open is asynchronous.
- Exact embedded-font live rendering/metrics, shaping/bidi, selected-run formatting, decorations/opacity/anchors, layout movement and visible scan-text reconstruction remain work. Styled paragraphs retain the 5,000-character bound, and active-editor undo remains memory-only. Hardware, native dialogs/installer UI, high-DPI, real Windows IME and representative personal PDFs remain manual gates. User root photo stays untouched and excluded from tests/source checkpoints. Full original goal remains active; no parity claim.
- Next: exact live font resources/Unicode mapping/metrics, then selected-run formatting and visible scan-text reconstruction, alongside the remaining full roadmap.

## 0.20 embedded font preview candidate (12 October 2026)

- Added read-only preview_fonts extraction for the requested font names on the current page/revision. Original embedded TTF/OTF/WOFF/WOFF2 bytes are returned with hashes, format and flags. Missing, unsupported, ambiguous-name or oversized resources explicitly fall back. Limits are 32 requested names, 8 MB per font and 12 MB total; overflow variants remain visibly substituted rather than falsely reported as loaded. Source documents and revisions are unchanged by extraction.
- The borderless editor loads original byte buffers through FontFace, applies original weight/italic descriptors to avoid synthetic duplication, uses the loaded family in text and width measurement, and releases owned faces on close. Cancellation prevents late-loaded faces from being registered. Original-font loading/substitution is visible in the floating toolbar. Automatic CSS kerning/ligatures are disabled for live text pending proper shaping/layout support.
- Embedded CJK/Greek/Latin fixture passed read-only byte/hash equality, stale revision rejection and explicit missing-font/base14 fallback. Browser native font loading, Unicode typing, measured width within 1 point of PyMuPDF, cancel cleanup, apply/save and independent PDFium text/render/source-hash checks passed. Frontend build passed; full regression is running. Latest verified installer remains 0.19.0.
- Raw CFF and unembedded base14 fonts still use preview substitutes; CFF/OpenType conversion and Unicode mapping are next work. Exact baseline/wrapping, subset-font ambiguity, larger fonts, shaping/bidi and selected-run formatting remain work. Packaging/native acceptance for this candidate is pending. Full original goal remains active.

- Candidate full source gates passed: 196 Python tests (112.89s), all 27 browser workflows (2.7m), and TypeScript/Vite build. Full browser JSON is preserved at artifacts/ui/full-regression-0.20.0-candidate.json. The TTF-specific browser workflow checks original font registration, source-metric width agreement, Unicode edit/save/independent reopen and face cleanup. Existing direct text, colors, forms, camera/scanner and OCR workflows passed. CFF/base14 conversion, broader metrics/layout and candidate packaging/native gates remain pending. Latest verified installer is 0.19.0; full original goal stays active.

- Reviewed embedded-font browser screenshot. A follow-up reader check found fractional page input could select an invalid array/page index; the page control now accepts integers only. The focused reader/TTF suite passed both checks (13.9s), and the final frontend rebuilt successfully. This follow-up is separate from the earlier full 27-workflow regression. CFF conversion and candidate packaging/native acceptance remain pending; latest verified installer stays 0.19.0.
