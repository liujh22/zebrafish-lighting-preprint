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
data <- read.csv("Bout_data_WT_preprocessed_SD_removed.csv")  # This takes about 30 seconds
data <- read.csv("Connected_data_preprocessed.csv") 
data <- read.csv("IBI_data_preprocessed.csv") 


# Factorize multiple columns
data$cond0<-NULL
data <- data %>%
  mutate(
    # Create the 'label' column by combining cond0 and ztime
    label = paste(cond1, ztime, sep = "_"),
    
    # Create the 'light' column based on conditions
    light = case_when(
      cond1 == "dd" ~ "no light",  # no light when cond0 == "dd"
      cond1 == "ld" & ztime == "night" ~ "no light",  # no light when cond0 == "ld" and ztime == "night"
      TRUE ~ "light"  # light for all other cases
    )
  )
factor_col <- c("cond1", "ztime", "expNum", "light", "label")
data[factor_col] <- lapply(data[factor_col], as.factor)
numeric_col = colnames(data[,sapply(data,is.numeric)])
data_circadian <- data[data$label =="dd_day"| data$label =="dd_night",]
data_lighting <- data[data$label =="dd_day"| data$label =="ld_day",]
# Take a look if you want
# skim(data)  # 4 Factors, 45 Variables

# Calculate MAD and MED for numeric variables and grouped by factors
data <- data %>%
  group_by(across(all_of(factor_col))) %>%
  summarise(across(all_of(numeric_col), list(MED = median, MAD = mad), .names = "{col}_{fn}"), .groups = "drop")

# Standard Scaling
numeric_col <- colnames(data[,sapply(data,is.numeric)])
data_std <- as.data.frame(scale(subset(data, select = numeric_col)))  # data set used for PCA

##################################
# Optional!!!! Split MAD and MED #
##################################

index_MED <- seq(5,94, by = 2)
data_MED <- data[,index_MED]
index_MAD <- seq(6, 94, by = 2)
data_MAD <- data[,index_MAD]
numeric_col <- colnames(data_MED[,sapply(data_MED,is.numeric)])
data_std <- as.data.frame(scale(subset(data_MED, select = numeric_col)))
numeric_col <- colnames(data_MAD[,sapply(data_MAD,is.numeric)])
data_std <- as.data.frame(scale(subset(data_MAD, select = numeric_col)))

# # Delete Outlier Rows
# problem_rows = c(5,17,47)
# data_std = data_std[-problem_rows,]
# data = data[-problem_rows,]


###########
### PCA ###
###########

# PCA using "prcomp()"
pca <- prcomp(data_std, center = T, scale. = T)
summary(pca)

# Screeplot
screeplot(pca, npcs = 10, type = "lines")
pr_var = ( pca$sdev )^2 

# Proportion of variance explained
prop_varex = pr_var / sum( pr_var )
plot(prop_varex, xlab = "Principal Component", 
     ylab = "Proportion of Variance Explained", type = "b" )

# Cumulative variance contribution plot
plot( cumsum( prop_varex ), xlab = "Principal Component", 
      ylab = "Cumulative Proportion of Variance Explained", type = "b" )


#################################################
### PCA plots for Individuals (with ellipse) ####
#################################################

# Define a list of configurations for the PCA plots
plot_configs <- list(
  list(group = data$light, title = "PCA of Lighting", file = "PCA of Lighting.pdf"),
  list(group = data$ztime, title = "PCA of Time", file = "PCA of Time.pdf"),
  list(group = interaction(data$cond1, data$ztime), title = "PCA of Time & Lighting", file = "PCA.pdf")
)

# Loop through the configurations and create plots
for (config in plot_configs) {
  plot <- ggbiplot(pca, ellipse = TRUE, obs.scale = 1, var.scale = 1, var.axes = FALSE, groups = config$group) +
    scale_colour_discrete() +
    ggtitle(config$title) +
    theme_bw() +
    theme(legend.position = "bottom")
  
  # Print the plot to the console
  print(plot)
  
  # Save the plot to the specified file
  ggsave(filename = paste0("/Users/jiahuan/Desktop/NYU_Intern/R_Code/PCA Plots/", config$file), plot = plot)
}


############################
### Check Factor Loading ###
############################

# PCA using "principal()"
pca_original <- principal(data_std, nfactors = 10, rotate = 'none')

# Get factor loadings 
loading<- as.data.frame(unclass(pca_original$loadings))

# Show in loadings on PC1 and PC2
barplot(sort(loading$PC1), xlab = "PC1", ylim =c(-1, 1), main = "Factor loadings on PC1")
barplot(sort(loading$PC2), xlab = "PC2", ylim =c(-1, 1), main = "Factor loadings on PC2")

