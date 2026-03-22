getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
library(dplyr)
library(cowplot)
library(ggplot2)
library(stats)

# Input#ggplot2 Input
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

# Combine conditions
combine_data <- rbind(dd_day, ld_day)

# Plot Bout Rate with color coding by label and aligned x-axis
ggplot(combine_data, aes(x = 1/propBoutIEI, color = label)) +
  geom_density(alpha = 0.05) +
  labs(
       x = "Bout Rate (Hz)",
       y = "Density") +
  theme_minimal() 
  #facet_wrap(~ label, scales = "free_x", ncol = 2)

