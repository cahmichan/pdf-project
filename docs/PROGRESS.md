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