# Get factors with loading (absolute value) > 0.8 on PC1 
abs_loading <- abs(loading)
PC1 <- abs_loading[order(abs_loading$PC1, decreasing = TRUE), "PC1", drop = FALSE ]
top_PC1 <- subset(PC1, PC1 >= 0.8)  # parameters with values
cat(rownames(top_PC1),fill=TRUE, sep = "\n")  # pure names

# Get factors with loading (absolute value) > 0.5 on PC2 
PC2 <- abs_loading[order(abs_loading$PC2, decreasing = TRUE), "PC2", drop = FALSE ]
top_PC2 <- subset(PC2, PC2 >= 0.5)  # parameters with values
cat(rownames(top_PC2),fill=TRUE, sep = "\n")  # pure names

# Bar plot of Top factors in PC1 and PC2
one_and_two_PC <- subset(loading, select = c(PC1, PC2))
PC1_data <- one_and_two_PC[rownames(top_PC1),]
PC2_data <- one_and_two_PC[rownames(top_PC2),]

barplot(as.matrix(PC1_data), beside=TRUE, ylim =c(-1, 1), main = "Top factors in PC1 (loading > 0.8) and their loading on PC2")
barplot(as.matrix(PC2_data), beside=TRUE, ylim =c(-1, 1), main = "Top factors in PC2 (loading > 0.5) and their loading on PC1")


##################
### PCA Biplot ###
##################

# Run PCA with "FactorMineR"
res.pca <- PCA(data_std, graph = FALSE)
var <- get_pca_var(res.pca)
ind <- get_pca_ind(res.pca)

# Quality of individuals
head(ind$cos2)
fviz_pca_ind(res.pca, col.ind = "cos2", pointsize = "cos2",
             gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07"),
             repel = TRUE)

fviz_cos2(res.pca, choice = "ind")

# Total contribution on PC1 and PC2
fviz_contrib(res.pca, choice = "ind", axes = 1:2)

# Change label size
fviz_pca_ind(res.pca, 
             pointsize = 3, pointshape = 21, fill = "lightblue",
             labelsize = 5, repel = TRUE, col.ind = data$light)

# Visualize factors with cos2 > 0.8
fviz_pca_var(res.pca, repel = TRUE,select.var = list(cos2 = 0.99))


####################################
# Biplot by parameter type - Pitch #
####################################

pitch_name <- colnames(data_std)[(grep("pitch", colnames(data_std)))]
pitch_MED_name <- c(pitch_name[(grep("MED", pitch_name))])
pitch_MAD_name <- c(pitch_name[(grep("MAD", pitch_name))])

# MED
pitch_MED <- fviz_pca_biplot(res.pca, select.var = list(name = pitch_MED_name),
                geom.ind = "point",
                addEllipses = FALSE,
                col.ind = data$light,
                pointshape = 20, pointsize = 4,
                palette = "aaas",
                legend.title = list(color = "Lighting"),
                title = "PCA1_pitch_MED"
)

# MAD
pitch_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = pitch_MAD_name),
                geom.ind = "point",
                addEllipses = FALSE,
                col.ind = data$light,
                pointshape = 20, pointsize = 4,
                palette = "aaas",
                legend.title = list(color = "Lighting"),
                title = "PCA1_pitch_MAD"
)
plot_grid(pitch_MED, pitch_MAD, ncol = 2, nrow = 1)

dev.copy(pdf, "Biplot_Pitch.pdf")
dev.off() 


###############################
# By Condition - Dark & Light #
###############################

dark_var_name <- c("rot_total_MAD",              
                   "rot_total_MED",
                   "bout_trajectory_Pre2Post_MED",
                   "x_pre_swim_MAD", 
                   "spd_peak_MED","spd_initial_MAD")

dark <- fviz_pca_biplot(res.pca, select.var = list(name = dark_var_name),
                         # Set limitation for axises
                         xlim = c(-20, 20),
                         ylim = c(-20, 20),
                         # Dimension 1 versus 2 
                         axes = c(1,2),
                         # Show individual data set in point
                         geom.ind = "point",
                         # Show parameter in arrow and text
                         geom.var = c("arrow", "text"),
                         addEllipses = FALSE,
                         col.ind = data$light,
                         pointshape = 20, pointsize = 3,
                         # palette = "aaas",
                         repel = TRUE,
                         # Things that want to hide
                         invisible = "none",
                         legend.title = list(color = "Lighting"),
                         legend = "color",
                         title = "Lighting Effect"
)

plot_grid(dark)
dark + theme(
  panel.grid.major = element_blank(),  # Remove major grid lines
  panel.grid.minor = element_blank(),  # Remove minor grid lines
  panel.background = element_blank(),  # Remove background color
  axis.line = element_line(),          # Keep axis lines
  legend.text = element_text(size = 10), 
  legend.title = element_text(size = 12),
  legend.position = "right"
) + guides(fill = "none")  # Hides the "Col." legend

