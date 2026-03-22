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
data <- read.csv("Bout_data_fin_preprocessed_SD_removed.csv")

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
combine_data <- rbind(ld_day, dd_day)  # 2 most different conditions

#############################
# Density plot for 3 components #
#########################
library(patchwork)

# Create the three individual plots
plot1 <- ggplot(combine_data, aes(x = traj_deviation, colour = cond1)) +
  geom_density() +
  xlab("Trajectory Deviation") +
  facet_wrap(~cond0) +
  theme_minimal()

plot2 <- ggplot(combine_data, aes(x = traj_deviation - atk_ang, colour = cond1)) +
  geom_density() +
  xlab("Early Rotation") +
  facet_wrap(~cond0) +
  theme_minimal()

plot3 <- ggplot(combine_data, aes(x = atk_ang, colour = cond1)) +
  geom_density() +
  xlab("Attack Angle") +
  facet_wrap(~cond0) +
  theme_minimal()


ggplot(combine_data[combine_data$cond1 == "ctrl",], aes(x = atk_ang, colour = cond0)) +
  geom_density() +
  xlab("Attack Angle") +
  #facet_wrap(~cond0) +
  theme_minimal()

# Combine the plots
combined_plot <- plot1 + (plot2 / plot3) + plot_layout(widths = c(2, 1))

# Display the combined plot
combined_plot


############################################
# MAD plot for 3 Traj_Deviation Components #
###########################################

# Step 1: Calculate MAD for each variable grouped by expNum, cond1, cond0, and ztime
mad_data <- combine_data %>%
  group_by(expNum, cond1, cond0, ztime) %>%
  summarise(
    traj_deviation_MAD = IQR(traj_deviation),
    atk_ang_MAD = IQR(atk_ang),
    diff_MAD = IQR(traj_deviation - atk_ang),
    .groups = 'drop'
  )

# Step 2: Reshape data to long format, reorder the MAD_type levels
mad_data_long <- mad_data %>%
  pivot_longer(cols = c(atk_ang_MAD, traj_deviation_MAD, diff_MAD), 
               names_to = "MAD_type", values_to = "MAD_value") %>%
  mutate(MAD_type = factor(MAD_type, levels = c( "diff_MAD", "atk_ang_MAD","traj_deviation_MAD"),
                           labels = c( "Early Rotation", "Attact Angle","Trajectory Deviation")))

# Step 3: Perform t-tests for each combination of cond1 and MAD_type comparing DD vs LD
t_test_results <- mad_data_long %>%
  group_by(cond1, MAD_type) %>%
  summarise(
    p_value = t.test(MAD_value ~ cond0)$p.value,  # T-test between DD and LD for each cond1 and MAD_type
    mean_DD = mean(MAD_value[cond0 == "DD"]),
    mean_LD = mean(MAD_value[cond0 == "LD"]),
    .groups = "drop"
  )

# Add significance levels
t_test_results <- t_test_results %>%
  mutate(significance = case_when(
    p_value < 0.001 ~ "***",
    p_value < 0.01 ~ "**",
    p_value < 0.05 ~ "*",
    TRUE ~ "ns"
  ))

# Step 4: Plot scatter plot with two lines for each condition and add significance markers near the lines
mad_plot <- ggplot(mad_data_long, aes(x = cond0, y = MAD_value, color = cond1)) +  
  geom_jitter(width = 0.2, height = 0.2, size = 3, alpha = 0.6) +  # Scatter plot with jitter for visibility
  stat_summary(fun = mean, geom = "point", aes(group = cond1), size = 4) +  # Mean points
  stat_summary(fun = mean, geom = "line", aes(group = cond1), size = 1.2) +  # Line connecting mean points
  facet_wrap(~MAD_type, scales = "free_y") +  # Facet by MAD_type in specified order
  xlab("Lighting Condition") +  
  ylab("MAD Value") +  
  theme_minimal()

# Step 5: Add significance markers to the plot near each line for ctrl and finless groups
mad_plot <- mad_plot + 
  geom_text(data = t_test_results %>% filter(cond1 == "ctrl"), 
            aes(x = 1.5, y = max(mad_data_long$MAD_value) * 1.1, label = significance), 
            inherit.aes = FALSE, size = 6, color = "#F8766D", vjust = -0.5) +  # Marker for 'ctrl'
  geom_text(data = t_test_results %>% filter(cond1 == "finless"), 
            aes(x = 1.5, y = max(mad_data_long$MAD_value) * 1.05, label = significance), 
            inherit.aes = FALSE, size = 6, color = "#00BFC4", vjust = -0.5)  # Marker for 'finless'

# Display the final plot
mad_plot

ggplot(mad_data_long[mad_data_long$MAD_type == 'Early Rotation',], aes(x = cond1, y = MAD_value, color = cond0)) +  
  geom_jitter(width = 0.2, height = 0.2, size = 3, alpha = 0.6) +  # Scatter plot with jitter for visibility
  stat_summary(fun = mean, geom = "point", aes(group = cond0), size = 4) +  # Mean points
  stat_summary(fun = mean, geom = "line", aes(group = cond0), size = 1.2) +  # Line connecting mean points
  facet_wrap(~MAD_type, scales = "free_y") +  # Facet by MAD_type in specified order
  xlab("") +  
  ylab("") +  
  ggtitle("IQR of Early Rotation")+
  theme_minimal()



