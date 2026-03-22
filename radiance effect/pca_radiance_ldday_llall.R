options(stringsAsFactors = FALSE)

radiance <- read.csv("Box Radiance.csv", check.names = FALSE)
colnames(radiance) <- c("boxNum", "radiance_mW")
radiance$radiance_mW <- suppressWarnings(as.numeric(radiance$radiance_mW))

df <- read.csv("Analyzed_data/wt_2025_all_Connected_bout_features_strict.csv", check.names = FALSE)
merged <- merge(df, radiance, by = "boxNum", all.x = TRUE)

parameter_candidates <- list(
  c("rot_bout"),
  c("spd_peak"),
  c("displ_swim"),
  c("WHM"),
  c("pre_IBI_time"),
  c("rot_total")
)

params <- c()
for (cand in parameter_candidates) {
  present <- cand[cand %in% colnames(merged)]
  if (length(present) > 0) params <- c(params, present[1])
}

for (p in params) merged[[p]] <- suppressWarnings(as.numeric(merged[[p]]))
merged$cond1 <- as.character(merged$cond1)
merged$ztime <- as.character(merged$ztime)

required_ok <- !is.na(merged$radiance_mW) & !is.na(merged$cond1) & !is.na(merged$ztime)
clean <- merged[required_ok, ]

clean <- clean[
  (tolower(clean$cond1) == "ll" & tolower(clean$ztime) == "day") |
    (tolower(clean$cond1) == "ld" & tolower(clean$ztime) == "day"),
]

if (!("expNum" %in% colnames(clean))) stop("Column 'expNum' is required for grouping.")
group_cols <- c("boxNum", "expNum", "cond1")
agg <- aggregate(
  clean[, c(params, "radiance_mW"), drop = FALSE],
  by = clean[, group_cols, drop = FALSE],
  FUN = function(x) median(x, na.rm = TRUE)
)

run_pca <- function(sub_df, label, params) {
  use_cols <- intersect(params, colnames(sub_df))
  sub_df <- sub_df[, c(use_cols, "radiance_mW"), drop = FALSE]
  sub_df <- sub_df[complete.cases(sub_df), , drop = FALSE]
  n <- nrow(sub_df)
  if (n < 3) return(NULL)
  if (length(unique(sub_df$radiance_mW)) < 2) return(NULL)

  X <- sub_df[, use_cols, drop = FALSE]
  sds <- sapply(X, sd, na.rm = TRUE)
  keep <- names(sds[sds > 0])
  if (length(keep) < 2) return(NULL)
  X <- X[, keep, drop = FALSE]

  pca <- prcomp(X, center = TRUE, scale. = TRUE)
  scores <- as.data.frame(pca$x)
  scores$radiance_mW <- sub_df$radiance_mW
  scores$subset <- label
  evr <- (pca$sdev^2) / sum(pca$sdev^2)

  res <- data.frame(
    subset = character(),
    pc = character(),
    explained_variance_ratio = numeric(),
    pearson_r_with_radiance = numeric(),
    pearson_p = numeric(),
    n = integer()
  )

  pc_cols <- colnames(pca$x)
  for (pc_name in pc_cols) {
    ct <- suppressWarnings(cor.test(scores[[pc_name]], sub_df$radiance_mW, method = "pearson"))
    res <- rbind(
      res,
      data.frame(
        subset = label,
        pc = pc_name,
        explained_variance_ratio = evr[which(colnames(scores) == pc_name)],
        pearson_r_with_radiance = unname(ct$estimate),
        pearson_p = ct$p.value,
        n = n
      )
    )
  }

  loadings <- as.data.frame(pca$rotation)
  loadings$parameter <- rownames(loadings)
  rownames(loadings) <- NULL
  loadings <- loadings[, c("parameter", setdiff(colnames(loadings), "parameter"))]

  list(res = res, loadings = loadings, scores = scores, evr = evr)
}

plot_pc12 <- function(scores_df, evr, label, out_file) {
  if (!all(c("PC1", "PC2", "radiance_mW") %in% colnames(scores_df))) return(invisible(NULL))
  if (nrow(scores_df) < 2) return(invisible(NULL))

  r <- scores_df$radiance_mW
  r_min <- min(r, na.rm = TRUE)
  r_max <- max(r, na.rm = TRUE)
  if (isTRUE(all.equal(r_min, r_max))) {
    cols <- rep("#2c7fb8", length(r))
  } else {
    norm <- (r - r_min) / (r_max - r_min)
    pal <- colorRampPalette(c("#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"))(256)
    idx <- pmax(1, pmin(256, floor(norm * 255) + 1))
    cols <- pal[idx]
  }

  png(filename = out_file, width = 1800, height = 1400, res = 220)
  par(mar = c(5, 5, 4, 4) + 0.1)
  plot(
    scores_df$PC1, scores_df$PC2,
    pch = 19, cex = 1.3, col = cols,
    xlab = sprintf("PC1 (%.1f%%)", 100 * evr[1]),
    ylab = sprintf("PC2 (%.1f%%)", 100 * evr[2]),
    main = paste0("PCA Score Plot: ", label, " (color = radiance)")
  )
  grid(col = "#d9d9d9")

  if (!isTRUE(all.equal(r_min, r_max))) {
    q <- as.numeric(quantile(r, probs = seq(0, 1, length.out = 6), na.rm = TRUE, type = 7))
    mids <- (q[-1] + q[-length(q)]) / 2
    idx_mid <- pmax(1, pmin(256, floor((mids - r_min) / (r_max - r_min) * 255) + 1))
    pal <- colorRampPalette(c("#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"))(256)
    legend_cols <- pal[idx_mid]
    legend_lbl <- sprintf("%.2f - %.2f mW", q[-length(q)], q[-1])
  } else {
    legend_cols <- "#2c7fb8"
    legend_lbl <- sprintf("%.2f mW", r_min)
  }

  legend(
    "topright",
    legend = legend_lbl,
    title = "Radiance",
    pch = 19,
    col = legend_cols,
    pt.cex = 1.2,
    cex = 0.85,
    bty = "n"
  )

  dev.off()
}

