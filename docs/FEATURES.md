# Feature status

This is a live implementation tracker, not a parity claim. Evidence is recorded in PROGRESS.md.

| Area | Current implementation | Remaining work |
| --- | --- | --- |
| Reader | Tabs, zoom, page navigation, selectable text, search, bookmarks, themes, page/external links, remembered position/zoom, selected-page print preview | Native print acceptance, viewport/large-file performance |
| Sessions | Immutable revisions, source preservation, undo/redo, persisted recovery | Cleanup policy, close-window unsaved handling; native cancellation/reconnection passed; timeout expiry not yet exercised |
| Page tools | Merge, ranges/extract, reorder/duplicate, delete, rotate, crop, blank page, numbers, text watermark; independent duplicates, visual drag organizer/split groups, precise visual crop/reset/selection and customizable numbers/watermarks verified in 0.9 | Image/diagonal watermarks, broader complex form/bookmark preservation cases |
| Images | Images to PDF, insert image/signature graphic, PNG/JPG page export, embedded image extraction and replace/remove | JPG quality controls, image masks and shared-image compatibility cases |
| Annotation | Quad text highlights, underline/strikeout, rectangles, sticky notes, freehand ink, standard stamps, comment edit/delete | Broader rotated text markup fixtures |
| Forms | Fill fields, create text/checkbox/dropdown/list fields, flatten widgets | Radio groups, direct page interaction, detection, complex field compatibility |
| Existing text | Latin rectangle replacement with overflow checks, visual rotation mapping; image overlaps rejected | Original fonts, block reflow, extended scripts, scan reconstruction |
| Security | AES-256 export, password open/decrypt, rectangular redaction plus auxiliary scrub, incremental certificate signing, personal encrypted identities, public certificate export and offline signature inspection | Broader redaction fixtures, permissions controls, visible certificate appearance, trusted timestamps/revocation assurance |
| Compression/repair | Lossless rewrite, screen/print lossy image presets, readable-PDF recovery | Quality preview, qpdf diagnostics |
| OCR | English offline OCR adds hidden searchable text, preserves visible page pixels | More languages, deskew, mixed-page OCR and scan editing |
| Office export | Editable text DOCX, editable text/image PPTX, image-slide PPTX, detected-table XLSX | Better reconstruction, broader fixtures, LibreOffice validation |
| Office import | Free LibreOffice DOCX/XLSX/PPTX import tested; ODF/RTF/TXT supported by adapter | Broader layout fixtures; configured runtime must remain available |
| Compare/archival | Positional text/pixel comparison with standalone HTML report; static PDF/A-2b export and independent veraPDF validation/XML report | Alignment of inserted/reordered pages; other archival conformance levels, broader layout/color fixtures |
| Markdown | Plain reading-order text export | Structural heading/table/list preservation |
| Workflows/scanner | Saved presets, batch jobs, per-file recovery receipts, failure continuation | Scanner integration |
| Intelligence | Not implemented yet | Free local models, hardware/license evaluation, quality gates |
| Installer | 0.9.0 installer, bundled OCR, Office adapter and native WebView2/edit/link/preview/cancel/batch smoke passed | Installed UI, actual print/scanner acceptance |

No personal files have been used for automated tests. Synthetic fixtures only.
