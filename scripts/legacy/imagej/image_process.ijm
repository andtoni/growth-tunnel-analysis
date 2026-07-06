// =============================================================================
// Add Scale Bars to Images — Fiji/ImageJ Macro
// =============================================================================
// Author:      Andrea Tonelli (tnland001@myuct.ac.za)
// ORCID:       https://orcid.org/0000-0002-1601-4103
// Institution: University of Cape Town
// Repository:  https://github.com/andtoni/growth-tunnel-analysis
//
// IMPORTANT — Windows path rules for Fiji macros:
//   Use FORWARD SLASHES ( / ) not backslashes ( \ )
//   Paths MUST end with a trailing slash ( / )
//
// Processing order (each step individually toggleable):
//   Step 0 — Detect and remove info/status bars at image edges
//   Step 1 — Normalise brightness and contrast across all images
//   Step 2 — Crop to square (centred, maximum area)
//   Step 3 — Add scale bar
//
// Output filename: image_[infobar]_[norm]_[square]_scalebar.tif
// =============================================================================

// =============================================================================
// USER SETTINGS
// =============================================================================

INPUT_DIR  = "C:/Users/andto/OneDrive/Desktop/University/PhD/DATA/Transmural Space Characterisation/3D Analysis Paper/codeoutput/Full Networks/Before/";
OUTPUT_DIR = "C:/Users/andto/OneDrive/Desktop/University/PhD/DATA/Transmural Space Characterisation/3D Analysis Paper/codeoutput/Full Networks/After/";

// Physical width of the ORIGINAL image in micrometres (um)
IMAGE_WIDTH_UM = 224.92;

// ── Step 0: Info bar detection ────────────────────────────────────────────────

// Enable or disable info bar detection and removal
//   true  — scan edges for status/data bars and crop them out before processing
//   false — skip detection, process full image
DETECT_INFO_BAR = true;

// Which edges to check:
//   "bottom"  — most common for microscopy/CT software info bars (recommended)
//   "all"     — checks bottom, top, left and right edges
INFO_BAR_EDGES = "bottom";

// Sensitivity (0.0 – 1.0):
//   How different must an edge strip's mean intensity be from the image centre
//   to be considered an info bar. Fraction of the full 0-255 intensity range.
//   0.10 — detects subtle bars (light grey on mid-grey image)
//   0.20 — standard setting, catches most software info bars  (recommended)
//   0.35 — only catches very obvious bars (black bar on bright image)
INFO_BAR_SENSITIVITY = 0.20;

// Minimum height/width in pixels to qualify as an info bar.
// Prevents small dark edges within the actual image from being misidentified.
// Recommended: 5-15 px for standard images, 20-40 px for high-resolution exports
INFO_BAR_MIN_PX = 8;

// Gap tolerance: number of "normal-looking" rows/columns allowed within a bar
// before the scan stops. Info bars with white text on a black background can have
// rows that briefly look normal — raising this allows the scan to continue through
// them. Recommended: 3-8. Raise if bars with text are being partially missed.
INFO_BAR_GAP_TOLERANCE = 5;

// Manual force crop — removes a fixed number of pixels from each edge
// regardless of what the auto-detection algorithm finds.
// Set each to 0 to rely on auto-detection only (default).
// Use when auto-detection consistently misses part of a bar, or when the
// info bar is on the top, left, right or a combination of edges.
// All four are applied simultaneously in a single crop operation.
//
//   Examples:
//     Bottom bar only:  INFO_BAR_FORCE_BOTTOM_PX = 60
//     Top bar only:     INFO_BAR_FORCE_TOP_PX    = 40
//     Right sidebar:    INFO_BAR_FORCE_RIGHT_PX  = 80
//     Top + bottom:     INFO_BAR_FORCE_TOP_PX = 40, INFO_BAR_FORCE_BOTTOM_PX = 60
INFO_BAR_FORCE_TOP_PX    = 0;
INFO_BAR_FORCE_BOTTOM_PX = 0;
INFO_BAR_FORCE_LEFT_PX   = 0;
INFO_BAR_FORCE_RIGHT_PX  = 0;

// ── Step 1: Normalisation ─────────────────────────────────────────────────────

NORMALIZE        = false;
NORMALIZE_METHOD = "percentile";  // "percentile" / "global_range" / "mean_std"
LOW_PCT          = 1;
HIGH_PCT         = 99;

// ── Step 2: Square crop ───────────────────────────────────────────────────────

