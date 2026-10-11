# Personal PDF Editor and Reader - Development Plan

Prepared: 11 October 2026

Revised: 11 October 2026 - free-only requirement confirmed by the user.

Status: Planning only. No application code, dependency installation, or implementation has been started.

## 1. Recommendation

Build a Windows desktop application that combines a comfortable PDF reader, an editor, and a toolbox for individual files and batches. Use mature PDF engines behind your own interface. Keep normal document processing on your computer, with no account, subscription infrastructure, or server to operate.

The recommended starting architecture is **Tauri 2 + React/TypeScript + PDF.js + a packaged Python PDF worker**. Use PyMuPDF for core PDF operations, then add specialist engines only where they are needed. This gives you a flexible interface and access to established document-processing libraries without writing a PDF parser yourself.

**Free is a hard requirement:** zero required software-license fees, subscriptions, paid APIs, or paid document engines. Use freely usable local components under their applicable licenses. Do not depend on trials, expiring free tiers, or software the user would need to purchase.

Evaluate existing-text editing and PDF-to-Office conversion before committing to the final engine. Implement difficult features with open-source libraries and custom code, documenting unsupported cases. If a feature cannot meet its acceptance criteria with free components, keep it explicitly limited or pending further development. Personal use reduces product and deployment overhead; it does not remove the technical difficulty of PDF editing.

The target is one coherent application with broad functionality. Full compatibility with every PDF and exact Adobe/iLovePDF output quality are goals to evaluate, not promises this plan can make.

## 2. Working assumptions

- Windows 11, 64-bit, is the initial target; confirm the actual Windows version and hardware in Phase 0.
- One user, local files, no collaboration or public distribution.
- Core functions work offline after installation; dependency downloads are setup activities.
- All required components must be free to use for this private local application. Paid engines, paid APIs, subscriptions, and trial-dependent features are excluded.
- Use a clean desktop interface, light/dark themes, keyboard shortcuts, and remembered reading position.
- Preserve original files by default and make every destructive operation reviewable.
- Deliver an installer containing the application and its core worker. Optional free LibreOffice, OCR, and archival components can be installed or detected separately. Microsoft Office is not required.

The free-only requirement is fixed. Other assumptions can change during implementation without changing the overall goal. Hardware information has not been provided yet.

## 3. What “editing a PDF” must mean

Treat these as distinct capabilities in the UI and feature tracker:

| Capability | What the user receives | Implementation implication |
| --- | --- | --- |
| Annotate | Highlights, comments, pen marks, and stamps | Standard PDF annotations that remain editable where supported |
| Add content | New text, images, and shapes | New PDF page content or annotations, depending on the tool |
| Fill forms | Values in existing interactive fields | Update field values and visible appearances together |
| Edit existing content | Change original text or images | Requires content analysis, font handling, and controlled replacement |
| Edit a scan | Change words visible in a scanned image | OCR plus image/content reconstruction; adding an OCR layer alone is insufficient |
| Reflow paragraphs | Longer replacement text wraps and shifts appropriately | Evaluate custom block reconstruction with free engines; support tested layouts first |

