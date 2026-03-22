getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
library(dplyr)
library(cowplot)
library(ggpmisc)
library(progress)

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


# Scatter plot for selected features 
variables <- c("pitch_initial", "pitch_peak",
               "pitch_end",
               "traj_peak",
               "spd_initial", "spd_peak", "angvel_initial_phase",
               "angvel_post_phase",
               "rot_full_accel", "rot_full_decel",
               "atk_ang", "angvel_initial_phase",
               "angvel_post_phase",
               "lift_distance_fullBout",
               "ydispl_swim", "xdispl_swim", "x_spd_peak", "y_spd_peak")

variables <- c(  "pitch_initial",            "pitch_mid_accel" ,         "pitch_pre_bout",           "pitch_peak",              
                 "pitch_post_bout",          "pitch_end",                "pitch_max_angvel",         "traj_initial" ,           
                 "traj_pre_bout"  ,          "traj_peak"   ,             "traj_post_bout"  ,         "traj_end"      ,          
                 "spd_initial",              "spd_peak"     ,            "angvel_initial_phase"  ,   "angvel_prep_phase",       
                 "angvel_post_phase"  ,      "traj_initial_phase",       "spd_initial_phase",        "rot_total"         ,      
                 "rot_bout"            ,     "rot_pre_bout"       ,      "rot_l_accel"       ,       "rot_full_accel"     ,     
                 "rot_full_decel"       ,    "rot_l_decel"         ,     "rot_early_accel"    ,      "rot_late_accel"      ,    
                 "rot_early_decel"       ,   "rot_late_decel"       ,    "rot_to_max_angvel"   ,     "bout_trajectory_Pre2Post",
                 "bout_displ"             ,  "traj_deviation"        ,   "atk_ang"              ,    "angvel_chg"              ,
                 "depth_chg_fullBout"      , "lift_distance"          ,  "lift_distance_fullBout",   "additional_depth_chg"    ,
                 "displ_swim"               ,"ydispl_swim"             , "xdispl_swim"            ,             
                               "x_spd_peak"  ,             "y_spd_peak" )
output_dir <- "output_plots"
if (!dir.exists(output_dir)) {
  dir.create(output_dir)
}

# Total number of iterations
total_iterations <- (length(variables) - 1) * length(variables) / 2

# Initialize the progress bar
pb <- progress_bar$new(
  format = "  Processing [:bar] :percent in :elapsed",
  total = total_iterations, clear = FALSE, width = 60
)

# Loop through each pair of variables
for (I in 1:(length(variables) - 1)) {
  for (j in (I + 1):length(variables)) {
    
    # Calculate the 5th and 95th percentiles for the current pair of variables
    x_lower <- quantile(data[[variables[I]]], 0.01)
    x_upper <- quantile(data[[variables[I]]], 0.99)
    y_lower <- quantile(data[[variables[j]]], 0.01)
    y_upper <- quantile(data[[variables[j]]], 0.99)
    
    # Filter the data to include only the values between the 5th and 95th percentiles
    filtered_data <- data %>%
      filter(!!sym(variables[I]) >= x_lower & !!sym(variables[I]) <= x_upper &
               !!sym(variables[j]) >= y_lower & !!sym(variables[j]) <= y_upper)
    
    # Create the plot with the filtered data
    p <- ggplot(filtered_data, aes_string(x = variables[I], y = variables[j], color = "light")) +
      geom_density_2d() +
      geom_smooth(method = "lm", se = FALSE) +
      stat_poly_eq(aes(label = paste(..eq.label.., ..adj.rr.label.., sep = "~~~")), 
                   parse = TRUE) +
      coord_fixed(ratio = 1)+
      xlim(-30, 30) +
      ylim(-30, 30) +
      ggtitle(paste("Desity map for", variables[I], "and", variables[j]))
    
    # Save the plot to a file
    filename <- paste0(output_dir, "/", variables[I], "_vs_", variables[j], ".png")
    ggsave(filename, plot = p, width = 8, height = 6)
    
    # Update the progress bar
    pb$tick()
  }
}