dev.copy(pdf, "Biplot_Dark.pdf")
dev.off() 


##############################
# By Condition - Day & Night #
##############################
day_var_name <- c("atk_ang_MED", 
                  "pitch_initial_MED", "spd_peak_MED", "x_spd_peak_MED",
                  "rot_full_accel_MED","rot_early_accel_MED",
                  "rot_bout_MED")

day <- fviz_pca_biplot(res.pca, select.var = list(name = day_var_name),
                        # Set limitation for axises
                        xlim = c(-20, 20),
                        ylim = c(-20, 20),
                        # Dimension 1 versus 2 
                        axes = c(1,2),
                        # Show individual data set in point
                        geom.ind = "point",
                        # Show parameter in arrow and text
                        geom.var = c("arrow", "text"),
                        addEllipses = FALSE,
                        col.ind = data$ztime,
                        pointshape = 20, pointsize = 3,
                        # palette = "aaas",
                        repel = TRUE,
                        # Things that want to hide
                        invisible = "none",
                        legend.title = list(color = "Day Time"),
                        legend = "color",
                        title = "Parameters that are positive in day time"
)

# Customize the theme to remove grid and format the legend
day <- day + theme(
  panel.grid.major = element_blank(),  # Remove major grid lines
  panel.grid.minor = element_blank(),  # Remove minor grid lines
  panel.background = element_blank(),  # Remove background color
  axis.line = element_line(),          # Keep axis lines
  legend.text = element_text(size = 10), 
  legend.title = element_text(size = 12),
  legend.position = "right"
) + guides(fill = "none")  # Hides the "Col." legend

plot_grid(day)


dev.copy(pdf, "Biplot_Day.pdf")
dev.off() 


########################
# By Condition - Night #
########################
night_var_name <- c()

night <- fviz_pca_biplot(res.pca, select.var = list(name = night_var_name),
                       # Set limitation for axises
                       xlim = c(-20, 20),
                       ylim = c(-20, 20),
                       # Dimension 1 versus 2 
                       axes = c(1,2),
                       # Show individual data set in point
                       geom.ind = "point",
                       # Show parameter in arrow and text
                       geom.var = c("arrow", "text"),
                       addEllipses = FALSE,
                       col.ind = data$ztime,
                       pointshape = 20, pointsize = 3,
                       # palette = "aaas",
                       repel = TRUE,
                       # Things that want to hide
                       invisible = "none",
                       legend.title = list(color = "Day Time"),
                       legend = "color",
                       title = "Parameters that are positive in night time"
)

plot_grid(night)
night + theme(legend.text = element_text(size = 10), 
              legend.title = element_text(size = 12),
              legend.position = "right") + 
  guides(fill = "none")  # Hides the "Col." legend

dev.copy(pdf, "Biplot_Night.pdf")
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
                                col.ind = data$light,
                                pointshape = 20, pointsize = 4,
                                palette = "aaas",
                                legend.title = list(color = "Lighting"),
                                title = "PCA1_rotation_MED"
)

# MAD 
rotation_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = rotation_MAD_name),
                                geom.ind = "point",
                                addEllipses = FALSE,
                                col.ind = data$light,
                                pointshape = 20, pointsize = 4,
                                palette = "aaas",
                                legend.title = list(color = "Lighting"),
                                title = "PCA1_rotation_MAD"
)

plot_grid(rotation_MED, rotation_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Rotation.pdf")
dev.off() 

##############
# Trajectory #
##############

traj_name <- colnames(data_std)[(grep("traj", colnames(data_std)))]
traj_MED_name <- c(traj_name[(grep("MED", traj_name))])
traj_MAD_name <- c(traj_name[(grep("MAD", traj_name))])

# MED
traj_MED <- fviz_pca_biplot(res.pca, select.var = list(name = traj_MED_name),
                            geom.ind = "point",
                            addEllipses = FALSE,
                            col.ind = data$light,
                            pointshape = 20, pointsize = 4,
                            palette = "aaas",
                            legend.title = list(color = "Lighting"),
                            title = "PCA1_traj_MED"
)

# MAD
traj_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = traj_MAD_name),
                            geom.ind = "point",
                            addEllipses = FALSE,
                            col.ind = data$light,
                            pointshape = 20, pointsize = 4,
                            palette = "aaas",
                            legend.title = list(color = "Lighting"),
                            title = "PCA1_traj_MAD"
)

