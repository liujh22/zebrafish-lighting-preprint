
library(RColorBrewer)

### Input
rm(list=ls())
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code")
getwd()
data_day = read.csv("rot_l_decel_2D_day.csv", header = T)  # Day
data_night = read.csv("rot_l_decel_2D_night.csv", header = T)  # Night

### Data frame for plotting
plot_day = as.data.frame(cbind("Pitch_Initial" = data_day$pitch_initial, 
                              "Rot_l_decel" = data_day$rot_l_decel, 
                              "Condition" = data_day$cond1))
plot_night = as.data.frame(cbind("Pitch_Initial" = data_night$pitch_initial, 
                                "Rot_l_decel" = data_night$rot_l_decel, 
                                "Condition" = data_night$cond1))

plot_day_dd = plot_day[plot_day$Condition == "dd",]
plot_day_ld = plot_day[plot_day$Condition == "ld",]
plot_day_ll = plot_day[plot_day$Condition == "ll",]
plot_night_dd = plot_night[plot_night$Condition == "dd",]
plot_night_ld = plot_night[plot_night$Condition == "ld",]
plot_night_ll = plot_night[plot_night$Condition == "ll",]


### Scatter Plots
# create a color palette to use in smoothed scatterplot
buylrd = c("#313695", "#4575B4", "#74ADD1", "#ABD9E9", "#E0F3F8", "#FFFFBF",
           "#FEE090", "#FDAE61", "#F46D43", "#D73027", "#A50026") 
myColRamp = colorRampPalette(c(buylrd))

# Smoothed Scatter Plot (Day)
par(mfrow = c(1, 3))
smoothScatter(x=plot_day_dd$Pitch_Initial,y=plot_day_dd$Rot_l_decel,
              colramp=myColRamp,
              main="DD",
              xlab="Pitch_Initial",
              ylab="Rot_l_decel")

smoothScatter(x=plot_day_ld$Pitch_Initial,y=plot_day_ld$Rot_l_decel,
              colramp=myColRamp,
              main="LD",
              xlab="Pitch_Initial",
              ylab="Rot_l_decel")

smoothScatter(x=plot_day_ll$Pitch_Initial,y=plot_day_ll$Rot_l_decel,
              colramp=myColRamp,
              main="LL",
              xlab="Pitch_Initial",
              ylab="Rot_l_decel")

mtext("Smoothscatter plot for Righting (Day Time)", side = 3, line = - 1.5, outer = TRUE)

# Smoothed Scatter Plot (Night)
par(mfrow = c(1, 3))
smoothScatter(x=plot_night_dd$Pitch_Initial,y=plot_night_dd$Rot_l_decel,
              colramp=myColRamp,
              main="DD",
              xlab="Pitch_Initial",
              ylab="Rot_l_decel",
              ylim= c(-15,20))

smoothScatter(x=plot_night_ld$Pitch_Initial,y=plot_night_ld$Rot_l_decel,
              colramp=myColRamp,
              main="LD",
              xlab="Pitch_Initial",
              ylab="Rot_l_decel",
              ylim= c(-15,20))

smoothScatter(x=plot_night_ll$Pitch_Initial,y=plot_night_ll$Rot_l_decel,
              colramp=myColRamp,
              main="LL",
              xlab="Pitch_Initial",
              ylab="Rot_l_decel",
              ylim= c(-15,20))

mtext("Smoothscatter plot for Righting (Night Time)", side = 3, line = - 1.5, outer = TRUE)
