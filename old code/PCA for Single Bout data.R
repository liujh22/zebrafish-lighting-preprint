####################
### PCA pipeline ###
####################

getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
library(dplyr)
library(ggbiplot)
library(FactoMineR)
library(factoextra)
library(cowplot)
library(skimr)
library(psych)

# Input
data <- read.csv("PCA_Preprocessed.csv")  # This takes about 30 seconds

# Factorize multiple columns
factor_col <- c("cond1", "ztime", "expNum", "light")
data[factor_col] <- lapply(data[factor_col], as.factor)
numeric_col = colnames(data[,sapply(data,is.numeric)])

# Standard Scaling
numeric_col <- colnames(data[,sapply(data,is.numeric)])
data_std <- as.data.frame(scale(subset(data, select = numeric_col)))  # data set used for PCA

# Keep rows within +- 3SD
keep_rows <- apply(data_std, 1, function(x) all(abs(x) <= 3))

# Filter the standardized data and categorical columns using the logical index
filtered_numeric_df <- data_std[keep_rows, ]
filtered_categorical_df <- data[keep_rows, factor_col]

# Combine the numeric and categorical data back into a single dataframe
filtered_df <- cbind(filtered_numeric_df, filtered_categorical_df)

# Print the first few rows to check the result
head(filtered_df)
data <- filtered_df

#######################################
# Optional! Select specific parameter #
#######################################
parameter_names = c("pitch_initial", "pitch_peak", "pitch_end", "traj_peak", "spd_peak", "displ_swim")
data_std <- as.data.frame(scale(subset(data, select = parameter_names)))

# Standard Scaling
numeric_col <- colnames(data[,sapply(data,is.numeric)])
data_std <- as.data.frame(scale(subset(data, select = numeric_col)))

###########
### PCA ###
###########

# PCA using "prcomp()"
pca <- prcomp(data_std, center = T, scale. = T)
summary(pca)

# Screeplot
screeplot(pca, npcs = 10, type = "lines")
pr_var = ( pca$sdev )^2 

# Proportion of variance
prop_varex = pr_var / sum( pr_var )
plot(prop_varex, xlab = "Principal Component", 
     ylab = "Proportion of Variance Explained", type = "b" )

# Cumulative variance contribution plot
plot( cumsum( prop_varex ), xlab = "Principal Component", 
      ylab = "Cumulative Proportion of Variance Explained", type = "b" )

# PCA using "principal()"
pca_original <- principal(data_std, nfactors = 10, rotate = 'none')

#############################
### Check Factor Loadings ###
#############################

# Get factor loadings 
loading<- as.data.frame(unclass(pca_original$loadings))

# Show in loadings on PC1 and PC2
barplot(sort(loading$PC1), xlab = "PC1", ylim =c(-1, 1), main = "Factor loadings on PC1")
barplot(sort(loading$PC2), xlab = "PC2", ylim =c(-1, 1), main = "Factor loadings on PC2")

# Get factors with loading (absolute value) > 0.8 on PC1 
abs_loading <- abs(loading)
PC1 <- abs_loading[order(abs_loading$PC1, decreasing = TRUE), "PC1", drop = FALSE ]
top_PC1 <- subset(PC1, PC1 >= 0.8)  # parameters with values
cat(rownames(top_PC1), fill=TRUE, sep = "\n")  # pure names

# Get factors with loading (absolute value) > 0.5 on PC2 
PC2 <- abs_loading[order(abs_loading$PC2, decreasing = TRUE), "PC2", drop = FALSE ]
top_PC2 <- subset(PC2, PC2 >= 0.5)  # parameters with values
cat(rownames(top_PC2), fill=TRUE, sep = "\n")  # pure names

# Bar plot of Top factors in PC1 and PC2
one_and_two_PC <- subset(loading, select = c(PC1, PC2))
PC1_data <- one_and_two_PC[rownames(top_PC1),]
PC2_data <- one_and_two_PC[rownames(top_PC2),]

barplot(as.matrix(PC1_data), beside=TRUE, ylim =c(-1, 1), main = "Top factors in PC1 (loading > 0.8) and their loading on PC2")
barplot(as.matrix(PC2_data), beside=TRUE, ylim =c(-1, 1), main = "Top factors in PC2 (loading > 0.5) and their loading on PC1")

#################################################
### PCA plots for Individuals (with ellipse) ####
#################################################

# Component correlation plot (Lighting)
ggbiplot(pca, ellipse=FALSE, obs.scale = 1, var.scale = 1, var.axes=FALSE, groups=data$light, alpha = 0.01) +
  scale_colour_discrete() +
  ggtitle("PCA of Lighting") +
  theme_bw() +
  theme(legend.position = "bottom")

# Component correlation plot (Time)
ggbiplot(pca, ellipse=FALSE, obs.scale = 1, var.scale = 1, var.axes=FALSE, groups=data$ztime, alpha = 0.03) +
  scale_colour_discrete() +
  ggtitle("PCA of Time") +
  theme_bw() +
  theme(legend.position = "bottom")

# Component correlation plot (Both)
ggbiplot(pca, ellipse=FALSE, obs.scale = 1, var.scale = 1, var.axes=FALSE, group=interaction(data$cond1, data$ztime), alpha = 0.03) +
  scale_colour_discrete() +
  ggtitle("PCA of Time & Lighting") +
  theme_bw()

###############################
### PCA plots for PC2, PC3 ####
###############################
library(cowplot)

# Define the combinations of choices
choices_list <- list(c(1,2), c(2,3), c(1,3))

# Initialize an empty list to store the plots
plots <- list()

# Loop through the combinations and create the plots
for (I in 1:length(choices_list)) {
  choice <- choices_list[[I]]
  plot <- ggbiplot(pca, choices = choice, ellipse=FALSE, obs.scale = 1, var.scale = 1, var.axes=FALSE, groups=data$cond1, alpha = 0.03) +
    scale_colour_discrete() +
    ggtitle(paste("PCA of Lighting - Choices:", choice[1], ",", choice[2])) +
    theme_bw() +
    theme(legend.position = "bottom")
  
  # Print each plot
  print(plot)
}

# Day vs. Night
for (I in 1:length(choices_list)) {
  choice <- choices_list[[I]]
  plot <- ggbiplot(pca, choices = choice, ellipse=FALSE, obs.scale = 1, var.scale = 1, var.axes=FALSE, groups=data$ztime, alpha = 0.03) +
    scale_colour_discrete() +
    ggtitle(paste("PCA of Time - Choices:", choice[1], ",", choice[2])) +
    theme_bw() +
    theme(legend.position = "bottom")
  
  # Print each plot
  print(plot)
}
