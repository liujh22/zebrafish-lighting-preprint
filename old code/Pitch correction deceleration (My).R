# 导入必要的库
library(ggplot2)
library(dplyr)
library(cowplot)
library(ggpmisc)

# 读取数据
rm(list = ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
data <- read.csv("Bout_data_preprocessed_SD_removed.csv")

# 过滤特定标签的数据
lighting_labels <- c("dd_day", "ld_day", "ld_night", "ll_night")
lighting <- data[data$label %in% lighting_labels, ]
circadian_labels <- c("ll_day", "ll_night", "dd_day", "dd_night")
circadian <- data[data$label %in% circadian_labels, ]

# 选择特定的列
selection <- c("rot_full_decel", "pitch_initial", "ztime", "label", "light")
circadian <- circadian[, selection]
lighting <- lighting[, selection]

# 自定义函数：拟合Sigmoid函数并计算R²
fit_sigmoid <- function(df, x_col, y_col) {
  y <- df[[y_col]]
  x <- df[[x_col]]
  model <- nls(
    y ~ (Asym / (1 + exp((xmid - x) / scal))) + c,
    start = list(Asym = max(y, na.rm = TRUE), xmid = mean(x, na.rm = TRUE), scal = -1, c = min(y, na.rm = TRUE)),
    data = df,
    control = nls.control(maxiter = 100, warnOnly = TRUE)
  )
  y_pred <- predict(model)
  ss_total <- sum((y - mean(y))^2)
  ss_res <- sum((y - y_pred)^2)
  r_squared <- 1 - (ss_res / ss_total)
  list(model = model, r_squared = r_squared)
}

# 自定义函数：绘制图表
plot_sigmoid <- function(data, x_col, y_col, group_col, title) {
  data_fits <- data %>%
    group_by(!!sym(group_col)) %>%
    do({
      fit <- tryCatch(fit_sigmoid(., x_col, y_col), error = function(e) NULL)
      if (!is.null(fit)) {
        x_predict <- seq(min(.[[x_col]], na.rm = TRUE), max(.[[x_col]], na.rm = TRUE), length.out = 100)
        y_predict <- predict(fit$model, newdata = data.frame(x = x_predict))
        r_squared <- fit$r_squared
        data.frame(x = x_predict, y = y_predict, r_squared = r_squared, label = unique(.$label))
      } else {
        data.frame(x = numeric(0), y = numeric(0), r_squared = NA, label = unique(.$label))
      }
    }) %>%
    ungroup()
  
  ggplot(data, aes_string(x = x_col, y = y_col, colour = group_col)) +
    geom_point(alpha = 0.1) +
    geom_line(data = data_fits, aes(x = x, y = y), col = "blue", size = 1) +
    ggtitle(title) +
    geom_text(data = data_fits %>% group_by(label) %>% summarise(r_squared = mean(r_squared, na.rm = TRUE)),
              aes(x = Inf, y = Inf, label = paste("R² =", round(r_squared, 2))),
              hjust = 1.1, vjust = 1.1, size = 3, color = "black")
}

# 过滤和处理数据，去除缺失值
lighting <- lighting %>% filter(!is.na(rot_full_decel) & !is.na(pitch_initial))
circadian <- circadian %>% filter(!is.na(rot_full_decel) & !is.na(pitch_initial))

# 分别绘制光照效果的Sigmoid曲线
plots_lighting <- lighting %>%
  split(.$label) %>%
  lapply(function(df) plot_sigmoid(df, 'pitch_initial', 'rot_full_decel', 'label', paste('Sigmoid fit for pitch_initial vs. rot_full_decel (Lighting Effect -', unique(df$label), ')')))

# 分别绘制昼夜节律效果的Sigmoid曲线
plots_circadian <- circadian %>%
  split(.$label) %>%
  lapply(function(df) plot_sigmoid(df, 'pitch_initial', 'rot_full_decel', 'label', paste('Sigmoid fit for pitch_initial vs. rot_full_decel (Circadian Effect -', unique(df$label), ')')))

# 组合图表
combined_plot <- plot_grid(plotlist = c(plots_lighting, plots_circadian), ncol = 2)

# 显示图表
print(combined_plot)
