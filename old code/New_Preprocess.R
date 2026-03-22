######################
### Pre-processing ###
###################### (Aug. 29 Version)
library(dplyr)
getwd()
setwd("/Users/jiahuan/Desktop/NYU_Intern/R_Code/Raw data from Python")
rm(list = ls())

#########
# Input #
#########
filename <- c("Bout_data_WT.csv")
data <- read.csv(filename)

###################################
# Delete variables you don't want #
###################################
data <- subset(data, select = -c( X,index, boutNum,epochNum, propBout_time,location_bout_in_epoch,
                                  rowsInRes,propBoutIEI_strict_pitch,propBoutIEI_strict_pitch_median,      
                                  propBoutIEI_strict_linearAccel,propBoutIEI_strict_linearAccel_median,
                                  propBoutIEI_strict_angVel,propBoutIEI_strict_angVel_median, 
                                  propBoutIEI_strict_angAcc,propBoutIEI_strict_angAcc_median, 
                                  propBoutIEI_strict_Dur,propBoutIEI_strict_yvel,            
                                  propBoutIEI_strict_yvel_median,propBoutIEI_strict_yAcce,           
                                  propBoutIEI_strict_yAccel_media, propBoutIEI_strict_spd,
                                  propBoutIEI_time,
                                  boxNum, exp   ))          

data <- subset(data, select = -c(X, x_initial, y_initial, x_end, y_end, 
                                 fish_length, boxNum, exp, bout_time))
####################################
# Check and Delete high NAs (>50%) #
####################################
# data <- subset(data, select = -c(pre_IBI_time, post_IBI_time))

# Delete any other row containing NAs
data <- na.omit(data)

############################
# Add new columns you want #
############################
data$x_spd_peak <- cos(data$traj_peak*pi/180) * data$spd_peak  
data$y_spd_peak <- sin(data$traj_peak*pi/180) * data$spd_peak  

##########################
# Remove Outliers >= 3SD #
##########################

# 首先获取所有数值列的列名
numeric_cols <- colnames(data)[sapply(data, is.numeric)]

# 使用 group_by() 和 filter() 只针对数值列进行操作
filtered_data <- data %>%
  group_by(cond0, cond1, ztime) %>%  # 按 'label' 列分组
  filter_at(vars(numeric_cols), all_vars(. >= (mean(.) - 3 * sd(.)) & . <= (mean(.) + 3 * sd(.)))) %>%
  ungroup()  # 取消分组

# 检查结果
str(filtered_data)


# Output
write.csv(filtered_data, "Bout_data_WT_preprocessed_SD_removed.csv", row.names = FALSE)
