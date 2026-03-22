# 导入必要的库
library(ggplot2)
library(dplyr)
library(cowplot)
library(ggpmisc)

# 读取数据
rm(list=ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
data <- read.csv("Bout_data_preprocessed_SD_removed.csv")

# Filter data for specific labels
lighting_labels <- c("dd_day", "ld_day", "ld_night", "ll_night")
lighting <- data[data$label %in% lighting_labels, ]
circadian_labels <- c("ll_day", "ll_night", "dd_day", "dd_night")
circadian <- data[data$label %in% circadian_labels, ]

# 选择特定的列
selection <- c("pitch_peak", "pitch_initial", "ztime", "label", "light")
circadian <- circadian[, selection]
lighting <- lighting[, selection]


combine_data <- rbind(dd_day, ld_day)
# 创建图表：光照效果
ggplot(combine_data, aes(x = pitch_initial, y = pitch_peak, colour = label)) +
  geom_density_2d() +
  geom_smooth(method = "lm", se = TRUE, size = 1) +
  facet_grid(~ztime) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               label.x = "right", label.y = "top", parse = TRUE) +
  ggtitle("Linear fit for pitch peak vs. pitch initial (Lighting Effect)")

# 创建图表：昼夜节律效果
plot_circadian <- ggplot(circadian, aes(x = pitch_initial, y = pitch_peak, colour = label)) +
  geom_density2d() +
  geom_smooth(method = "lm", se = TRUE, size = 1) +
  facet_grid(~light) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               label.x = "right", label.y = "top", parse = TRUE) +
  ggtitle("Linear fit for pitch peak vs. pitch initial (Circadian Effect)")

# 组合图表
combined_plot <- plot_grid(plot_lighting, plot_circadian, ncol = 1)

# 显示图表
print(combined_plot)