CROP_TO_SQUARE = true;
CROP_ANCHOR    = "center";  // "center" "top" "bottom" "left" "right"

// ── Step 3: Scale bar ─────────────────────────────────────────────────────────

SCALE_BAR_COLOR    = "White";
SCALE_BAR_HEIGHT_PX = 20;
THICKNESS_MODE     = "auto";   // "auto" or "fixed"
FONT_SIZE_PT       = 18;
FONT_MODE          = "auto";   // "auto" or "fixed"

// Auto border around scale bar on bright backgrounds
//   true  — detects local brightness and adds thin black border when needed
//   false — no border, scale bar drawn as-is
AUTO_BORDER       = true;

// Brightness threshold (0-255): corner mean above this triggers the border
// 180 = near-white backgrounds  |  140 = mid-grey backgrounds
BORDER_THRESHOLD  = 180;

// Border thickness in pixels
// Recommended: 2-3 for standard resolution, 4-6 for high-res exports
BORDER_PX         = 2;

// Show or hide the scale bar measurement text label
//   true  — shows the length (e.g. "25 um") next to the bar (default)
//   false — bar only, no text. A separate reference file records the
//            scale bar sizes for each image for use during manuscript writing
SHOW_SCALE_TEXT   = false;

OUTPUT_FORMAT      = "TIFF";   // "PNG" or "TIFF"

STANDARD_SIZES = newArray(1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000, 2000, 5000);

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// ── Compute mean intensity of a single row ────────────────────────────────────
function rowMean(y, w) {
    makeRectangle(0, y, w, 1);
    getRawStatistics(np, m);
    run("Select None");
    return m;
}

// ── Compute mean intensity of a single column ─────────────────────────────────
function colMean(x, h) {
    makeRectangle(x, 0, 1, h);
    getRawStatistics(np, m);
    run("Select None");
    return m;
}

// ── Get mean of the central region (used as image reference) ─────────────────
function centralMean(w, h) {
    margin = 0.2;
    cx = round(w * margin);
    cy = round(h * margin);
    cw = w - 2 * cx;
    ch = h - 2 * cy;
    if (cw < 10) cw = 10;
    if (ch < 10) ch = 10;
    makeRectangle(cx, cy, cw, ch);
    getRawStatistics(np, m);
    run("Select None");
    return m;
}

// ── Detect info bar on one edge, return number of pixels to remove ────────────
// edge:      "bottom" "top" "left" "right"
// c_mean:    reference mean intensity from image centre
// threshold: intensity difference that flags a row/col as info bar
// min_px:    minimum consecutive rows/cols to confirm a bar
function detectEdgeBar(edge, c_mean, threshold, min_px) {
    w = getWidth();
    h = getHeight();
    max_scan = round(minOf(300, h * 0.3));  // scan at most 30% of image or 300px
    if (edge == "left" || edge == "right") {
        max_scan = round(minOf(300, w * 0.3));
    }

    bar_px = 0;

    // Gap tolerance: allows rows/columns with brighter text within a dark bar
    // to be correctly included rather than stopping the scan prematurely
    gap_count     = 0;
    candidate_px  = 0;

    if (edge == "bottom") {
        for (r = h - 1; r >= h - max_scan; r--) {
            m = rowMean(r, w);
            if (abs(m - c_mean) > threshold) {
                candidate_px += gap_count + 1;
                bar_px        = candidate_px;
                gap_count     = 0;
            } else {
                gap_count++;
                if (gap_count > INFO_BAR_GAP_TOLERANCE) break;
            }
        }
    } else if (edge == "top") {
        for (r = 0; r < max_scan; r++) {
            m = rowMean(r, w);
            if (abs(m - c_mean) > threshold) {
                candidate_px += gap_count + 1;
                bar_px        = candidate_px;
                gap_count     = 0;
            } else {
                gap_count++;
                if (gap_count > INFO_BAR_GAP_TOLERANCE) break;
            }
        }
    } else if (edge == "left") {
        for (c = 0; c < max_scan; c++) {
            m = colMean(c, h);
            if (abs(m - c_mean) > threshold) {
                candidate_px += gap_count + 1;
                bar_px        = candidate_px;
                gap_count     = 0;
            } else {
                gap_count++;
                if (gap_count > INFO_BAR_GAP_TOLERANCE) break;
            }
        }
    } else if (edge == "right") {
        for (c = w - 1; c >= w - max_scan; c--) {
            m = colMean(c, h);
            if (abs(m - c_mean) > threshold) {
                candidate_px += gap_count + 1;
                bar_px        = candidate_px;
                gap_count     = 0;
            } else {
                gap_count++;
                if (gap_count > INFO_BAR_GAP_TOLERANCE) break;
            }
        }
    }

    // Return 0 if below minimum size (avoids false positives)
    if (bar_px < min_px) return 0;
    return bar_px;
}