The iLovePDF editor describes adding text, images, shapes, and freehand annotations. Acrobat also documents modifying existing text. Both belong in the scope, with separate acceptance criteria. [iLovePDF editor](https://www.ilovepdf.com/edit-pdf), [Adobe text editing](https://helpx.adobe.com/acrobat/desktop/edit-documents/edit-text-in-pdfs/modify-text.html)

Do not present a white rectangle over old text as text replacement or secure redaction. Do not label an image pasted into a PowerPoint slide as a fully editable conversion.

## 4. Technology choices

### Recommended components

| Component | Role | When to add it |
| --- | --- | --- |
| Tauri 2 | Desktop window, native dialogs, controlled file access, worker lifecycle, installer | Foundation |
| React + TypeScript + Vite | Tabs, tool panels, command palette, page organizer, jobs | Foundation |
| PDF.js | Page display, text selection, search, links, viewer layers | Reader |
| Python + PyMuPDF | Page operations, content insertion, annotations, fields, extraction, redaction | Foundation |
| qpdf | Structural checks, encryption, rewriting, recovery attempts, structural optimization | Utilities |
| Tesseract + OCRmyPDF | Persistent OCR text layers and scan processing | OCR |
| LibreOffice adapter | DOCX/XLSX/PPTX to PDF | Conversion |
| python-docx / python-pptx / openpyxl | Generate editable Office output from extracted content and custom reconstruction | Conversion; these are output writers, not complete conversion engines |
| pyHanko | Certificate signing and signature validation | Advanced signatures |
| veraPDF | Independent validation of PDF/A outputs | Archival export |
| Small local JSON files | Preferences, recents, workflow definitions, job summaries | Foundation |

PDF.js provides display and viewer layers suitable for building a customized reader. PyMuPDF provides core manipulation APIs; it is not a ready-made Acrobat editing UI. [PDF.js architecture](https://mozilla.github.io/pdf.js/getting_started/), [PyMuPDF feature comparison](https://pymupdf.readthedocs.io/en/latest/about.html)

Tauri explicitly supports external binaries, including packaged Python workers. The worker must be packaged for the target architecture rather than relying on Python being installed on the user's computer. [Tauri sidecars](https://v2.tauri.app/develop/sidecar/)

Use one main PDF manipulation engine initially. Do not add pypdf, pikepdf, pdf-lib, PDFium, and Ghostscript simply because each can perform some overlapping functions. Add a dependency when a measured capability gap requires it.

### Alternatives and when they make sense

| Approach | Strength | Tradeoff | Decision |
| --- | --- | --- | --- |
| Tauri + React + Python | Flexible UI, mature web reader, strong Python tooling | Three language ecosystems and worker packaging | Recommended for this feature-rich custom app |
| Python + PySide6 | Fewer implementation languages; fast document-tool development | A polished custom reader/editor still needs substantial UI work | Good alternative if simplest development is the priority |
| C# + WPF/WinUI | Strong Windows integration and native desktop controls | Need suitable document engine bindings or a worker | Prefer if C# is your maintenance preference |
| Electron + React | Familiar desktop web stack and Chromium behavior | Bundled browser runtime and larger deployment footprint | Consider if WebView2 proves unsuitable in the prototype |

These are engineering judgments, not measured comparisons on your computer. The initial prototype should validate the recommended stack before a large UI investment.

Select engines only from components usable at no charge under their licenses. Evaluate alternatives on the same fixtures and prefer one main engine plus focused adapters. Paid SDK evaluation is outside this plan.

### Licensing for this personal project

Use the AGPL edition of PyMuPDF/MuPDF for this private local application. Keep license notices and source/dependency records. Reassess the obligations if you later distribute the app or expose it to other users over a network; do not assume process separation removes license obligations. The paid licensing route is excluded. [PyMuPDF licensing](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright), [GNU license FAQ](https://www.gnu.org/licenses/gpl-faq.en.html)

LibreOffice is available under open-source licenses. The Office-output writers are also freely usable under their license terms. Confirm the licenses of the exact shipped versions and their transitive dependencies during Phase 0. [LibreOffice licenses](https://www.libreoffice.org/licenses/), [python-docx license](https://github.com/python-openxml/python-docx/blob/master/LICENSE), [python-pptx license](https://github.com/scanny/python-pptx/blob/master/LICENSE), [openpyxl documentation](https://openpyxl.readthedocs.io/en/stable/)

## 5. Application architecture

```text
Desktop interface: React + PDF.js
                |
       typed document commands
                |
Tauri: file access, sessions, job supervision
                |
        local stdio IPC protocol
                |
Python PDF worker: PyMuPDF and tool adapters
                |
Private working files -> validated PDF -> chosen output
```

### Keep the document state coherent

- Opening a document creates a session ID and a private working copy. Record a source fingerprint and the current revision.
- The worker owns the canonical PDF revision. PDF.js renders that same revision through a scoped local asset mechanism.
- Frontend tools send semantic operations, such as moving an annotation or changing a field value. The worker applies and saves them.
- Use a customized viewer; route form and annotation interactions through the application state. Avoid two independent save pipelines using PDF.js and Python.
- Include document ID, revision ID, job ID, parameters, and structured errors in commands. Reject edits against stale revisions.
- Use streamed progress messages for long jobs. Exchange large documents through authorized files, not repeated base64 payloads.
- Never pass arbitrary user strings into a shell. Launch approved executables with structured argument arrays.

### Undo, redo, and saving

Use an operation history for ordinary edits and checkpoints for transforms that are difficult to reverse, such as OCR, compression, and conversion. Undo/redo applies to the working session. Applying redactions produces a separate finalized output; recoverable pre-redaction history must never be embedded in it.

Write to a temporary output on the destination volume, validate it, close file handles, then replace or rename into place. Handle disk-full, permission, cloud-sync, and file-lock failures explicitly. Save As is the initial default; replacing an original requires an explicit overwrite action and a recoverable backup. Check whether another application changed the source before overwriting it.

### Coordinate mapping

Define a canonical page-coordinate model. Explicitly transform between PDF coordinates, PyMuPDF page coordinates, PDF.js viewports, and screen pixels. Test crop boxes, page origins, rotation, user units, zoom, and Windows display scaling. This is essential for correctly placing highlights, fields, text, and redaction rectangles.

### Jobs and performance

Run heavy tasks outside the UI process. Start with one writer per document and a bounded number of read-only jobs. PyMuPDF documents must not be shared across concurrent threads; use separate processes for parallel work. [PyMuPDF multiprocessing guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html)

Render visible pages and a small nearby range. Bound thumbnail and page caches; cancel obsolete render requests. Support job cancellation, timeouts, worker restarts, and per-file batch results. Cancellation must leave the original file intact.

## 6. Feature coverage

The inventory below maps the current iLovePDF tool categories and adds the reader/editor functions expected from an Acrobat-like app. It includes newer forms and intelligence tools so they are not silently omitted. Phase numbers refer to the roadmap below. [iLovePDF tool inventory](https://www.ilovepdf.com/), [iLovePDF tool documentation](https://www.ilovepdf.com/help/documentation)

| Feature | Planned approach | Phase / qualification |
| --- | --- | --- |
| Read PDFs | Tabs, zoom, fit modes, thumbnails, search, select/copy, bookmarks, links, print | 1 |
| Merge | Ordered file/page selection | 2; reconcile form names and document structures |
| Split | Ranges, every N pages, individual pages | 2 |
| Organize | Reorder, duplicate, insert, replace, remove, extract pages | 2 |
| Rotate | Single page, selection, or document | 2 |
| Crop | Adjustable crop boxes and preview | 2; hidden content can remain outside crop |
| Page numbers | Position, format, range, start number | 2 |
| Watermark | Text/image, opacity, placement, page range | 2 |
| JPG/images to PDF | JPG/PNG imports, orientation, margins, page size | 2 |
| PDF to JPG/images | Render pages with DPI/quality controls | 2 |
| Extract images | Export embedded images separately | 2 |
| Annotate | Highlight, underline, strikeout, comments, ink, shapes, stamps | 3 |
| Add text/images | Place, resize, style, align | 3 |
| PDF forms | Fill existing AcroForms, create/edit fields, optional flattening | 3; automatic detection in 7 |
| Sign yourself | Draw/type/import a visible signature | 3; distinct from certificate signing |
| Protect | Password-based encryption and permission settings | 4 |
| Unlock | Decrypt a file using the supplied required credentials | 4; no password-recovery feature planned |
| Redact | Mark, preview, apply, sanitize, verify final output | 4 |
| Compress | Lossless optimization and separate lossy image presets | 4 |
| Repair | Diagnostic checks and recovery attempts with a report | 4; cannot recreate missing content |
| OCR | Searchable/selectable saved PDFs, languages, deskew, page range | 4 |
| Edit existing text | Bounded replacement with font/layout checks | 5; feasibility gate in 0 |
| Edit existing images | Selected image replacement/move/delete | 5; shared resources need careful handling |
| Edit scanned text | OCR-assisted reconstruction and preview | 5; advanced, fidelity limits |
| Word to PDF | Local LibreOffice export | 6; no Microsoft Office requirement |
| PowerPoint to PDF | Local presentation export | 6 |
| Excel to PDF | Sheets, print area, page orientation and scaling | 6 |
| HTML to PDF | Optional local browser print adapter | 6; URL input explicitly uses the network |
| PDF to Word | Evaluate pdf2docx and custom extraction/reconstruction with python-docx | 6; editable output and layout scored separately |
| PDF to PowerPoint | Custom reconstruction with python-pptx; image-slide mode separate | 6; editable reconstruction limited to tested layouts |
| PDF to Excel | Table detection, region preview, editable cells using openpyxl | 6; OCR and complex tables require review |
| PDF to PDF/A | Conversion adapter plus independent validation | 6; start with one selected profile |
| Compare PDFs | Side-by-side pages, text and rendered-image differences | 6; normalize and align pages |
| PDF to Markdown | Local structured extraction, reviewed reading order | 6 |
| Scan to PDF | Image import first, Windows WIA/TWAIN scanner adapter later | 7; test actual scanner |
| Workflows | Saved local sequences with batch queue and output templates | 7 |
| Certificate signing | Local certificate/private-key integration and verification | 7; self-signed or already-held certificates, no purchased certificate required |
| Request signatures | Export a prepared PDF, manually share it, and track the returned file locally | 8; hosted signing-service automation is outside the free local baseline |
| AI summarizer | Optional freely usable local model with page references | 8; license and hardware/model evaluation required; no paid API |
| Translate PDF | Freely usable local translation model plus new document layout | 8; exact layout preservation is a separate hard problem |

“All functions” means every requested tool gets a tracked implementation or a clearly identified dependency/feasibility outcome. It does not mean claiming complete parity while replacing difficult functions with lookalike outputs. Full acceptance requires resolving the conditional rows above.

Cloud storage integrations, mobile capture, and automated signature-request delivery are service capabilities. The personal desktop equivalents are local files, scanner/image import, and manual sharing of prepared PDFs. Exact hosted equivalents are outside the free local baseline. Keep those choices explicit in the feature tracker.

## 7. Important engineering boundaries

### Genuine text and image editing

PDF text may be individually positioned glyphs using subset fonts, with little paragraph structure. A small replacement and a rewritten paragraph need different algorithms.

Start with supported horizontal text blocks. Detect the font, available glyphs, text direction, bounds, and surrounding content. Provide a preview, enforce overflow checks, and disclose font substitution. For a narrowly supported replacement, remove the original content and insert the replacement; prove that underlying text is gone and neighboring graphics remain intact. Never apply broad redactions as a generic editing algorithm.

Test longer replacements, embedded fonts, rotated text, tables, ligatures, Arabic/CJK content, and shared image objects early. Unsupported cases should offer conversion/source-document editing through free tools or remain explicitly unsupported until custom reconstruction is implemented. Changing invisible OCR text does not change the words visible in the scan. [PyMuPDF page editing and redaction APIs](https://pymupdf.readthedocs.io/en/latest/page.html)

### Forms

Support standard AcroForms first. Preserve field names, types, flags, values, and appearance streams. Test both reopened field data and rendering in another reader. Resolve duplicate field names during merges and handle shared field parents. Mark dynamic XFA, document scripts, and complex calculations as compatibility cases; do not silently flatten them.

### OCR

Begin with English; add Malay or other languages after confirming actual needs. Assess scan quality and process image-only pages selectively.

PyMuPDF can provide OCR text for searching and can generate searchable PDFs from images. An in-memory OCR TextPage is not automatically a persistent document change. OCRmyPDF is preferable for a production pipeline that preserves existing document content where possible. Its current installation guide includes native 64-bit Windows instructions; WSL and Docker are alternatives, not baseline requirements. [PyMuPDF OCR](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html), [OCRmyPDF Windows installation](https://ocrmypdf.readthedocs.io/en/latest/installation.html)

### Compression

Offer a lossless preset and explicitly labeled lossy presets with size/quality previews. Preserve searchable text and vector content where possible. qpdf can optimize streams and some images but does not resample images, so it cannot provide every image-downsampling preset alone. Do not claim a guaranteed percentage reduction. [qpdf optimization limits](https://qpdf.readthedocs.io/en/stable/cli.html#optimizing-file-size)

### Secure redaction

Applying redaction must remove targeted text, relevant image pixels, and graphics as appropriate. Include hidden text layers, annotations, attachments, and metadata in the sanitization review. Export a fully rewritten, cleaned file, not an incremental revision retaining previous sensitive objects. Keep original/session recovery outside the exported document.

Verify by extraction/search, object/attachment inspection, and visual inspection in an independent engine. Cropping, flattening annotations, or painting a black box does not prove removal. Publish this function as supported only for the tested content classes. [Adobe redaction and sanitization](https://helpx.adobe.com/in/acrobat/desktop/protect-documents/redact-pdfs/redacting-sanitizing.html)

### Conversions

Office-to-PDF and PDF-to-Office are different problems. LibreOffice supports headless conversion for the first direction. Font availability, page breaks, spreadsheet print settings, and embedded objects still need representative tests. [LibreOffice conversion parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html)

For PDF-to-Word, evaluate pdf2docx only as a limited candidate: Artifex announced in March 2026 that it is no longer actively maintaining the project and that it was relicensed under MIT. If adopted, pin a tested revision and own maintenance; do not make universal Word export depend on it without evaluation. Compare it with custom PyMuPDF extraction and python-docx reconstruction on the same fixtures. [Artifex project status](https://github.com/ArtifexSoftware/pdf2docx/discussions/374)

For PDF-to-PowerPoint, reconstruct supported text and image blocks with python-pptx; provide a separately labeled image-slide export for appearance preservation. For PDF-to-Excel, extract tables with the main PDF engine and write editable cells using openpyxl. The writers create Office files; reading order, layout reconstruction, and table interpretation remain our implementation work. Validate outputs in LibreOffice so testing also has no Microsoft Office requirement.

Score visual resemblance, editable structure, reading order, and table accuracy independently. Image-only export can be useful, but it must have a different label from editable export.

### Signatures and archival files

A drawn signature is a visible mark. A digital signature uses cryptography and certificates. Show cryptographic integrity, document modifications, certificate trust, and revocation evidence separately. An offline result may lack current revocation evidence; display unknown status accurately. Sign finalized bytes and avoid later rewrite/compression steps that invalidate the signature. [pyHanko validation](https://pyhanko.readthedocs.io/en/latest/cli-guide/validation.html)

Use a locally generated self-signed certificate or one the user already holds. Self-signed certificates are not automatically trusted by other readers; do not claim universally trusted identity verification. Purchased certificates, paid timestamp services, and paid signing providers are not dependencies of this app.

Detect signed PDFs on open. Ordinary editing should operate on a separate copy with an explicit signature-status change. Support allowed incremental updates only through a tested signature-aware workflow.

A PDF/A metadata flag is not compliance. Select a profile, evaluate conversion dependencies such as OCRmyPDF/Ghostscript, then require a passing independent validation report before claiming that profile. PDF/A conversion is not automatic accessibility remediation. [veraPDF validation](https://docs.verapdf.org/validation/)

## 8. User experience

Use one main window with document tabs. The reader stays central while tools change around it.

| Area | Intended behavior |
| --- | --- |
| Home | Open file, recent documents, favorite tools, recent jobs |
| Left panel | Thumbnails, bookmarks, search results, attachments |
| Center | PDF reading/editing canvas with stable selection and zoom |
| Top toolbar | Read, Annotate, Edit, Pages, Convert, Protect |
| Right panel | Contextual tool settings and properties |
| Bottom area | Page/zoom status and collapsible background jobs |
| Tools view | Searchable tool catalog and batch drop zone |

Typical utility flow: **Choose files -> choose settings -> preview -> save output.** Defaults should remember useful preferences, and technical diagnostics should remain behind a details panel.

Keep selection mode explicit: text selection, hand/pan, annotation, content edit, and redaction marking. Support Ctrl+O, Ctrl+S, Ctrl+Shift+S, Ctrl+F, Ctrl+Z, and Ctrl+Y. Show unsaved changes per tab and offer recovery after a crash.

Begin with built-in view modes, not PDF recoloring. Dark application chrome should not alter exported pages. Use accessible labels, visible focus, keyboard operation, scalable text, and adequate contrast.

## 9. Development roadmap

Estimates below are planning ranges for one developer working steadily, with mature libraries and ordinary test files. They are not measured delivery commitments. Conditional engine work can extend them substantially.

| Phase | Deliverable | Exit gate | Rough effort |
| --- | --- | --- | --- |
| 0 - Feasibility | Small viewer/worker/installer experiment and engine decision | Real file open, operation, save, independent reopen; text-edit and conversion comparison | 3-7 working days |
| 1 - Reader foundation | Tabs, navigation, selection/search, print, sessions, safe saving/recovery | Comfortable reading and reliable saved/recovered files | 1-2 weeks |
| 2 - Page and image tools | Merge/split/organize, crop/rotate, numbers/watermarks, image import/export | Content and essential structures preserved on fixtures | 1-2 weeks |
| 3 - Everyday editor | Annotations, added text/images, AcroForms, visible signatures, undo/redo | Interactive results reopen correctly in another reader | 2-3 weeks |
| 4 - Document utilities | OCR, compression, protect/unlock, repair, redaction | Persistent OCR, corruption-free outputs, verified removal | 2-4 weeks |
| 5 - Content editor | Existing text/images and supported scan editing | Original content changed without collateral damage; limits documented | 3-6+ weeks |
| 6 - Conversion and comparison | Office conversions, table export, HTML, Markdown, compare, PDF/A | Results pass format-specific quality checks | 3-6+ weeks |
| 7 - Personal workflow release | Scanner, workflow presets, certificate signing, form detection, installer refinement | Native end-to-end acceptance on your machine | 2-3 weeks |
| 8 - Extended functions | Free local summarization/translation and manual signature-request preparation | Separate quality, hardware, model-license, and workflow acceptance | Estimate after feasibility |

### Phase 0 must answer the expensive questions first

1. Confirm Windows architecture, RAM, typical document sizes, freely usable fonts, LibreOffice availability, and scanner needs.
2. Build a small Tauri/PDF.js shell and package a Python worker; test file paths containing spaces and Unicode.
3. Open a form, a long PDF, and a scan. Place an annotation on rotated/cropped pages and reopen the output independently.
4. Test small original-text replacement, a longer paragraph, and shared-image replacement. Record supported cases and failures.
5. Compare free engine approaches on difficult text and PDF-to-Office examples, including pdf2docx versus custom reconstruction.
6. Prove installer launch, worker restart, and operation without internet or a developer Python installation.
7. Record the selected stack, licenses, dependency versions, results, and explicit limitations in a decision receipt. Confirm that every required dependency works without a purchase, subscription, paid API, or expiring trial.

If full paragraph editing fails, evaluate another free approach or plan further custom layout work. Mark the unsupported cases clearly and revise estimates; do not substitute a paid engine. The rest of the app should talk to a document-engine interface so free engine changes do not require a UI rewrite.

### First useful version

Finish Phases 1-3 first: reader, page tools, image conversion, annotations, added content, forms, and visible signatures. Use it on your own ordinary files before expanding. This is roughly 4-7 weeks after feasibility under the assumptions above.

Phases 4-7 take the app toward a broad personal toolkit. The table suggests roughly 4-8 months of focused development for a broad release covering supported cases. Custom editing/reconstruction and compatibility work can increase that substantially under the free-only constraint. Local intelligence and manual signature-request workflows are additional work. Exact full Acrobat parity is not a sensible fixed-date commitment for a solo project.

Release a tested installer at each useful milestone. Capture the completed scope, failed cases, test results, and next tasks in a short handover file.

## 10. Verification and acceptance

### Representative fixture set

Start with approximately 25-40 legally available or synthetic PDFs covering:

- Normal text, subset/embedded fonts, multi-column layouts, tables, and large images.
- Scans, mixed scanned/text pages, low-resolution pages, and chosen OCR languages.
- Rotated pages, differing crop boxes, large page dimensions, and unusual coordinates.
- AcroForms, duplicate field names, annotations, links, bookmarks, layers, and attachments.
- Encrypted, signed, mildly malformed, and unrecoverable documents.
- A 500-page file, a 200 MB image-heavy file, and Unicode/long file paths.

Keep originals immutable. Each feature records input hashes, expected results, output artifacts, and failures. Use personal documents for local acceptance only; do not accidentally commit them into a repository.

### Meaningful checks

| Feature | Evidence required |
| --- | --- |
| Reader | Visual correctness, selection/search, zoom/rotation, native print output |
| Page operations | Expected page order/count, render comparison, required structures preserved |
| Forms | Field values and appearances agree after reopening; flattening removes widgets when chosen |
| OCR | Text is searchable after app restart and in another reader; scan appearance acceptable |
| Existing-text edits | Replacement appears, old text removed, adjacent content unaffected, fonts/layout checked |
| Redaction | Hidden/visible target content removed, clean rewritten export, independent inspection |
| Compression | Size and image quality recorded; non-target content preserved |
| Encryption | Correct/wrong password behavior and successful independent reopening |
| Digital signature | Integrity/trust/revocation results separated; subsequent edit behavior tested |
| Conversion | Open in target application; check editing, layout, tables, and page breaks |
| PDF/A | Passing report for the exact claimed profile |
| Recovery | Forced crash, job cancellation, locked file, disk failure, and original-file preservation |
| Installer | Normal Windows launch, worker availability, optional dependency detection, offline operation |

Automated tests should cover engine operations and document-state transitions. UI tests should cover the critical open/edit/save/reopen flows. Use a second engine, such as a PDFium-based reader or Acrobat Reader, for independent visual review rather than checking every result only with its producing engine.

Proposed performance goals, to benchmark on your hardware: first page within approximately two seconds for an ordinary small document; visible feedback within 100 ms for normal UI actions; responsive cancellation for long jobs; bounded memory while navigating a large document. These are targets, not current results.

Browser fixtures, successful builds, and library-level tests do not establish native acceptance. Manually verify Windows dialogs, display scaling, printing, scanner access, crash recovery, and installer behavior on your machine.

## 11. Privacy, maintenance, and packaging

- Local processing is the default. Bundle viewer assets and fonts required by the app; do not load them from a CDN.
- Disable embedded PDF JavaScript and automatic execution of attachments or launch actions. Restrict external navigation and desktop command capabilities. [Tauri capabilities](https://v2.tauri.app/security/capabilities/)
- Keep the Python worker in a separate process with resource/time limits. Process separation improves fault isolation but is not an operating-system sandbox.
- Put working files in per-session directories with user-scoped access. Offer cache/history clearing; clean abandoned sessions on startup. File deletion is not a guarantee of forensic erasure from SSDs or backups.
- Keep passwords, document text, and signing secrets out of logs and command lines. Use Windows-backed secret storage for any credentials added later.
- Retain only minimal diagnostic metadata by default. Make crash reports and document samples local and opt-in.
- Pin tested dependency versions and keep a license inventory. Update PDF parsers deliberately and rerun the fixture suite after upgrades.
- Use PyInstaller or an equivalent packager after the Phase 0 packaging test. Verify native libraries, OCR language data, worker version matching, and shutdown behavior.
- Plan for WebView2 availability in the Windows installer. Tauri documents multiple deployment strategies; choose one that matches your offline-install needs. [Tauri Windows installer](https://v2.tauri.app/distribute/windows-installer/)
- Keep optional components discoverable through a simple settings page showing availability and required setup.
- Avoid installing WSL, Docker, a database server, or a virtual printer driver as baseline requirements.

Summarization and translation use local models with licenses permitting free personal use, subject to hardware and output-quality evaluation. Do not build paid API, hosted signing, or cloud-processing dependencies into the app. Manual sharing of an exported PDF is a separate user action.

## 12. Free-only policy and scope decisions

The application must require **zero software-license, subscription, and API charges** to install and use its supported functions on the user's existing Windows computer. This covers the PDF engine, OCR, conversion tools, viewer, packaging, and any local model added later. Hardware, electricity, storage, and development time still exist; no new purchase is assumed by this plan.

Dependency selection must meet all of these conditions:

- Free use is permitted by the exact version's license, including bundled dependencies and model weights.
- Normal operation needs no payment, credit card, metered API, expiring trial, or paid activation.
- Office conversion and validation work through LibreOffice; Microsoft Office is not required.
- A personal installer can be built and used without purchasing a code-signing certificate.
- Features that exceed the free engine's abilities receive explicit support limits and further development tasks.

If these conditions fail, choose another free component or defer the affected capability. Do not introduce paid fallbacks.

The most useful early decisions are:

1. Is modest original-text editing sufficient, or is full paragraph reflow a must-have?
2. Must PDF-to-Word/Excel/PowerPoint closely preserve layout and editability?
3. Which difficult editing/conversion cases should receive custom development first?
4. Which languages, scanner, and typical document sizes matter most?

These are decisions for the feasibility milestone, not reasons to delay this plan. Proceed with Windows, local processing, and the free-only baseline. The budget constraint has already been answered and must not be reopened as a routine engine-selection question.

## 13. Proposed project organization

```text
PDF Project/
  PERSONAL_PDF_APP_PLAN.md
  docs/                 engine decisions, feature tracker, handovers
  app/                  React/TypeScript interface
  src-tauri/            desktop host and job supervisor
  worker/               Python engine and specialist adapters
  tests/                synthetic/public fixtures and assertions
  scripts/              reproducible packaging and verification
  artifacts/            local test outputs and release receipts
```

This layout is proposed; these application directories have not been created. Keep build outputs, caches, secrets, and personal PDF fixtures excluded from version control.

## 14. First implementation brief

When implementation is requested, start with Phase 0 only:

> Use PERSONAL_PDF_APP_PLAN.md as the planning baseline. Free is a hard requirement: use only components that permit free private local use, with no paid engines, paid APIs, subscriptions, purchases, or expiring trials. Build an isolated Windows feasibility prototype with Tauri, React, PDF.js, and a packaged local Python/PyMuPDF worker under its AGPL license. Prove file opening, coordinate mapping, one page operation, one annotation, safe saving, and independent reopening. Evaluate genuine existing-text editing and free PDF-to-Office reconstruction before selecting the final engine. Use LibreOffice for Office conversion/validation. Record exact versions, licensing, packaging results, supported cases, and failures. Produce a decision receipt and a native prototype installer. Keep originals unchanged and do not claim full Acrobat or iLovePDF parity from build success. Document difficult features as limited or pending custom development instead of proposing a paid fallback.

The final engine choice follows that evidence. The interface, reader, and tool catalog then grow around a tested document pipeline.