plot_pc1_vs_radiance <- function(scores_df, evr, label, out_file) {
  if (!all(c("PC1", "radiance_mW") %in% colnames(scores_df))) return(invisible(NULL))
  if (nrow(scores_df) < 2) return(invisible(NULL))

  png(filename = out_file, width = 1800, height = 1400, res = 220)
  par(mar = c(5, 5, 4, 2) + 0.1)
  plot(
    scores_df$radiance_mW, scores_df$PC1,
    pch = 19, cex = 1.2, col = "#2c7fb8",
    xlab = "Radiance (mW)",
    ylab = sprintf("PC1 (%.1f%%)", 100 * evr[1]),
    main = paste0("PC1 as a Function of Radiance: ", label)
  )
  grid(col = "#d9d9d9")

  if (length(unique(scores_df$radiance_mW)) > 1) {
    fit <- lm(PC1 ~ radiance_mW, data = scores_df)
    abline(fit, col = "#d7191c", lwd = 2)
    ct <- suppressWarnings(cor.test(scores_df$PC1, scores_df$radiance_mW, method = "pearson"))
    txt <- sprintf("r = %.3f, p = %.3g, n = %d", unname(ct$estimate), ct$p.value, nrow(scores_df))
    usr <- par("usr")
    text(usr[1] + 0.02 * (usr[2] - usr[1]), usr[4] - 0.06 * (usr[4] - usr[3]), txt, adj = c(0, 1), cex = 1)
  }

  dev.off()
}

out_res <- list()
out_load <- list()
out_scores <- list()

sub_pool <- agg

rr <- run_pca(sub_pool, "Pooled_LLday_LDday", params)
if (!is.null(rr)) {
  out_res[["Pooled_LLday_LDday"]] <- rr$res
  out_load[["Pooled_LLday_LDday"]] <- rr$loadings
  out_scores[["Pooled_LLday_LDday"]] <- rr
} else {
  cat("Skip pooled subset (insufficient/invalid data)\n")
}

if (length(out_res) == 0) stop("No analyzable subset found")

res_all <- do.call(rbind, out_res)
write.csv(res_all, "Statistics/pca_radiance_correlation_Pooled_LLday_LDday.csv", row.names = FALSE)

for (nm in names(out_load)) {
  write.csv(out_load[[nm]], paste0("Statistics/pca_loadings_", nm, ".csv"), row.names = FALSE)
}

dir.create("Plots_folder/radiance_effect", recursive = TRUE, showWarnings = FALSE)
for (nm in names(out_scores)) {
  out_file <- paste0("Plots_folder/radiance_effect/pca_pc1_pc2_", nm, "_colored_by_radiance.png")
  plot_pc12(out_scores[[nm]]$scores, out_scores[[nm]]$evr, nm, out_file)
  cat("Saved: ", out_file, "\n", sep = "")

  out_file_pc1 <- paste0("Plots_folder/radiance_effect/pca_pc1_vs_radiance_", nm, ".png")
  plot_pc1_vs_radiance(out_scores[[nm]]$scores, out_scores[[nm]]$evr, nm, out_file_pc1)
  cat("Saved: ", out_file_pc1, "\n", sep = "")
}

for (subset_name in unique(res_all$subset)) {
  cat("\n===", subset_name, "===\n")
  ss <- res_all[res_all$subset == subset_name, ]
  ss$abs_r <- abs(ss$pearson_r_with_radiance)
  ss <- ss[order(-ss$abs_r), ]
  print(head(ss[, c("pc", "explained_variance_ratio", "pearson_r_with_radiance", "pearson_p", "n")], 3), row.names = FALSE)
}

cat("\nSaved: Statistics/pca_radiance_correlation_Pooled_LLday_LDday.csv\n")
for (nm in names(out_load)) {
  cat("Saved: ", paste0("Statistics/pca_loadings_", nm, ".csv"), "\n", sep = "")
}