// ── Apply info bar crop to current image ──────────────────────────────────────
// Returns array: [removed_bottom, removed_top, removed_left, removed_right]
function applyInfoBarDetection(sensitivity, edges, min_px) {
    w = getWidth();
    h = getHeight();

    threshold = sensitivity * 255;
    c_mean    = centralMean(w, h);

    removed_bottom = 0;
    removed_top    = 0;
    removed_left   = 0;
    removed_right  = 0;

    if (edges == "bottom" || edges == "all") {
        removed_bottom = detectEdgeBar("bottom", c_mean, threshold, min_px);
    }
    if (edges == "all") {
        removed_top   = detectEdgeBar("top",   c_mean, threshold, min_px);
        removed_left  = detectEdgeBar("left",  c_mean, threshold, min_px);
        removed_right = detectEdgeBar("right", c_mean, threshold, min_px);
    }

    total_removed = removed_bottom + removed_top + removed_left + removed_right;

    if (total_removed > 0) {
        new_x = removed_left;
        new_y = removed_top;
        new_w = w - removed_left - removed_right;
        new_h = h - removed_top  - removed_bottom;

        // Safety check — ensure crop is valid
        if (new_w > 0 && new_h > 0) {
            makeRectangle(new_x, new_y, new_w, new_h);
            run("Crop");
        }
    }

    result = newArray(removed_bottom, removed_top, removed_left, removed_right);
    return result;
}

// ── Percentile from histogram ─────────────────────────────────────────────────
function computePercentile(pct) {
    n_bins = 1000;
    getHistogram(h_values, h_counts, n_bins);
    total = 0;
    for (b = 0; b < h_counts.length; b++) total += h_counts[b];
    threshold = total * pct / 100.0;
    cumulative = 0;
    for (b = 0; b < h_counts.length; b++) {
        cumulative += h_counts[b];
        if (cumulative >= threshold) return h_values[b];
    }
    return h_values[n_bins - 1];
}

// ── Median of array ───────────────────────────────────────────────────────────
function arrayMedian(arr) {
    n = arr.length;
    if (n == 0) return 0;
    if (n == 1) return arr[0];
    sorted = Array.copy(arr);
    for (a = 0; a < n - 1; a++) {
        for (b = a + 1; b < n; b++) {
            if (sorted[b] < sorted[a]) {
                tmp = sorted[a]; sorted[a] = sorted[b]; sorted[b] = tmp;
            }
        }
    }
    mid = floor(n / 2);
    if (n % 2 == 0) return (sorted[mid-1] + sorted[mid]) / 2.0;
    return sorted[mid];
}

// ── Auto-select scale bar length (~15% of physical image width) ───────────────
function selectScaleBarLength(width_um) {
    target = width_um * 0.15;
    best   = STANDARD_SIZES[0];
    diff   = abs(STANDARD_SIZES[0] - target);
    for (s = 1; s < STANDARD_SIZES.length; s++) {
        d = abs(STANDARD_SIZES[s] - target);
        if (d < diff) { diff = d; best = STANDARD_SIZES[s]; }
    }
    return best;
}

// ── Build list of supported image files ───────────────────────────────────────
function getImageFiles(dir) {
    all = getFileList(dir);
    buf = newArray(all.length);
    n   = 0;
    for (k = 0; k < all.length; k++) {
        f       = all[k];
        dot_idx = lastIndexOf(f, ".");
        if (dot_idx < 0) continue;
        ext = toLowerCase(substring(f, dot_idx));
        if (!File.isDirectory(dir + f) &&
            (ext == ".png" || ext == ".tif" || ext == ".tiff" ||
             ext == ".jpg" || ext == ".jpeg" || ext == ".bmp")) {
            buf[n] = f;
            n++;
        }
    }
    return Array.trim(buf, n);
}

// =============================================================================
// INITIALISE
// =============================================================================

