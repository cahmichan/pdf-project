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