plot_grid(traj_MED, traj_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Trajectory.pdf")
dev.off() 

################
# Displacement #
################

displ_name <- colnames(data_std)[(grep("displ", colnames(data_std)))]
displ_MED_name <- c(displ_name[(grep("MED", displ_name))])
displ_MAD_name <- c(displ_name[(grep("MAD", displ_name))])

# MED
displ_MED <- fviz_pca_biplot(res.pca, select.var = list(name = displ_MED_name),
                             geom.ind = "point",
                             addEllipses = FALSE,
                             col.ind = data$light,
                             pointshape = 20, pointsize = 4,
                             palette = "aaas",
                             legend.title = list(color = "Lighting"),
                             title = "PCA1_displ_MED"
)

# MAD
displ_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = displ_MAD_name),
                             geom.ind = "point",
                             addEllipses = FALSE,
                             col.ind = data$light,
                             pointshape = 20, pointsize = 4,
                             palette = "aaas",
                             legend.title = list(color = "Lighting"),
                             title = "PCA1_displ_MAD"
)

plot_grid(displ_MED, displ_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Displacement.pdf")
dev.off() 

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
                           col.ind = data$light,
                           pointshape = 20, pointsize = 4,
                           palette = "aaas",
                           legend.title = list(color = "Lighting"),
                           title = "PCA1_spd_MED"
)

# MAD
spd_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = spd_MAD_name),
                           geom.ind = "point",
                           addEllipses = FALSE,
                           col.ind = data$light,
                           pointshape = 20, pointsize = 4,
                           palette = "aaas",
                           legend.title = list(color = "Lighting"),
                           title = "PCA1_spd_MAD"
)

plot_grid(spd_MED, spd_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Speed.pdf")
dev.off() 

#########
# Angel #
#########
ang_name <- colnames(data_std)[(grep("ang", colnames(data_std)))]
ang_MED_name <- c(ang_name[(grep("MED", ang_name))])
ang_MAD_name <- c(ang_name[(grep("MAD", ang_name))])

# MED
ang_MED <- fviz_pca_biplot(res.pca, select.var = list(name = ang_MED_name),
                           geom.ind = "point",
                           addEllipses = FALSE,
                           col.ind = data$light,
                           pointshape = 20, pointsize = 4,
                           palette = "aaas",
                           legend.title = list(color = "Lighting"),
                           title = "PCA1_ang_MED"
)

# MAD
ang_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = ang_MAD_name),
                           geom.ind = "point",
                           addEllipses = FALSE,
                           col.ind = data$light,
                           pointshape = 20, pointsize = 4,
                           palette = "aaas",
                           legend.title = list(color = "Lighting"),
                           title = "PCA1_ang_MAD"
)

plot_grid(ang_MED, ang_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Angel.pdf")
dev.off() 

########
# Lift #
########

lift_name <- colnames(data_std)[(grep("lift", colnames(data_std)))]
lift_MED_name <- c(lift_name[(grep("MED", lift_name))])
lift_MAD_name <- c(lift_name[(grep("MAD", lift_name))])

# MED
lift_MED <- fviz_pca_biplot(res.pca, select.var = list(name = lift_MED_name),
                            geom.ind = "point",
                            addEllipses = FALSE,
                            col.ind = data$light,
                            pointshape = 20, pointsize = 4,
                            palette = "aaas",
                            legend.title = list(color = "Lighting"),
                            title = "PCA1_lift_MED"
)

# MAD
lift_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = lift_MAD_name),
                            geom.ind = "point",
                            addEllipses = FALSE,
                            col.ind = data$light,
                            pointshape = 20, pointsize = 4,
                            palette = "aaas",
                            legend.title = list(color = "Lighting"),
                            title = "PCA1_lift_MAD"
)

plot_grid(lift_MED, lift_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Lift.pdf")
dev.off() 

#########
# Depth #
#########

depth_name <- colnames(data_std)[(grep("depth", colnames(data_std)))]
depth_MED_name <- c(depth_name[(grep("MED", depth_name))])
depth_MAD_name <- c(depth_name[(grep("MAD", depth_name))])

# MED
depth_MED <- fviz_pca_biplot(res.pca, select.var = list(name = depth_MED_name),
                             geom.ind = "point",
                             addEllipses = FALSE,
                             col.ind = data$light,
                             pointshape = 20, pointsize = 4,
                             palette = "aaas",
                             legend.title = list(color = "Lighting"),
                             title = "PCA1_depth_MED"
)

# MAD
depth_MAD <- fviz_pca_biplot(res.pca, select.var = list(name = depth_MAD_name),
                             geom.ind = "point",
                             addEllipses = FALSE,
                             col.ind = data$light,
                             pointshape = 20, pointsize = 4,
                             palette = "aaas",
                             legend.title = list(color = "Lighting"),
                             title = "PCA1_depth_MAD"
)

plot_grid(depth_MED, depth_MAD, ncol = 2, nrow = 1)
dev.copy(pdf, "Biplot_Depth.pdf")
dev.off() 

