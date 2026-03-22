# 加载必要的包
library(dplyr)
library(ggplot2)
library(ggrepel)
library(cowplot)
rm(list=ls())

# 读取数据并计算 bout_rate
getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())
data <- read.csv("IBI_data_preprocessed_SD_removed.csv")
data<-data %>% mutate(bout_rate = 1 / propBoutIEI_Dur)


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

# Plot DD_day
# Calculate the median
median_value <- median(dd_day$propBoutIEI_angVel, na.rm = TRUE)

# Create a new column to separate the data into two segments
dd_day <- dd_day %>%
  mutate(segment = ifelse(propBoutIEI_angVel < median_value, "Below Median", "Above Median"))

# Plot with segmented regression lines
ggplot(dd_day, aes(x = propBoutIEI_angVel, y = 1/propBoutIEI, color = segment)) +
  geom_point(alpha = 0.02) +
  geom_smooth(method = "lm", se = FALSE) + # Fits separate linear models for each segment
  scale_color_manual(values = c("Below Median" = "red", "Above Median" = "blue")) + # Customize colors
  ggtitle("AngVel Sensitivity (DD_day)") +
  stat_poly_eq(aes(label = ..rr.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ x, parse = TRUE, vjust = 1.5)+
  stat_poly_eq(aes(label = ..eq.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ x, parse = TRUE) +
  ylab("Bout Rate")+
  xlab("AngVel") +
  xlim(-20, 20)
  theme_minimal()

  
# Plot LD_day
median_value <- median(ld_day$propBoutIEI_angVel, na.rm = TRUE)

# Create a new column to separate the data into two segments
ld_day <- ld_day %>%
  mutate(segment = ifelse(propBoutIEI_angVel < median_value, "Below Median", "Above Median"))

# Plot with segmented regression lines
ggplot(ld_day, aes(x = propBoutIEI_angVel, y = 1/propBoutIEI, color = segment)) +
  geom_point(alpha = 0.02) +
  geom_smooth(method = "lm", se = FALSE) + # Fits separate linear models for each segment
  scale_color_manual(values = c("Below Median" = "red", "Above Median" = "blue")) + # Customize colors
  ggtitle("AngVel Sensitivity (LD_day)") +
  stat_poly_eq(aes(label = ..rr.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ x, parse = TRUE, vjust = 1.5)+
  stat_poly_eq(aes(label = ..eq.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ x, parse = TRUE) +
  ylab("Bout Rate")+
  xlab("AngVel") +
  xlim(-20, 20)
  theme_minimal()
  