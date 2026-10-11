# Folio implementation handover

Objective remains active: finish the personal, free Windows PDF editor/reader following `PERSONAL_PDF_APP_PLAN.md`. The user authorized autonomous implementation while away, free project-scoped tooling, tests and a local installer. Never buy, publish, upload personal documents or silently replace originals. This is implementation work, beyond the plan's original planning-only first brief.

## Current baseline

Tauri 2 desktop host, React/TypeScript interface, local PDF.js 6 viewer resources, PyMuPDF 1.28.2 canonical session engine packaged with PyInstaller. English Tesseract fast data is bundled for persistent offline OCR. All document mutations create validated immutable revisions with undo/redo. Normal PDF save copies exact working bytes. Secure redaction rewrites and sanitizes auxiliary content. Source documents remain intact.

`artifacts/releases/0.6.0` contains the latest fully verified installer and SHA256 receipt. Version 0.6.0 includes offline certificate signing/inspection, ink/stamps, saved presets/batch jobs, signature rewrite checks, Office import, reader links/position/print preview and improved rotated editing; package and actual native WebView2 verification passed. Refer to the latest PROGRESS.md and receipts before choosing a build.

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

Finish the current candidate's native/installer checks, preserve the installer receipt, and make a local source checkpoint. Continue meaningful independent work from FEATURES.md: advanced text/image/layout fidelity, form detection/radio groups, annotation ink/stamps, structural Markdown/HTML, archival conversion with independent validation, visible certificate appearances and scanner integration. Evaluate optional local models only with free components and useful quality evidence.

Never describe unsupported conversion/layout cases as Acrobat parity. OCR spelling, complex layouts, original-font reuse and semantic comparison need separate evidence. Printing, scanner hardware, native dialogs/installer UI and unusual real PDFs require explicit manual acceptance when the user returns. Maintain PROGRESS.md, FEATURES.md and setup instructions as implementation progresses. Do not mark the full goal complete just because a build passes.
