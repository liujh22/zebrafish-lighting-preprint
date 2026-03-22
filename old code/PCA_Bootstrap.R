### PCA pipeline
getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
rm(list = ls())

### Packages
#library(tidyverse)
library(dplyr)
library(psych)
library(FactoMineR)
library(factoextra)
library(ggbiplot)
library(cowplot)

# library(tidyr)
# library(stats)
# library(boot)
# library(ggplot2)
# library(ggpmisc)
# library(devtools)
# library(reshape2)
# library(corrplot)

# Input
data <- read.csv("PCA_Preprocessed.csv")

# Factorize 
data$cond1 <- as.factor(data$cond1)
data$ztime <- as.factor(data$ztime)
data$expNum <- as.factor(data$expNum)

# List of numeric and categorical variables
numeric_col = colnames(data[,sapply(data,is.numeric)])
factor_col = colnames(data[,sapply(data,is.factor)])

str(data)

#############
# Bootstrap #
#############

# Separate data by "cond1" and "zTime"
groups <- split(data, interaction(data$cond1, data$ztime))

# Delete categorical columns
groups <- lapply(groups, function(group) {
  group %>% select(numeric_col)
})

# Number of bootstrap samples
n_bootstrap <- 500

# Bootstrap analysis for each group
bootstrap_results <- list()

# Run bootstrap
set.seed(123)  # Setting seed for reproducibility

for (group_name in names(groups)) {
  # Initialize matrix to store results
  group_data <- groups[[group_name]]
  results_matrix <- matrix(nrow = n_bootstrap, ncol = ncol(group_data) * 2)
  
  for (i in 1:n_bootstrap) {
    # Sample with replacement
    sampled_indices <- sample(1:nrow(group_data), replace = TRUE)
    sampled_data <- group_data[sampled_indices, ]
    
    # Calculate medians and MADs for each column and store them in the results matrix
    for (j in 1:ncol(sampled_data)) {
      median_index <- 2 * j - 1  # Odd index for median
      mad_index <- 2 * j         # Even index for MAD
      results_matrix[i, median_index] <- median(sampled_data[, j])
      results_matrix[i, mad_index] <- mad(sampled_data[, j], constant = 1)
    }
  }
  
  # Store results matrix in bootstrap_results list
  bootstrap_results[[group_name]] <- results_matrix
}


# Convert results matrices into a single data frame and add categorical labels
all_results <- data.frame()  # Initialize an empty data frame

for (group_name in names(bootstrap_results)) {
  # Convert the current group's results matrix to a data frame
  temp_df <- as.data.frame(bootstrap_results[[group_name]])
  
  # Add column names for clarity
  col_names <- c()
  for (j in 1:(ncol(temp_df)/2)) {
    col_names <- c(col_names, paste0("Median", j), paste0("MAD", j))
  }
  names(temp_df) <- col_names
  
  # Add the group name as a categorical label
  temp_df$CategoryLabel <- group_name
  
  # Bind this group's results to the main data frame
  all_results <- bind_rows(all_results, temp_df)
}

# Change column names
new_column_names <- unlist(lapply(numeric_col, function(name) c(paste0(name, "_MED"), paste0(name, "_MAD"))))

# Rename the columns in the dataframe
names(all_results)[1:length(new_column_names)] <- new_column_names


# View the final results
# 500 boot strap * 2 (day/night) * 3 (ll/ld/dd) = 3000 rows
print(all_results)
write.csv(all_results,"/Users/jiahuan/Desktop/NYU_Intern/R_Code/PCA_bootstrap_result.csv", row.names = FALSE)

#####################################################################
### Run only if you don't want to rerun the bootstrapping process ###
#####################################################################
all_results <- read.csv("PCA_bootstrap_result.csv")

###########
### PCA ###
###########

# Get numeric
result_numeric <- subset(all_results, select = -c(CategoryLabel))

# PCA using "prcomp()"
pca <- prcomp(result_numeric , center = T, scale. = T)
summary(pca)

# Screeplot
screeplot(pca, npcs = 10, type = "lines")

# Another PCA using "principal()"
pca_original <- principal(result_numeric, nfactors = 10, rotate = 'none')


# Get factor loadings 
loading<- as.data.frame(unclass(pca_original$loadings))

# Show in loadings on PC1 and PC2
barplot(sort(loading$PC1), xlab = "PC1", ylim =c(-1, 1))
barplot(sort(loading$PC2), xlab = "PC2", ylim =c(-1, 1))

##################
### PCA plots ####
##################

# Component correlation plot (Both)
ggbiplot(pca,ellipse=TRUE,obs.scale = 1, var.scale = 1,var.axes=FALSE, groups = all_results$CategoryLabel)+
  scale_colour_discrete()+
  ggtitle("PCA of Time & Lighting")+
  theme_bw()
dev.copy(pdf, "PCA_Bootstrap.pdf")
dev.off()

##############
### Biplot ###
##############

