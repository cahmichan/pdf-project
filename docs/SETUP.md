# Personal Windows setup

The core app installer needs Windows x64 and the free Microsoft Edge WebView2 runtime. It includes its PDF worker and English OCR model. Node, Rust, Python and Microsoft Office are not required to run the installed core app.

Latest verified installer milestone: `artifacts/releases/0.10.0/Folio_0.10.0_x64-setup.exe`. This build includes offline OCR, comparison, image tools, configured free Office import, reader links, print preview, ink/stamps, certificate signing/inspection, native worker cancellation saved batch workflows and configured archival conversion.

## Free Office runtime

Run from the project folder with the development Python environment:

```powershell
.\.venv\Scripts\python.exe scripts/setup_office.py
```

This downloads the official LibreOffice 26.8.1 Windows MSI, checks the pinned official SHA256, and extracts its files under `tools/LibreOffice` with the MIT-licensed lessmsi utility. It does not register LibreOffice as a Windows application. The runtime path is recorded in Folio's app-data `settings.json`. Keep this project folder available after configuring it. The core installer does not embed the large LibreOffice runtime.

The setup downloads about 358 MB and needs more disk space for extraction. Downloads and extraction receipts stay within this project. Conversion uses a disposable LibreOffice profile with macro execution disabled, preserves the original Office document, and opens a converted PDF working copy for review. Linked external document content is rejected. Fonts, print areas and pagination can differ from Microsoft Office.

## Manual acceptance when you return

Install the latest verified installer and open synthetic PDFs first. Check native Open/Save dialogs, overwrite prompts, closing with changes, high-DPI displays, keyboard navigation and representative PDFs you use. Review redacted output in another viewer and confirm that search/copy does not reveal the removed content. Review OCR spelling and Office export/import layout.

Printing and scanner hardware acceptance remain pending. No printer/scanner operation has been silently performed.

## Recovery files

Folio retains private revision copies and OCR text under its Tauri app-data directory, normally `%APPDATA%\personal.folio.pdf`. Encrypted PDFs are decrypted into private working copies after a correct password. Original documents are kept unchanged. Closing a document tab does not erase its recovery session.

## Personal certificates

Under Protect, choose Sign with certificate. Use a local PKCS#12 .pfx/.p12 identity or create an encrypted self-signed personal identity. Save a separate signed PDF and reopen it to inspect signed bytes, cryptographic validity and trust separately. The initial certificate signature is invisible; a signature graphic can be placed before signing.

Export the public certificate when you need an explicit trust certificate. It contains no private key. Folio does not change Windows trust stores. Keep the private identity file and its password safe; Folio clears passwords after each operation and does not remember them. Offline inspection does not establish current revocation status or a trusted signing time. Self-signed certificates are not automatically trusted in other readers.

## Free archival runtime

Run `.\.venv\Scripts\python.exe scripts/setup_archival.py` from the project folder. This downloads verified Ghostscript, a project-local free Temurin JRE, 7-Zip and veraPDF. It extracts files under tools, verifies veraPDF's detached publisher signature with Git's GPG, and records runtime paths in Folio's settings. It does not register an application, change system PATH, or require Oracle Java. Keep the configured project folder available; the large tools are separate from the core installer.

Under Convert, Archival PDF/A-2b exports the whole document as a separate static copy, then requires an independent veraPDF pass. Forms/annotations are flattened and links/attachments are removed. Review text, colors and layout. Check PDF/A-2b inspects the current working copy and can save the full XML report. Other PDF/A conformance levels are not implemented.

## Organize and split pages

Open a PDF, select Pages, and choose Organize pages visually. Drag thumbnails or use Move left/right, Duplicate selected, and Remove selected. Cancel discards staged changes. Apply page order makes one undoable working revision; save a separate copy when ready. Copied form fields receive unique names, and copied internal links target the first retained copy of their destination.

For multiple output files, select Split into separate PDFs and Choose split method. Choose one file per page, a fixed page count per file, or custom groups such as `1-3;4-6;7,9`. Select an output folder and save. Each output gets a unique filename; the working document does not change. A JSON receipt records completed or failed files. Interrupted receipts also appear in Batch tools under Recent batch jobs. Keep completed outputs if a job is interrupted; rerunning creates new files.

## Precise crop, page numbers and text watermarks

In Pages, select Crop margins. Trim each visible edge independently in points, millimeters or inches; these margins follow the displayed rotation and apply to the chosen page range. Draw a rectangle keeps that area on the current page only. Reset to full page restores the MediaBox for the chosen range. A size readout previews the current page. Undo reverses the last operation. Cropping hides content rather than removing it.

Page numbers supports a starting number and a format such as `Page {n} of {total}`. `{n}` is the sequence starting at your chosen value, `{total}` is the count of selected pages, `{page}` is the original working-document page number, and `{pages}` is the document page count. Numbering follows the ordered page range; repeated page numbers are used only once. Choose top/middle/bottom, left/center/right, font size, color, opacity and spacing. Text watermarks share the placement and opacity controls. Both currently use a single line of Latin text with standard Helvetica. Save a separate copy and review placement.

## Fill forms directly on the page

Choose Forms, then Fill existing fields. Supported text, multiline, checkbox, dropdown and single-select list fields become editable on the page, including on rotated/cropped pages. The sidebar and page controls share values. Read-only fields are disabled and text length limits apply. Values remain staged while navigating pages/tabs; Apply saves edits from visited pages as one working revision. Save a copy applies staged values before exporting. Working changes preserve the original.

Unapplied drafts are held in memory, so apply/save before exiting. Closing a tab or undoing with pending values shows a warning. Signature fields use certificate signing; complex radio/multi-select fields and scripted calculations require further compatibility work. Review output in another viewer before using a completed form.
