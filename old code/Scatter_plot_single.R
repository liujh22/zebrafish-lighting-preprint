getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
library(dplyr)
library(ggbiplot)
library(FactoMineR)
library(factoextra)
library(cowplot)
library(ggpmisc)

# Input
data <- read.csv("PCA_Preprocessed.csv")

# Factorize 
data$cond1 <- as.factor(data$cond1)
data$ztime <- as.factor(data$ztime)
data$expNum <- as.factor(data$expNum)
data$light <- as.factor(data$light)

# List of numeric and categorical variables
numeric_col = colnames(data[,sapply(data,is.numeric)])
factor_col = colnames(data[,sapply(data,is.factor)])

# Filter data for y_spd_peak > 0 and y_spd_peak < 0
data_pos <- data[data$pitch_pre_bout > 0, ]
data_neg <- data[data$pitch_pre_bout < 0, ]

# Scatter plot for y_spd_peak > 0

ggplot(data, aes(x = pitch_initial, y = pitch_peak, color = ztime)) +
  geom_point(alpha = 0.04) +
  geom_smooth(method = "lm", se = FALSE) +
  ggtitle("Scatter plot for y_spd_peak > 0") +
  coord_fixed(ratio = 1)

# Scatter plot for y_spd_peak < 0
ggplot(data_neg, aes(x = x_spd_peak, y = y_spd_peak, color = light)) +
  geom_point(alpha = 0.02) +
  geom_smooth(method = "lm", se = FALSE) +
  ggtitle("Scatter plot for y_spd_peak < 0") +
  coord_fixed(ratio = 1)


