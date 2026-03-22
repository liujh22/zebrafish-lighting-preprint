getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
library(dplyr)
library(cowplot)
library(ggplot2)
library(stats)
library(ggpmisc)
library(gridExtra)

# Input#ggplot2 Input
data <- read.csv("IBI_data_WT_preprocessed_SD_removed.csv")

# Filter data for specific conditions and time
dd_day <- data[data$ztime == "day"&data$cond1 == "dd", ]
dd_night <- data[data$ztime == "night"&data$cond1 == "dd", ]
ld_day <- data[data$ztime == "day"&data$cond1 == "ld", ]
ld_night <- data[data$ztime == "night"&data$cond1 == "ld",  ]

# List of datasets
datasets <- list(dd_day = dd_day, ld_day = ld_day)
datasets <- list(dd_day = dd_day, dd_night = dd_night)

# Initialize a list to store the plots
plots <- list()

# Loop through each dataset
for (name in names(datasets)) {
  # Extract the dataset
  dataset <- datasets[[name]]
  
  # Subset the data before binning
  filtered_dataset <- dataset %>%
    filter(propBoutIEI_pitch >= -15 & propBoutIEI_pitch <= 30,
           propBoutIEI_angVel >= -10 & propBoutIEI_angVel <= 10,
           1/propBoutIEI <= 3.5)
  
  # Bin the filtered data
  filtered_dataset <- filtered_dataset %>%
    mutate(
      binned_pitch = cut(propBoutIEI_pitch, breaks = 20, labels = FALSE),
      binned_angVel = cut(propBoutIEI_angVel, breaks = 20, labels = FALSE)
    )
  
  # Create the plot
  p <- ggplot(filtered_dataset, aes(x = binned_pitch, y = binned_angVel, fill = 1/propBoutIEI)) +
    geom_tile() +
    scale_fill_gradientn(colors = c("blue", "green", "red")) +
    theme_minimal() +
    scale_x_continuous(breaks = c(min(filtered_dataset$binned_pitch), max(filtered_dataset$binned_pitch)), labels = c(-15, 30)) +
    scale_y_continuous(breaks = c(min(filtered_dataset$binned_angVel), max(filtered_dataset$binned_angVel)), labels = c(-10, 10)) +
    labs(x = "IEI_Pitch (degree)", y = "IEI_AngVel (degree/s)", fill = "Bout Rate (Hz)") +
    ggtitle(paste("Plot for", name))
  
  # Store the plot in the list
  plots[[name]] <- p
}

# Arrange the plots side by side
grid.arrange(plots$dd_day, plots$ld_day, ncol = 2)
grid.arrange(plots$dd_day, plots$dd_night, ncol = 2)
