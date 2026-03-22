library(dplyr)
library(ggplot2)
library(ggpubr)
library(cowplot)
library(MASS)

rm(list = ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
data <- read.csv("PCA_preprocessed_IBI.csv")

# 设定160个格子
numBins <- 160

# 区间为0到20，每个格子长0.125
edges <- seq(0, 20, length.out = numBins + 1)

# Define labels for conditions
conditions <- c("ld_day", "dd_day")

# Function to analyze and plot data for a given condition
analyze_and_plot <- function(data, condition_label) {
  condition_data <- data %>% filter(label == condition_label)
  
  # Calculate IEI and bout rate for the condition
  IEI <- condition_data %>% filter(propBoutIEI <= 20) %>% pull(propBoutIEI)
  boutrate <- 1 / IEI
  
  # Prepare data for plotting
  data_plot_bout_rate <- data.frame(x = boutrate)
  
  # Fit distributions
  fit_weibull <- fitdistr(data_plot_bout_rate$x, "weibull")
  fit_normal <- fitdistr(data_plot_bout_rate$x, "normal")
  fit_lognormal <- fitdistr(data_plot_bout_rate$x, "lognormal")
  fit_gamma <- fitdistr(data_plot_bout_rate$x, "gamma")
  
  # Calculate AIC and BIC
  aic_values <- c(
    AIC(fit_weibull),
    AIC(fit_normal),
    AIC(fit_lognormal),
    AIC(fit_gamma)
  )
  
  bic_values <- c(
    BIC(fit_weibull),
    BIC(fit_normal),
    BIC(fit_lognormal),
    BIC(fit_gamma)
  )
  
  names(aic_values) <- c("Weibull", "Normal", "Log-Normal", "Gamma")
  names(bic_values) <- c("Weibull", "Normal", "Log-Normal", "Gamma")
  
  print(paste("AIC Values for", condition_label, ":"))
  print(aic_values)
  
  print(paste("BIC Values for", condition_label, ":"))
  print(bic_values)
  
  # Create the plot for the condition
  p <- ggplot(data_plot_bout_rate, aes(x)) +
    geom_histogram(aes(y = ..density..), breaks = edges, color = "black", fill = "lightblue") +
    stat_function(fun = dnorm, args = list(mean = mean(data_plot_bout_rate$x), sd = sd(data_plot_bout_rate$x)), aes(color = "Normal"), size = 1) +
    stat_function(fun = function(x) dlnorm(x, meanlog = mean(log(data_plot_bout_rate$x)), sdlog = sd(log(data_plot_bout_rate$x))), aes(color = "Log-Normal"), size = 1) +
    stat_function(fun = function(x) dgamma(x, shape = (mean(data_plot_bout_rate$x)^2) / var(data_plot_bout_rate$x), rate = mean(data_plot_bout_rate$x) / var(data_plot_bout_rate$x)), aes(color = "Gamma"), size = 1) +
    stat_function(fun = function(x) dweibull(x, fit_weibull$estimate['shape'], fit_weibull$estimate['scale']), aes(color = "Weibull"), size = 1) +
    ylim(0, 2) +
    xlim(0, 10) +
    labs(title = paste("Histogram with Various Fits -", condition_label),
         x = "Bout Rate(Hz)",
         y = "Density",
         color = "Distribution") +
    theme_minimal() +
    scale_color_manual(values = c("Normal" = "red", "Log-Normal" = "blue", "Gamma" = "purple", "Weibull" = "darkgreen"))
  
  return(p)
}

# Loop through each condition and generate plots
plots <- list()
for (condition in conditions) {
  plots[[condition]] <- analyze_and_plot(data, condition)
}

# Combine the histogram plots
combined_histogram_plot <- plot_grid(plots[["ld_day"]], plots[["dd_day"]], ncol = 1, align = "v")

# Print the combined histogram plot
print(combined_histogram_plot)