# Add "light"
all_results <- all_results %>%
  mutate(
    Time = ifelse(grepl("\\.day$", CategoryLabel), "day", "night"),
    Condition = sub("\\.(day|night)$", "", CategoryLabel),
    Light = case_when(
      grepl("ll", CategoryLabel) ~ "light",
      grepl("ld", CategoryLabel) & grepl("day$", CategoryLabel) ~ "light",
      grepl("ld", CategoryLabel) & grepl("night$", CategoryLabel) ~ "no light",
      grepl("dd", CategoryLabel) & grepl("day$", CategoryLabel) ~ "no light",
      grepl("dd", CategoryLabel) & grepl("night$", CategoryLabel) ~ "no light",
      TRUE ~ "Unknown"  # Handles unexpected cases
    )
  ) %>%
  select(-CategoryLabel)  # Optionally remove the original CategoryLabel column

#############
# Factorize #
#############
all_results$Time<-as.factor(all_results$Time)
all_results$Light <- as.factor(all_results$Light)
all_results$Condition <- as.factor(all_results$Condition)

# View the updated results
str(all_results)

# Standard Scaling
numeric_col = colnames(all_results[,sapply(all_results,is.numeric)])
factor_col = colnames(all_results[,sapply(all_results,is.factor)])
data_std <- as.data.frame(scale(subset(all_results, select = numeric_col)))

##################
### PCA Biplot ###
##################
res.pca <- PCA(data_std, graph = FALSE)
var <- get_pca_var(res.pca)
ind <- get_pca_ind(res.pca)

# Quality of individuals
# fviz_pca_ind(res.pca, col.ind = "cos2", pointsize = "cos2",
#              gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07"),
#              repel = TRUE # Avoid text overlapping (slow if many points)
# )
# 
# fviz_cos2(res.pca, choice = "ind")

# Total contribution on PC1 and PC2
# fviz_contrib(res.pca, choice = "ind", axes = 1:2)
# 
# Change labelsize
# fviz_pca_ind(res.pca, 
#              pointsize = 3, pointshape = 21, fill = "lightblue",
#              labelsize = 5, repel = TRUE)



#########
# Speed #
#########
spd_name <- colnames(data_std)[(grep("spd", colnames(data_std)))]
spd_MED_name <- c(spd_name[(grep("MED", spd_name))])
spd_MAD_name <- c(spd_name[(grep("MAD", spd_name))])
# MED
spd_MED <- fviz_pca_biplot(res.pca, select.var = list(name = spd_MED_name),
                           geom.ind = "point",
                           addEllipses = FALSE,
                           col.ind = all_results$Light,
                           pointshape = 20, pointsize = 4,
                           palette = "aaas",
                           legend.title = list(color = "Lighting"),
                           title = "PCA1_spd_MED"
)

# MAD
spd_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = spd_MAD_name),
                           geom.ind = "point",
                           addEllipses = FALSE,
                           col.ind = all_results$Light,
                           pointshape = 20, pointsize = 4,
                           palette = "aaas",
                           legend.title = list(color = "Lighting"),
                           title = "PCA1_spd_MAD"
)

plot_grid(spd_MED, spd_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Bootstrap_Speed.pdf")
dev.off()


#########
# Pitch #
#########

pitch_name <- colnames(data_std)[(grep("pitch", colnames(data_std)))]
pitch_MED_name <- c(pitch_name[(grep("MED", pitch_name))])
pitch_MAD_name <- c(pitch_name[(grep("MAD", pitch_name))])

# MED
pitch_MED <- fviz_pca_biplot(res.pca, select.var = list(name = pitch_MED_name),
                             geom.ind = "point",
                             addEllipses = FALSE,
                             col.ind = all_results$Light,
                             pointshape = 20, pointsize = 4,
                             palette = "aaas",
                             legend.title = list(color = "Lighting"),
                             title = "PCA1_pitch_MED"
)

# MAD
pitch_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = pitch_MAD_name),
                             geom.ind = "point",
                             addEllipses = FALSE,
                             col.ind = all_results$Light,
                             pointshape = 20, pointsize = 4,
                             palette = "aaas",
                             legend.title = list(color = "Lighting"),
                             title = "PCA1_pitch_MAD"
)

plot_grid(pitch_MED, pitch_MAD, ncol = 2, nrow = 1)

dev.copy(pdf, "Biplot_Bootstrap_Pitch.pdf")
dev.off() 

############
# Rotation #
############
rotation_name <- colnames(data_std)[(grep("rot", colnames(data_std)))]
rotation_MED_name <- c(rotation_name[(grep("MED", rotation_name))])
rotation_MAD_name <- c(rotation_name[(grep("MAD", rotation_name))])

# MED
rotation_MED <- fviz_pca_biplot(res.pca, select.var = list(name = rotation_MED_name),
                                geom.ind = "point",
                                addEllipses = FALSE,
                                col.ind = all_results$Light,
                                pointshape = 20, pointsize = 4,
                                palette = "aaas",
                                legend.title = list(color = "Lighting"),
                                title = "PCA1_rotation_MED"
)

# MAD 
rotation_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = rotation_MAD_name),
                                geom.ind = "point",
                                addEllipses = FALSE,
                                col.ind = all_results$Light,
                                pointshape = 20, pointsize = 4,
                                palette = "aaas",
                                legend.title = list(color = "Lighting"),
                                title = "PCA1_rotation_MAD"
)

plot_grid(rotation_MED, rotation_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Bootstrap_Rotation.pdf")
dev.off() 
