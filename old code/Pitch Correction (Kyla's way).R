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
selection <- c("rot_bout", "pitch_initial", "ztime", "label", "light")
circadian <- circadian[, selection]
lighting <- lighting[, selection]

# 自定义函数：在指定范围内进行线性拟合，并在其余区域转换为水平线
fit_line <- function(data, x_col, y_col, lower, upper) {
  data <- data %>% mutate(
    segment = case_when(
      !!sym(x_col) < lower ~ 'left',
      !!sym(x_col) > upper ~ 'right',
      TRUE ~ 'middle'
    )
  )
  
  middle_data <- data %>% filter(segment == 'middle')
  middle_fit <- lm(reformulate(x_col, y_col), data = middle_data)
  
  lower_y <- predict(middle_fit, newdata = setNames(data.frame(lower), x_col))
  upper_y <- predict(middle_fit, newdata = setNames(data.frame(upper), x_col))
  
  middle_data <- middle_data %>% mutate(fit = predict(middle_fit))
  left_data <- data %>% filter(segment == 'left') %>% mutate(fit = lower_y)
  right_data <- data %>% filter(segment == 'right') %>% mutate(fit = upper_y)
  
  result_data <- bind_rows(left_data, middle_data, right_data)
  return(result_data)
}

# 对数据应用自定义函数
dd_day <- fit_line(dd_day, 'pitch_initial', 'rot_bout', -20, 30)
ld_day <- fit_line(ld_day, 'pitch_initial', 'rot_bout', -20, 30)

combine_data <- rbind(dd_day, ld_day)
combined <- fit_line(combine_data, 'pitch_initial', 'rot_bout', -20, 30)

# 创建图表：光照效果
ggplot(dd_day, aes(x = pitch_initial, y = rot_bout, colour = label)) +
  geom_line(aes(y = fit), size = 3, colour = "blue") +
  geom_point(alpha = 0.05) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               label.x = "right", label.y = "top", parse = TRUE) +
  facet_grid(~ztime) +
  xlim(-40,40)+
  ggtitle("Righting rotation (dd_day)")

ggplot(ld_day, aes(x = pitch_initial, y = rot_bout, colour = label)) +
  geom_line(aes(y = fit), size = 3, colour = "blue") +
  geom_point(alpha = 0.05) +
  stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
               label.x = "right", label.y = "top", parse = TRUE) +
  facet_grid(~ztime) +
  xlim(-40,40)+
  ggtitle("Righting rotation (ld_day)")# 

# # 创建图表：昼夜节律效果
# plot_circadian <- ggplot(circadian, aes(x = pitch_initial, y = rot_bout, colour = label)) +
#   geom_line(aes(y = fit), size = 1) +
#   geom_density_2d(aes(color = label)) +
#   stat_poly_eq(aes(label = paste(..adj.rr.label.., ..eq.label.., sep = "~~~")), 
#                label.x = "right", label.y = "top", parse = TRUE) +
#   facet_grid(~light) +
#   ggtitle("Density map for righting gain (Circadian Effect)")
# 
# # 组合图表
# combined_plot <- plot_grid(plot_lighting, plot_circadian, ncol = 1)
# 
# # 显示图表
# print(combined_plot)