if (!File.exists(INPUT_DIR)) {
    exit("ERROR: Input directory not found:\n  " + INPUT_DIR +
         "\nUse forward slashes and end with /");
}
if (!File.exists(OUTPUT_DIR)) {
    File.makeDirectory(OUTPUT_DIR);
    print("Created output directory: " + OUTPUT_DIR);
}

img_files = getImageFiles(INPUT_DIR);
n_images  = img_files.length;

print("=============================================================");
print("Scale Bar Macro  |  Andrea Tonelli, UCT, 2025");
print("=============================================================");
print("Input:            " + INPUT_DIR);
print("Output:           " + OUTPUT_DIR);
print("Images found:     " + n_images);

detect_label = "false";
if (DETECT_INFO_BAR) detect_label = "true  (edges: " + INFO_BAR_EDGES +
    ", sensitivity: " + INFO_BAR_SENSITIVITY + ")";
print("Info bar detect:  " + detect_label);

norm_label = "false";
if (NORMALIZE) norm_label = "true  (" + NORMALIZE_METHOD + ")";
print("Normalise:        " + norm_label);

crop_label = "false";
if (CROP_TO_SQUARE) crop_label = "true  (anchor: " + CROP_ANCHOR + ")";
print("Crop to square:   " + crop_label);

print("Image width:      " + IMAGE_WIDTH_UM + " um (original)");
print("Output format:    " + OUTPUT_FORMAT);
print("=============================================================");

if (n_images == 0) {
    exit("ERROR: No supported images found in:\n  " + INPUT_DIR);
}

// =============================================================================
// PASS 1 — Collect statistics (info bar removal applied first)
// =============================================================================

ref_low  = 0;
ref_high = 255;
ref_mean = 128;
ref_std  = 40;

if (NORMALIZE) {
    pass1_label = "\nPASS 1 — Collecting statistics...";
    if (DETECT_INFO_BAR) pass1_label = "\nPASS 1 — Collecting statistics (info bars removed before sampling)...";
    print(pass1_label);
    all_lows  = newArray(n_images);
    all_highs = newArray(n_images);
    all_means = newArray(n_images);
    all_stds  = newArray(n_images);
    global_min =  1e9;
    global_max = -1e9;

    setBatchMode(true);

    for (i = 0; i < n_images; i++) {
        open(INPUT_DIR + img_files[i]);

        // Remove info bar before sampling so bar pixels do not skew statistics
        if (DETECT_INFO_BAR) {
            applyInfoBarDetection(INFO_BAR_SENSITIVITY, INFO_BAR_EDGES, INFO_BAR_MIN_PX);
        }
        // Force crop all four edges in one operation (Pass 1 — before stats)
        force_any_p1 = INFO_BAR_FORCE_TOP_PX + INFO_BAR_FORCE_BOTTOM_PX +
                       INFO_BAR_FORCE_LEFT_PX + INFO_BAR_FORCE_RIGHT_PX;
        if (force_any_p1 > 0) {
            pw = getWidth(); ph = getHeight();
            fx = INFO_BAR_FORCE_LEFT_PX;
            fy = INFO_BAR_FORCE_TOP_PX;
            fw = pw - INFO_BAR_FORCE_LEFT_PX - INFO_BAR_FORCE_RIGHT_PX;
            fh = ph - INFO_BAR_FORCE_TOP_PX  - INFO_BAR_FORCE_BOTTOM_PX;
            if (fw > 0 && fh > 0) { makeRectangle(fx, fy, fw, fh); run("Crop"); }
        }

        // For RGB colour images, skip the 32-bit conversion — it collapses
        // all three colour channels into a single grayscale image.
        // getHistogram() and getRawStatistics() on RGB return luminance-based
        // statistics (0-255) which are valid reference values for normalisation.
        if (bitDepth() != 24) run("32-bit");

        if (NORMALIZE_METHOD == "percentile") {
            lo = computePercentile(LOW_PCT);
            hi = computePercentile(HIGH_PCT);
            all_lows[i]  = lo;
            all_highs[i] = hi;
            print("  [" + (i+1) + "/" + n_images + "] " + img_files[i] +
                  "  p" + LOW_PCT + "=" + d2s(lo,1) + "  p" + HIGH_PCT + "=" + d2s(hi,1));

        } else if (NORMALIZE_METHOD == "global_range") {
            getRawStatistics(np, m, sd, mn, mx);
            if (mn < global_min) global_min = mn;
            if (mx > global_max) global_max = mx;
            print("  [" + (i+1) + "/" + n_images + "] " + img_files[i] +
                  "  min=" + d2s(mn,1) + "  max=" + d2s(mx,1));

        } else if (NORMALIZE_METHOD == "mean_std") {
            getRawStatistics(np, m, sd, mn, mx);
            all_means[i] = m;
            all_stds[i]  = sd;
            print("  [" + (i+1) + "/" + n_images + "] " + img_files[i] +
                  "  mean=" + d2s(m,1) + "  std=" + d2s(sd,1));
        }

        close("*");
    }

    setBatchMode(false);

    if (NORMALIZE_METHOD == "percentile") {
        ref_low  = arrayMedian(all_lows);
        ref_high = arrayMedian(all_highs);
        print("\n  Reference window: [" + d2s(ref_low,2) + " , " + d2s(ref_high,2) + "]");

    } else if (NORMALIZE_METHOD == "global_range") {
        ref_low  = global_min;
        ref_high = global_max;
        print("\n  Reference window: [" + d2s(ref_low,2) + " , " + d2s(ref_high,2) + "]");

    } else if (NORMALIZE_METHOD == "mean_std") {
        ref_mean = arrayMedian(all_means);
        ref_std  = arrayMedian(all_stds);
        ref_low  = ref_mean - 2.0 * ref_std;
        ref_high = ref_mean + 2.0 * ref_std;
        print("\n  Reference mean: " + d2s(ref_mean,2) +
              "  std: " + d2s(ref_std,2));
        print("  Display window: [" + d2s(ref_low,2) + " , " + d2s(ref_high,2) + "]");
    }

    print("\nPASS 1 complete.");
}

