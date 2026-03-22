library(dplyr)
library(ggplot2)
library(ggpmisc)
library(cowplot)

# 读取数据并计算 bout_rate
getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())
data <- read.csv("IBI_data_preprocessed_SD_removed.csv")

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


# Calculate bout rate & (theta - p)
calculate_deviation_bout_rate <- function(df) {
  df %>%
    mutate(deviation_from_preferred_pitch = propBoutIEI_pitch_median - median(propBoutIEI_pitch_median),
           bout_rate = 1 / propBoutIEI)
}

dd_day <- calculate_deviation_bout_rate(dd_day)
ld_day <- calculate_deviation_bout_rate(ld_day)
combine_data <-rbind(dd_day, ld_day)

# Plot DD_day
ggplot(dd_day, aes(x = deviation_from_preferred_pitch, y = 1/propBoutIEI)) +
  geom_point(alpha = 0.02) +
  geom_smooth(method = "lm", formula = y ~ poly(x, 2), se = FALSE, color = "blue") + # Fits a quadratic function
  ggtitle("Pitch Sensitivity (DD_day)") +
  stat_poly_eq(aes(label = ..rr.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ poly(x, 2), parse = TRUE, vjust = 2) +
  stat_poly_eq(aes(label = ..eq.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ poly(x, 2), parse = TRUE) +
  ylab("Bout Rate") +
  xlab("Deviation from preferred Pitch") +
  xlim(-30, 30) +
  theme_minimal()

# Plot LD_day
ggplot(ld_day, aes(x = deviation_from_preferred_pitch, y = 1/propBoutIEI)) +
  geom_point(alpha = 0.02) +
  geom_smooth(method = "lm", formula = y ~ poly(x, 2), se = FALSE, color = "blue") + # Fits a quadratic function
  ggtitle("Pitch Sensitivity (LD_day)") +
  stat_poly_eq(aes(label = ..rr.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ poly(x, 2), parse = TRUE, vjust = 2) +
  stat_poly_eq(aes(label = ..eq.label..),
               label.x.npc = "right", label.y.npc = "top",
               formula = y ~ poly(x, 2), parse = TRUE) +
  ylab("Bout Rate") +
  xlab("Deviation from preferred Pitch") +
  xlim(-30, 30) +
  theme_minimal()

