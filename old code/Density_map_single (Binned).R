# Load necessary libraries
library(ggplot2)
library(cowplot)
library(dplyr)

# Function to compute median for each bin
compute_medians <- function(data) {
  data %>%
    group_by(spd_bins) %>%
    summarize(median_rot_total = median(rot_total, na.rm = TRUE),
              median_post_IBI_time = median(1 / post_IBI_time, na.rm = TRUE))
}

# Compute medians for data_dd and data_ld during the day
medians_dd <- compute_medians(data_dd[data_dd$ztime == "day", ])
medians_ld <- compute_medians(data_ld[data_ld$ztime == "day", ])

# Determine the range for the x-axis
x_range <- range(c(medians_dd$median_rot_total, medians_ld$median_rot_total), na.rm = TRUE)

# Set the y-axis range
y_range <- c(0, 10)

# Create a custom color palette with enough colors
num_bins <- length(unique(c(medians_dd$spd_bins, medians_ld$spd_bins)))
color_palette <- scales::seq_gradient_pal("blue", "red", "Lab")(seq(0, 1, length.out = num_bins))

# Create the first plot for data_dd during the day with medians
p3 <- ggplot(medians_dd[medians_dd$median_rot_total >= 0,], aes(x = median_rot_total, y = median_post_IBI_time, color = spd_bins)) +
  geom_point(size = 3) +
  ggtitle("DD_day") +
  ylab("Bout Rate (Hz)")+
  scale_color_manual(values = color_palette) +
  xlim(x_range) +
  ylim(y_range)

# Create the second plot for data_ld during the day with medians
p4 <- ggplot(medians_ld[medians_ld$median_rot_total >= 0,], aes(x = median_rot_total, y = median_post_IBI_time, color = spd_bins)) +
  geom_point(size = 3) +
  ggtitle("LD_day") +
  ylab("Bout Rate (Hz)")+
  scale_color_manual(values = color_palette) +
  xlim(x_range) +
  ylim(y_range)

# Combine the two plots side by side
combined_plot <- plot_grid(p1, p3, labels = c("A", "B"))
combined_plot_2 <- plot_grid(p2, p4, labels = c("A", "B"))
combined_plot_3<- plot_grid(p3, p4, labels = c("A", "B"))
# Display the combined plot
print(combined_plot)
print(combined_plot_2)
combined_plot_3
