# 导入必要的库
library(ggplot2)
library(dplyr)
library(cowplot)
library(ggpmisc)

# 读取数据
rm(list=ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
lighting <- read.csv("bout_lighting.csv")
circadian <- read.csv("bout_circadian.csv") 

# 选择特定的列
selection <- c("rot_early_accel", "pitch_initial", "ztime", "label", "light","rot_late_accel")
circadian <- circadian[, selection]
lighting <- lighting[, selection]

# 创建图表：光照效果
plot_lighting <- ggplot(lighting, aes(x = pitch_initial, y = rot_l_accel, colour = label)) +
  geom_smooth(method = "lm", formula = y ~ x, se = TRUE, size = 1) +
  geom_density_2d(aes(color = label)) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               label.x = "right", label.y = "top", parse = TRUE) +
  facet_grid(~ztime) +
  ggtitle("Density map for steering gain (Lighting Effect)")

# 创建图表：昼夜节律效果
plot_circadian <- ggplot(circadian, aes(x = pitch_initial, y = rot_l_accel, colour = label)) +
  geom_smooth(method = "lm", formula = y ~ x, se = TRUE, size = 1) +
  geom_density_2d(aes(color = label)) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               label.x = "right", label.y = "top", parse = TRUE) +
  facet_grid(~light) +
  ggtitle("Density map for steering gain (Circadian Effect)")

# 组合图表
combined_plot <- plot_grid(plot_lighting, plot_circadian, ncol = 1)

# 显示图表
print(combined_plot)