// =============================================================================
// PASS 2 — Process all images
// =============================================================================

print("\nPASS 2 — Processing images...\n");

// Build log as a string — written to disk at the end using File.saveString
// This avoids File.open handle conflicts with setBatchMode(true)
log_path    = OUTPUT_DIR + "scale_bar_reference.txt";
getDateAndTime(yr, mo, dow, dom, hr, mn, sc, ms);
log_content = "Scale Bar Reference Log\n";
log_content = log_content + "Generated:       " + yr + "-" + (mo+1) + "-" + dom + "  " + hr + ":" + mn + "\n";
log_content = log_content + "Input folder:    " + INPUT_DIR + "\n";
log_content = log_content + "Image width:     " + IMAGE_WIDTH_UM + " um (original)\n";
log_content = log_content + "Show text label: " + SHOW_SCALE_TEXT + "\n";
log_content = log_content + "\n";
log_content = log_content + "Filename\tScale bar (um)\tField of view (um)\tBlack background\tOutput file\n";

n_done = 0;
n_skip = 0;

setBatchMode(true);

for (i = 0; i < n_images; i++) {

    filename = img_files[i];
    print("Processing [" + (i+1) + "/" + n_images + "]: " + filename);

    open(INPUT_DIR + filename);

    // Pixel size from original image width — calculated before any cropping
    orig_w    = getWidth();
    px_per_um = orig_w / IMAGE_WIDTH_UM;

    name_suffix = "";

    // ── Step 0: Detect and remove info bar ────────────────────────────────────

    // Auto-detection
    if (DETECT_INFO_BAR) {
        removed = applyInfoBarDetection(
            INFO_BAR_SENSITIVITY, INFO_BAR_EDGES, INFO_BAR_MIN_PX
        );
        r_bottom = removed[0];
        r_top    = removed[1];
        r_left   = removed[2];
        r_right  = removed[3];
        total    = r_bottom + r_top + r_left + r_right;

        if (total > 0) {
            print("  Info bar removed:  bottom=" + r_bottom + "px  top=" + r_top +
                  "px  left=" + r_left + "px  right=" + r_right + "px");
            if (r_left + r_right > 0) {
                px_per_um = getWidth() / IMAGE_WIDTH_UM;
                print("  Note: pixel size recalculated after side bar removal");
            }
            name_suffix = name_suffix + "_infobar";
        } else {
            print("  Info bar:          none detected by auto");
        }
    }

    // Manual force crop — removes fixed pixels from any combination of edges
    // in a single crop operation. Applied after auto-detection.
    force_any = INFO_BAR_FORCE_TOP_PX + INFO_BAR_FORCE_BOTTOM_PX +
                INFO_BAR_FORCE_LEFT_PX + INFO_BAR_FORCE_RIGHT_PX;
    if (force_any > 0) {
        cur_w = getWidth();
        cur_h = getHeight();
        fc_x  = INFO_BAR_FORCE_LEFT_PX;
        fc_y  = INFO_BAR_FORCE_TOP_PX;
        fc_w  = cur_w - INFO_BAR_FORCE_LEFT_PX - INFO_BAR_FORCE_RIGHT_PX;
        fc_h  = cur_h - INFO_BAR_FORCE_TOP_PX  - INFO_BAR_FORCE_BOTTOM_PX;
        if (fc_w > 0 && fc_h > 0) {
            makeRectangle(fc_x, fc_y, fc_w, fc_h);
            run("Crop");
            print("  Force crop:        top=" + INFO_BAR_FORCE_TOP_PX +
                  "px  bottom=" + INFO_BAR_FORCE_BOTTOM_PX +
                  "px  left="   + INFO_BAR_FORCE_LEFT_PX   +
                  "px  right="  + INFO_BAR_FORCE_RIGHT_PX  + "px");
            if (indexOf(name_suffix, "_infobar") < 0) {
                name_suffix = name_suffix + "_infobar";
            }
        }
    }

    // ── Step 1: Normalise ─────────────────────────────────────────────────────
    if (NORMALIZE) {
        is_colour = (bitDepth() == 24);  // 24-bit = RGB Color

        if (is_colour) {
            // ── Colour image (confocal, fluorescence, brightfield RGB) ─────────
            // Preserves all three colour channels by using setMinAndMax + Apply LUT
            // instead of converting to 32-bit (which collapses channels to greyscale).
            // The reference window (ref_low / ref_high) was derived from luminance
            // statistics in Pass 1, which correctly represents overall brightness.
            // Applying the same stretch to all channels maintains colour balance.
            setMinAndMax(ref_low, ref_high);
            run("Apply LUT");
            // Image remains RGB Color — no type conversion needed
            print("  Normalised:        " + NORMALIZE_METHOD + " (colour-safe)");

        } else {
            // ── Grayscale image (SEM, CT, phase-contrast) ─────────────────────
            // Convert to 32-bit for precise floating-point arithmetic,
            // apply linear stretch, then convert back to 8-bit for output.
            run("32-bit");

            if (NORMALIZE_METHOD == "percentile" || NORMALIZE_METHOD == "global_range") {
                run("Subtract...", "value=" + ref_low);
                range = ref_high - ref_low;
                if (range > 0) {
                    run("Multiply...", "value=" + (255.0 / range));
                }
                setMinAndMax(0, 255);

            } else if (NORMALIZE_METHOD == "mean_std") {
                getRawStatistics(np, img_mean, img_std);
                run("Subtract...", "value=" + img_mean);
                if (img_std > 0) {
                    run("Divide...",   "value=" + img_std);
                    run("Multiply...", "value=" + ref_std);
                }
                run("Add...", "value=" + ref_mean);
                setMinAndMax(0, 255);
            }

            run("8-bit");
            print("  Normalised:        " + NORMALIZE_METHOD + " (grayscale)");
        }

        name_suffix = name_suffix + "_norm";
    }

    // ── Step 2: Square crop ───────────────────────────────────────────────────
    if (CROP_TO_SQUARE) {
        img_w = getWidth();
        img_h = getHeight();

        if (img_w != img_h) {
            sq = minOf(img_w, img_h);
            if (img_w > img_h) {
                // Landscape
                if (CROP_ANCHOR == "center") {
                    cx = floor((img_w - sq) / 2); cy = 0;
                } else if (CROP_ANCHOR == "right") {
                    cx = img_w - sq; cy = 0;
                } else {
                    cx = 0; cy = 0;
                }
            } else {
                // Portrait
                if (CROP_ANCHOR == "center") {
                    cx = 0; cy = floor((img_h - sq) / 2);
                } else if (CROP_ANCHOR == "bottom") {
                    cx = 0; cy = img_h - sq;
                } else {
                    cx = 0; cy = 0;
                }
            }
            makeRectangle(cx, cy, sq, sq);
            run("Crop");
            print("  Cropped to:        " + sq + " x " + sq + " px");
        } else {
            print("  Already square");
        }
        name_suffix = name_suffix + "_square";
    }

    // ── Step 3: Scale bar ─────────────────────────────────────────────────────
    final_w            = getWidth();
    final_h            = getHeight();
    effective_width_um = final_w / px_per_um;
    scale_bar_um       = selectScaleBarLength(effective_width_um);

    run("Set Scale...", "distance=" + px_per_um + " known=1 unit=um global");

    if (THICKNESS_MODE == "auto") {
        bar_height = round(final_w * 0.015);
        if (bar_height < 5)  bar_height = 5;
        if (bar_height > 80) bar_height = 80;
    } else {
        bar_height = SCALE_BAR_HEIGHT_PX;
    }

    if (FONT_MODE == "auto") {
        font_size = round(final_w * 0.02);
        if (font_size < 12)  font_size = 12;
        if (font_size > 120) font_size = 120;
    } else {
        font_size = FONT_SIZE_PT;
    }



    // ── Auto-border: use whole image mean to decide if border is needed ───────
    // If the overall image is bright, the white scale bar may be hard to read.
    // When triggered, Fiji's built-in background=Black is used — this always
    // positions the black background perfectly because Fiji calculates both
    // the bar and its background together. No manual pixel calculation needed.
    need_border = false;
    if (AUTO_BORDER) {
        run("Select None");
        getRawStatistics(np_img, img_mean_whole);
        if (img_mean_whole > BORDER_THRESHOLD) {
            need_border = true;
            print("  Image mean:        " + d2s(img_mean_whole, 0) +
                  " > " + BORDER_THRESHOLD + " — black background added to scale bar");
        } else {
            print("  Image mean:        " + d2s(img_mean_whole, 0) +
                  " (< " + BORDER_THRESHOLD + ") — no background needed");
        }
    }

    // ── Add scale bar overlay ─────────────────────────────────────────────────
    // SHOW_SCALE_TEXT controls whether the measurement label is shown.
    // Both "bold" and "label" are omitted when hiding text — "bold" alone can
    // trigger text rendering in some Fiji versions even without "label".
    // font is also set to 0 when hiding as a belt-and-braces measure.
    if (SHOW_SCALE_TEXT) {
        text_opts = " bold label";
        font_opt  = font_size;
    } else {
        text_opts = "";
        font_opt  = 0;
    }

    if (need_border) {
        run("Scale Bar...",
            "width="   + scale_bar_um +
            " height=" + bar_height   +
            " font="   + font_opt     +
            " color=White"            +
            " background=Black"       +
            " location=[Lower Right]" +
            text_opts + " overlay");
    } else {
        run("Scale Bar...",
            "width="   + scale_bar_um    +
            " height=" + bar_height      +
            " font="   + font_opt        +
            " color="  + SCALE_BAR_COLOR +
            " background=None"           +
            " location=[Lower Right]"    +
            text_opts + " overlay");
    }

    run("Flatten");
    name_suffix = name_suffix + "_scalebar";
    border_note = "";
    if (need_border) border_note = "  [black background]";
    print("  Scale bar:         " + scale_bar_um + " um  |  " +
          d2s(effective_width_um, 2) + " um field of view" + border_note);



    // ── Save ──────────────────────────────────────────────────────────────────
    name_only = substring(filename, 0, lastIndexOf(filename, "."));
    if (OUTPUT_FORMAT == "TIFF") {
        saveAs("Tiff", OUTPUT_DIR + name_only + name_suffix + ".tif");
    } else {
        saveAs("PNG",  OUTPUT_DIR + name_only + name_suffix + ".png");
    }

    // Append entry to log string
    out_filename  = name_only + name_suffix + "." + toLowerCase(OUTPUT_FORMAT);
    border_logged = "No";
    if (need_border) border_logged = "Yes";
    log_content = log_content +
        filename + "\t" +
        scale_bar_um + "\t" +
        d2s(effective_width_um, 2) + "\t" +
        border_logged + "\t" +
        out_filename + "\n";

    close("*");
    print("  Saved:             " + name_only + name_suffix +
          "." + toLowerCase(OUTPUT_FORMAT));
    print("");
    n_done++;
}

setBatchMode(false);

// Save log string to disk in one call — reliable in all Fiji modes
File.saveString(log_content, log_path);

print("=============================================================");
print("COMPLETE");
print("  Images processed: " + n_done);
print("  Skipped:          " + n_skip);
print("  Scale bar log:    " + log_path);
if (NORMALIZE) {
    print("  Display window:   [" + d2s(ref_low,2) + " , " + d2s(ref_high,2) + "]");
}
print("  Output folder:    " + OUTPUT_DIR);
print("=============================================================");
