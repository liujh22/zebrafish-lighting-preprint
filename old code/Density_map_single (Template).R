getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
library(dplyr)
library(cowplot)
library(ggplot2)
library(stats)
library(ggpmisc)

# Input#ggplot2 Input
data <- read.csv("Bout_data_WT_preprocessed_SD_removed.csv")
data <- read.csv("Bout_data_fin_preprocessed_SD_removed.csv")
data <- read.csv("IBI_data_WT_preprocessed_SD_removed.csv")
data <- read.csv("IBI_data_fin_preprocessed_SD_removed.csv")

# Factorize 
data$cond1 <- as.factor(data$cond1)
data$ztime <- as.factor(data$ztime)
data$cond0 <- as.factor(data$cond0)
data$expNum <- as.factor(data$expNum)

# List of numeric and categorical variables
numeric_col = colnames(data[,sapply(data,is.numeric)])
factor_col = colnames(data[,sapply(data,is.factor)])

# Filter data for specific conditions and time
# Fin Dataset
dd_day <- data[data$cond0 == "DD"&data$ztime == "day", ]
ld_day <- data[data$cond0 == "LD"&data$ztime == "day", ]
dd_night <- data[data$cond0 == "DD"&data$ztime == "night", ]
ld_night <- data[data$cond0 == "LD"&data$ztime == "night", ]

# WT dataset
dd_day <- data[data$cond1 == "dd"&data$ztime == "day", ]
ld_day <- data[data$cond1 == "ld"&data$ztime == "day", ]
dd_night <- data[data$cond1 == "dd"&data$ztime == "night", ]
ld_night <- data[data$cond1 == "ld"&data$ztime == "night", ]
ll_day <- data[data$cond1 == "ll"&data$ztime == "day", ]
ll_night <- data[data$cond1 == "ll"&data$ztime == "night", ]

# Create a custom gradient with blue, green, yellow, and red
color_gradient <- scale_color_gradientn(colors = c("blue", "green", "yellow", "red"))

# Create the first plot for data_dd during the day with the custom color gradient
p1 <- ggplot(dd_day, aes(y = propBoutIEI_pitch_median-median(propBoutIEI_pitch_median), x = propBoutIEI_angVel)) +
  #geom_point(alpha = 0.4) +
  geom_bin_2d()+
  ggtitle("DD_day") 


#############################
# Empirical IEI Pitch #
#########################
combine_data <- rbind(dd_day, dd_night)  # 2 most different conditions
######

ggplot(combine_data, aes(x = traj_deviation-atk_ang, colour = cond1)) +
  geom_density() +
  #xlab("") +
  ylab("Density") +
  facet_wrap(~ztime) +
  theme_minimal()


ggplot(combine_data, aes(x = traj_post_bout-pitch_post_bout, colour = cond1)) +
  geom_density() +
  xlab("Defence Angle (traj_post_bout-pitch_post_bout)") +
  ylab("Density") +
  facet_wrap(~cond0) +
  theme_minimal()

# 绘制重叠密度图
ggplot(combine_data, aes(y = propBoutIEI_angAcc , x = propBoutIEI_spd,color = label)) +
  #geom_density2d() +
  geom_point(alpha = 0.01) +
  stat_smooth(method = "lm", se = FALSE) +
  stat_poly_eq(aes(label = ..eq.label..), 
               label.x.npc = "right", label.y.npc = "top", 
               formula = y ~ x, parse = TRUE) +
  stat_poly_eq(aes(label = ..rr.label..), 
               label.x.npc = "right", label.y.npc = "top", 
               formula = y ~ x, parse = TRUE, vjust = 1.5)+
  labs(title = "Density Plot",
       x = "speed",
       y = "angAcc") +
  theme_minimal() 
    #xlim(-100,100)+
  #scale_fill_discrete(name = "Condition")



# 拟合正态分布
model <- nls(pre_IBI_time ~ a * exp(-((traj_pre_bout - b)^2 / (2 * c^2))), 
             data = dd_day, 
             start = list(a = 1, b = mean(dd_day$traj_pre_bout), c = sd(dd_day$traj_pre_bout)))

# 生成拟合的值
dd_day$fit <- predict(model, newdata = dd_day)

# 绘图
ggplot(dd_day, aes(y = pre_IBI_time, x = traj_pre_bout, color = label)) +
  geom_point(alpha = 0.08) +
  geom_line(aes(y = fit), color = "blue")  # 绘制拟合曲线

# 残差计算
dd_day$residuals <- dd_day$pre_IBI_time - dd_day$fit

# 绘制残差图
ggplot(dd_day, aes(x = traj_pre_bout, y = residuals, color = label)) +
  geom_point(alpha = 0.5) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "red") +
  labs(title = "Residual Plot")

# 拟合正态分布
model <- nls(pre_IBI_time ~ a * exp(-((traj_pre_bout - b)^2 / (2 * c^2))), 
             data = ld_day, 
             start = list(a = 1, b = mean(ld_day$traj_pre_bout), c = sd(ld_day$traj_pre_bout)))

# 生成拟合的值
ld_day$fit <- predict(model, newdata = ld_day)

# 绘图
ggplot(ld_day, aes(y = pre_IBI_time, x = traj_pre_bout, color = label)) +
  geom_point(alpha = 0.08) +
  geom_line(aes(y = fit), color = "blue") +  # 绘制拟合曲线
  stat_poly_eq(aes(label = paste(..eq.label.., ..adj.rr.label.., sep = "~~~")), 
               parse = TRUE)


# Load necessary libraries
library(ggplot2)
library(ggpubr)

# Initialize a list of your datasets
datasets <- list(ld_day = ld_day, dd_day = dd_day, ld_night = ld_night, dd_night = dd_night)

#########
combine_data <- rbind(dd_day, ld_day)
combine_data <- combine_data[, c("atk_ang", "label","expNum", "traj_peak")]
combine_data$climb <- combine_data$traj_peak >= 20
combine_data <- combine_data %>%
  filter(climb == TRUE) %>% 
  group_by(expNum, label) %>%
  summarize(median_atk_ang = mean(atk_ang), .groups = "drop")


# Ensure 'label' is a factor with 'ld_night' on the left and 'dd_night' on the right
combine_data$label <- factor(combine_data$label, levels = c("dd_day", "ld_day"))

# Plotting
ggplot(combine_data, aes(x = label, y = median_atk_ang, group = expNum)) +
  geom_point(aes(color = label), size = 3) +  # Points colored by label
  geom_line(color = "gray", size = 1) +       # Gray lines connecting points within each expNum
  labs(y = "Attack angle (deg)")+             # y-axis label
  ylim(-20,30)


# 使用 dplyr 来计算中位数，并根据 label 分类
median_table <- data %>%
  group_by(label) %>%
  summarize(median_lift = median(lift_distance))

median_table

