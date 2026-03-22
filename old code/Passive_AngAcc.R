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
data <- read.csv("IBI_data_preprocessed_SD_removed.csv")
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

combine_data <- rbind(dd_day, ld_day)

# 绘制原始重叠密度图
ggplot(combine_data, aes(x = propBoutIEI_angAcc,color = label)) +
  geom_density() +
  xlim(-30, 30)+
    labs(title = "Density Plot for Angular Acceleration",
       x = "Passive AngAcc",
       y = "Density") +
  theme_minimal() 

# AngAcc ~ Speed
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
  labs(
       x = "propBoutIEI_spd",
       y = "PropBoutIEI_angAcc") +
  theme_minimal() 

# AngAcc ~ IEI
ggplot(combine_data, aes(y = propBoutIEI_angAcc , x = propBoutIEI,color = label)) +
  #geom_density2d() +
  geom_point(alpha = 0.01) +
  labs(
       x = "propBoutIEI",
       y = "PropBoutIEI_angAcc") +
  theme_minimal() 

# Add filter, speed <=1, IEI >= 2
# Calculate mean and SD for each group
summary_stats <- combine_data %>%
  filter(propBoutIEI >= 2, propBoutIEI_spd <= 1) %>%
  group_by(label) %>%
  summarise(
    mean_value = mean(propBoutIEI_angAcc, na.rm = TRUE),
    sd_value = sd(propBoutIEI_angAcc, na.rm = TRUE)
  )

# Create text labels with mean and SD values
summary_stats <- summary_stats %>%
  mutate(label_text = paste0(label, ": Mean = ", round(mean_value, 2), ", SD = ", round(sd_value, 2)))

# Plot with density and add the text box
ggplot(filter(combine_data, propBoutIEI >= 2, propBoutIEI_spd <= 1), aes(x = propBoutIEI_angAcc, color = label )) +
  geom_density(alpha = 0.5) +
  labs(title = "Density Plot AngAcc (IEI >= 2, spd <= 1) ",
       x = "Passive AngAcc",
       y = "Density") +
  xlim(-30, 30) +
  theme_minimal() +
  # Add mean lines
  geom_vline(data = summary_stats, aes(xintercept = mean_value, color = label), linetype = "dashed") +
  # Add a text box in the top right corner with mean and SD values
  annotate("text", x = Inf, y = Inf, label = paste(summary_stats$label_text, collapse = "\n"), 
           hjust = 1.1, vjust = 2, size = 4, color = "black", fontface = "bold", 
           box.padding = unit(0.5, "lines"), 
           parse = FALSE) +
  theme(plot.margin = margin(5, 15, 5, 5, "pt"))
