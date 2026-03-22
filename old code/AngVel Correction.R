# 清除工作区
rm(list = ls())

# 设置工作目录
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")

# 加载必要的包
library(dplyr)
library(ggplot2)
library(ggpmisc)
library(ggrepel)
library(cowplot)

# 读取数据并计算 bout_rate
getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())
data <- read.csv("Bout_data_preprocessed_SD_removed.csv")

# Factorize 
data$cond1 <- as.factor(data$cond1)
data$ztime <- as.factor(data$ztime)
data$expNum <- as.factor(data$expNum)
data$light <- as.factor(data$light)

# List of numeric and categorical variables
numeric_col = colnames(data[,sapply(data,is.numeric)])
factor_col = colnames(data[,sapply(data,is.factor)])

# Filter data for specific conditions and time
dd_day <- data[data$label == "dd_day", ]
dd_night <- data[data$labe == "dd_night", ]
ld_day <- data[data$labe == "ld_day", ]
ld_night <- data[data$labe == "ld_night", ]

#
combine_data <- rbind(dd_day, ld_day)

# 创建图表：光照效果
ggplot(combine_data, aes(x = angvel_initial_phase, y = angvel_chg, colour = label)) +
  geom_smooth(method = "lm", formula = y ~ x, se = TRUE, size = 1) +
  geom_density_2d(aes(color = label)) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               formula = y ~ x, label.x = "right", label.y = "top", parse = TRUE) +
  facet_grid(~ztime) +
  xlim(-25, 25) +
  ylim(-25, 25) +
  ggtitle("AngVel Correction (Lighting Effect)")

# 创建图表：昼夜节律效果
plot_circadian <- ggplot(circadian, aes(x = angvel_initial_phase, y = angvel_chg, colour = label)) +
  geom_smooth(method = "lm", formula = y ~ x, se = TRUE, size = 1) +
  geom_density_2d(aes(color = label)) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               formula = y ~ x, label.x = "right", label.y = "top", parse = TRUE) +
  facet_grid(~light) +
  xlim(-25, 25) +
  ylim(-25, 25) +
  ggtitle("Density map for righting gain (Circadian Effect)")

# 组合图表
combined_plot <- plot_grid(plot_lighting, plot_circadian, ncol = 1)

# 显示图表
print(combined_plot)
